from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialogButtonBox, QLabel, QMessageBox,QApplication
from qgis.core import Qgis, QgsDistanceArea, QgsMessageLog, QgsPointXY, QgsSpatialIndex,QgsWkbTypes
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsSimpleLineSymbolLayer, QgsVectorLayer
from qgis.gui import QgsHighlight, QgsMapToolEmitPoint

from . import string_to_real
from ..ui.Popup_ui import Ui_Form
import os
NEIGHBOR_SAMPLE_SIZE = 100
from .. import get_icon_path

class Popup(QWidget, Ui_Form):
    ui_rows = 3 #Rows that are defined in the UI
    def __init__(self, km_value,orthogonal_distance, value_list: list[tuple[str, str]]):
        super().__init__()
        self.setupUi(self)
        self.label_value_km.setText(str(km_value))
        self.label_value_ortho.setText(str(orthogonal_distance))

        self.setWindowIcon(QIcon(get_icon_path()))
        self.setWindowTitle(self.tr("StreckenKM"))
        index = 0

        icon_path = os.path.join(os.path.dirname(__file__),"..","icons", "icon_copy.png")

        icon = QIcon(icon_path)
        self.ui_rows = self.gridLayout.rowCount()
        for index, (value_name, value) in enumerate(value_list):
            self.gridLayout.addWidget(QLabel(value_name), index + self.ui_rows, 0, 1, 1)
            self.gridLayout.addWidget(QLabel(str(value)), index + self.ui_rows, 1, 1, 1)
            button = QPushButton()
            button.setText("")
            button.setMaximumSize(QSize(24, 24))
            button.setIcon(icon)
            button.clicked.connect(lambda b,t=value:self.copy_to_clipboard(t))
            self.gridLayout.addWidget(button, index + self.ui_rows, 2, 1, 1)

        self.pushbutton_km.clicked.connect(lambda:self.copy_to_clipboard(str(km_value)))
        self.pushbutton_km.setIcon(icon)
        self.pushbutton_km.setText("")

        self.pushButton_ortho.clicked.connect(lambda:self.copy_to_clipboard(str(km_value)))
        self.pushButton_ortho.setIcon(icon)
        self.pushButton_ortho.setText("")

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, index + self.ui_rows+1, 0, 1, 3)
        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.accepted.connect(self.hide)

    def copy_to_clipboard(self,text):
        clipboard = QApplication.clipboard()
        clipboard.setText(str(text))


