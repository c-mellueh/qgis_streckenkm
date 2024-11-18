from PyQt5.QtWidgets import QPushButton
from qgis.PyQt.QtCore import Qt,QSize
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialogButtonBox, QLabel, QMessageBox, QWidget
from qgis.core import Qgis, QgsDistanceArea, QgsMessageLog, QgsPointXY, QgsSpatialIndex
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsSimpleLineSymbolLayer, QgsVectorLayer
from qgis.gui import QgsHighlight, QgsMapToolEmitPoint
from PyQt5.QtWidgets import QWidget
from . import string_to_real
from ..ui.Popup_ui import Ui_Form

NEIGHBOR_SAMPLE_SIZE = 100


class Popup(QWidget, Ui_Form):
    def __init__(self, km_value, value_list: list[tuple[str, str]]):
        super().__init__()
        self.setupUi(self)
        self.label_value.setText(str(km_value))

        index = 0
        for index, (value_name, value) in enumerate(value_list):
            self.gridLayout.addWidget(QLabel(value_name), index + 1, 0, 1, 1)
            self.gridLayout.addWidget(QLabel(str(value)), index + 1, 1, 1, 1)
            button = QPushButton()
            button.setText("")
            button.setMaximumSize(QSize(24, 24))
            self.gridLayout.addWidget(button, index + 1, 2, 1, 1)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, index + 2, 0, 1, 3)
        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.accepted.connect(self.hide)


class NearestPointFinder(QgsMapToolEmitPoint):
    def __init__(self, iface, spatial_index, layer: QgsVectorLayer, field_name, field_is_real, ignore_sidings,
                 displayed_field_names: list[str]):
        self.canvas = iface.mapCanvas()
        super().__init__(self.canvas)
        self.iface = iface
        self.spatial_index: QgsSpatialIndex = spatial_index
        self.layer = layer
        self.temp_layer: QgsVectorLayer | None = None
        self.create_hidden_layer()
        self.temp_layer_provider = self.temp_layer.dataProvider()
        self.line: QgsFeature | None = None
        self.highlight = None
        self.distance_calc = QgsDistanceArea()
        self.distance_calc.setEllipsoid(self.layer.crs().authid())
        self.field_is_real = field_is_real
        self.ignore_sidings = ignore_sidings
        self.field_name = field_name
        self.displayed_field_names = displayed_field_names
        self.popup:Popup|None = None

    def create_hidden_layer(self):
        epsg_code = self.layer.crs().authid()
        self.temp_layer = QgsVectorLayer(f"LineString?crs={epsg_code}", "Nearest Line", "memory")
        QgsProject.instance().addMapLayer(self.temp_layer)
        tree_view = self.iface.layerTreeView()
        model = self.iface.layerTreeView().layerTreeModel()
        root = QgsProject().instance().layerTreeRoot()
        node = root.findLayer(self.temp_layer.id())
        index = model.node2index(node)
        tree_view.setRowHidden(index.row(), index.parent(), True)
        tree_view.setCurrentIndex(model.node2index(root))

        line_symbol = QgsSimpleLineSymbolLayer()

        # Set the line width (thick line)
        line_symbol.setWidth(2.0)  # Adjust for your desired thickness

        # Set the line color (red)
        line_symbol.setColor(QColor(255, 0, 0))

        # Set the line style (dotted)
        line_symbol.setPenStyle(Qt.DotLine)

        # Apply the symbol layer to the layer renderer
        renderer = self.temp_layer.renderer()
        symbol = renderer.symbol()
        symbol.changeSymbolLayer(0, line_symbol)

    def __del__(self):
        """Remove the layer from the project."""
        QgsProject.instance().removeMapLayer(self.temp_layer)
        QgsMessageLog.logMessage("Point finder will be deleted", "Custom Log", Qgis.Info)

        if self.highlight:
            self.highlight.hide()

    def get_neighbor(self, point: QgsPointXY) -> QgsFeature | None:
        nearest_ids = self.spatial_index.nearestNeighbor(QgsPointXY(point), NEIGHBOR_SAMPLE_SIZE)
        nearest_feature = None
        nearest_dist = float('inf')
        if not nearest_ids:
            return None
        for fid in nearest_ids:
            feature = self.layer.getFeature(fid)
            geom = feature.geometry()
            distance = geom.distance(QgsGeometry.fromPointXY(point))
            if distance < nearest_dist:
                nearest_feature = feature
                nearest_dist = distance
        return nearest_feature

    def get_value_list(self,feature: QgsFeature):
        value_tuples = list()
        for name in self.displayed_field_names:
            value = feature[name] if name in feature.fields().names() else ""
            if isinstance(value,float):
                value = round(value,3)
            value_tuples.append((name,value))
        return value_tuples

    def canvasReleaseEvent(self, event):
        if not self.layer or not self.spatial_index:
            QMessageBox.warning(None, "Warning", "No valid point layer or spatial index.")
            return

        # Get the clicked point in map coordinates
        click_point = QgsPointXY(self.toMapCoordinates(event.pos()))

        # Find nearest point ID
        nearest_feature = self.get_neighbor(click_point)
        if not nearest_feature:
            QMessageBox.information(None, "Info", "No points found nearby.")
            return

        self.highlight_feature(nearest_feature)
        nearest_geom = nearest_feature.geometry()
        rec_dist, closest_point, next_index, is_left = nearest_geom.closestSegmentWithContext(click_point)
        dist = self.get_partial_line_length(nearest_feature.geometry(), next_index - 1, closest_point)
        strecken_km_text = nearest_feature[self.field_name] if self.field_name in nearest_feature.fields().names() else ""

        self.draw_line(QgsPointXY(click_point), closest_point)
        if not strecken_km_text:
            QMessageBox.information(None, "Kein Hauptgleis", "Streckenkilometer nicht vorhanden")
            return
        position = round(string_to_real(strecken_km_text) + dist / 1000,3)
        value_list = self.get_value_list(nearest_feature)

        self.popup = Popup(position,value_list)
        self.popup.show()
    def get_partial_line_length(self, line: QgsGeometry, index: int, new_point):
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
        partial_line = QgsGeometry.fromPolylineXY([last_point, new_point])
        cumulative_length += partial_line.length()
        return cumulative_length

    def highlight_feature(self, feature: QgsFeature):
        # Remove previous highlight
        self.hide_highlight()

        # Highlight the new feature
        self.highlight = QgsHighlight(self.canvas, feature, self.layer)
        self.highlight.setColor(QColor(255, 0, 0))  # Red highlight
        self.highlight.setWidth(2)
        self.highlight.show()

    def hide_highlight(self):
        if self.highlight:
            self.highlight.hide()

    def delete_lines(self):
        self.temp_layer_provider.truncate()
        self.temp_layer.updateExtents()
        self.temp_layer.triggerRepaint()

    def draw_line(self, start_point, end_point):
        # Create a line feature
        self.delete_lines()

        line_geom = QgsGeometry.fromPolylineXY([start_point, end_point])
        line_feature = QgsFeature()
        line_feature.setGeometry(line_geom)
        # Add the line feature to the temporary layer
        self.temp_layer_provider.addFeature(line_feature)
        self.temp_layer.updateExtents()
        self.temp_layer.triggerRepaint()
        self.line = line_feature