class NearestPointFinder(QgsMapToolEmitPoint):
    def __init__(self, iface, spatial_index, layer: QgsVectorLayer, field_name, field_is_real, ignore_sidings,
                 displayed_field_names: list[str]):
        self.canvas = iface.mapCanvas()
        self.highlight:QgsHighlight|None = None

        super().__init__(self.canvas)
        self.iface = iface
        self.spatial_index: QgsSpatialIndex = spatial_index
        self.search_layer = layer
        self.field_is_real = field_is_real
        self.ignore_sidings = ignore_sidings
        self.start_pos_field_name = field_name
        self.displayed_field_names = displayed_field_names
        self.line_layer: QgsVectorLayer | None = None
        self.create_line_layer()

        self.line: QgsFeature | None = None

        self.distance_calc = QgsDistanceArea()
        self.distance_calc.setEllipsoid(self.search_layer.crs().authid())

        self.popup: Popup | None = None


    def __del__(self):
        """Remove the layer from the project."""
        QgsProject.instance().removeMapLayer(self.line_layer)
        QgsMessageLog.logMessage("Point finder will be deleted", "StreckenKM", Qgis.Info)

        if self.highlight:
            self.highlight.hide()

    def get_neighbor(self, point: QgsPointXY) -> QgsFeature | None:

        nearest_ids = self.spatial_index.nearestNeighbor(QgsPointXY(point), NEIGHBOR_SAMPLE_SIZE)
        nearest_feature = None
        nearest_dist = float('inf')
        if not nearest_ids:
            return None
        for fid in nearest_ids:
            feature = self.search_layer.getFeature(fid)
            val = feature[self.start_pos_field_name]
            if not val and self.ignore_sidings:
                continue
            geom = feature.geometry()
            distance = geom.distance(QgsGeometry.fromPointXY(point))
            if distance < nearest_dist:
                nearest_feature = feature
                nearest_dist = distance
        return nearest_feature

    def get_value_list(self, feature: QgsFeature) -> list[tuple[str, str]]:
        value_tuples = list()
        for name in self.displayed_field_names:
            value = feature[name] if name in feature.fields().names() else ""
            if isinstance(value, float):
                value = round(value, 3)
            value_tuples.append((name, value))
        return value_tuples

    def canvasReleaseEvent(self, event):
        if not self.search_layer or not self.spatial_index:
            QMessageBox.warning(None,self.tr("Warning"), self.tr("No valid point layer or spatial index."))
            return

        # Get the clicked point in map coordinates
        click_point = QgsPointXY(self.toMapCoordinates(event.pos()))

        # Find nearest point ID
        nearest_feature = self.get_neighbor(click_point)
        if not nearest_feature:
            QMessageBox.information(None,self.tr("Info"), self.tr("No points found nearby."))
            return

        #Highlight nearest Feature
        self.highlight_feature(nearest_feature)



        if QgsWkbTypes.geometryType(self.search_layer.wkbType())== QgsWkbTypes.LineGeometry:
            # Search for closest Point
            ortho_dist, closest_point, next_index, is_left = nearest_feature.geometry().closestSegmentWithContext(
                click_point)
            dist = self.get_partial_line_length(nearest_feature.geometry(), next_index - 1, closest_point)

        else:
            closest_point = nearest_feature.geometry().asPoint()
            dist = 0

        start_pos = nearest_feature[
            self.start_pos_field_name] if self.start_pos_field_name in nearest_feature.fields().names() else ""

        #Draw Line to Closest Point
        self.draw_line(QgsPointXY(click_point), closest_point)

        #Handle Empty Value
        if not start_pos:
            QMessageBox.information(None, self.tr("Value not found"), self.tr("Kilometer value doesn't exist"))
            return

        #Calculate Linear Reference of closest Point
        if self.field_is_real:
            position = start_pos + dist / 1000
        else:
            position = string_to_real(start_pos) + dist / 1000
        position = round(position, 3)

        #Create Popup
        geometry = None
        if self.popup is not None:
            geometry = self.popup.geometry()
            self.popup.hide()
            self.popup.close()

        self.popup = Popup(position,round(ortho_dist,3), self.get_value_list(nearest_feature))

        if geometry:
            self.popup.setGeometry(geometry)
        self.popup.show()

    def get_partial_line_length(self, line: QgsGeometry, index: int, closest_point:QgsPointXY):
        """
        calculates Length from Start of LineSegement to Closest Point
        """
        line_strings = line.asMultiPolyline()
        cumulative_length = 0
        current_segment = 0
        last_point = [line_strings[0][0]]
        for line in line_strings:
            vertices = line  # Vertices of the current LineString
            last_point = vertices[0]
            num_segments = len(vertices) - 1  # Number of segments in the current LineString

            # Check if the target segment index is within this LineString
            if current_segment + num_segments > index:
                # Calculate the partial length in this LineString
                target_index = index - current_segment  # Segment index within this LineString
                last_point = vertices[target_index]
                partial_vertices = vertices[:target_index + 1]  # Include points up to the target segment
                partial_line = QgsGeometry.fromPolylineXY(partial_vertices)
                cumulative_length += partial_line.length()
                break
            else:
                # Add the full length of this LineString
                full_line = QgsGeometry.fromPolylineXY(vertices)
                cumulative_length += full_line.length()
                current_segment += num_segments
        partial_line = QgsGeometry.fromPolylineXY([last_point, closest_point])
        cumulative_length += partial_line.length()
        return cumulative_length

    def highlight_feature(self, feature: QgsFeature):
        # Remove previous highlight
        self.hide_highlight()

        # Highlight the new feature
        self.highlight = QgsHighlight(self.canvas, feature, self.search_layer)
        self.highlight.setColor(QColor(255, 0, 0))  # Red highlight
        self.highlight.setWidth(2)
        self.highlight.show()

    def hide_highlight(self):
        if self.highlight:
            self.highlight.hide()

    def delete_lines(self):
        """
        delete all existing lines
        """
        self.line_layer.dataProvider().truncate()
        self.line_layer.updateExtents()
        self.line_layer.triggerRepaint()

    def draw_line(self, start_point, end_point):
        """
        Draws line between start_point and end_point
        """
        #Delete the existing line
        self.delete_lines()

        # Create a line feature
        line_geom = QgsGeometry.fromPolylineXY([start_point, end_point])
        line_feature = QgsFeature()
        line_feature.setGeometry(line_geom)

        # Add the line feature to the temporary layer
        self.line_layer.dataProvider().addFeature(line_feature)
        self.line_layer.updateExtents()
        self.line_layer.triggerRepaint()
        self.line = line_feature

    def create_line_layer(self):
        #Create Layer
        epsg_code = self.search_layer.crs().authid()
        self.line_layer = QgsVectorLayer(f"LineString?crs={epsg_code}", "Nearest Line", "memory")
        QgsProject.instance().addMapLayer(self.line_layer)
        tree_view = self.iface.layerTreeView()
        model = self.iface.layerTreeView().layerTreeModel()
        root = QgsProject().instance().layerTreeRoot()
        node = root.findLayer(self.line_layer.id())
        index = model.node2index(node)

        #Hide Layer from TreeView
        tree_view.setRowHidden(index.row(), index.parent(), True)
        tree_view.setCurrentIndex(model.node2index(root))

        #Style Layer
        line_symbol = QgsSimpleLineSymbolLayer()

        # Set the line width (thick line)
        line_symbol.setWidth(1.0)  # Adjust for your desired thickness

        # Set the line color (red)
        line_symbol.setColor(QColor(255, 0, 0))

        # Set the line style (dotted)
        line_symbol.setPenStyle(Qt.DotLine)

        # Apply the symbol layer to the layer renderer
        renderer = self.line_layer.renderer()
        symbol = renderer.symbol()
        symbol.changeSymbolLayer(0, line_symbol)
