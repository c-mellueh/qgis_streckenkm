from qgis.PyQt.QtCore import QSize, Qt,pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialogButtonBox, QLabel, QMessageBox,QApplication,QDockWidget
from qgis.core import Qgis, QgsDistanceArea, QgsMessageLog, QgsPointXY,QgsWkbTypes
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsSimpleLineSymbolLayer, QgsVectorLayer
from qgis.gui import QgsHighlight, QgsMapToolEmitPoint

from . import string_to_real
from .settings_widget import SettingsWidget
from .data_widget import DataWidget
NEIGHBOR_SAMPLE_SIZE = 100

class NearestPointFinder(QgsMapToolEmitPoint):
    point_found = pyqtSignal(float,float,list)
    def __init__(self, iface, settings_widget:SettingsWidget):
        self.canvas = iface.mapCanvas()
        self.highlight:QgsHighlight|None = None

        super().__init__(self.canvas)
        self.iface = iface
        self.settings_widget = settings_widget
        self.line_layer: QgsVectorLayer | None = None
        self.create_line_layer()

        self.line: QgsFeature | None = None
        self.distance_calc = QgsDistanceArea()
        self.distance_calc.setEllipsoid(self.search_layer.crs().authid())
        self.data_widget: DataWidget | None = None

    @property
    def spatial_index(self):
        return self.settings_widget.spatial_index_dict.get(self.settings_widget.layer)

    @property
    def search_layer(self) -> QgsVectorLayer:
        return self.settings_widget.layer
    @property
    def start_pos_field_name(self):
        settings = self.settings_widget.get_settings()
        return settings[1]
    @property
    def field_is_real(self) ->bool:
        settings = self.settings_widget.get_settings()
        return settings[2]

    @property
    def ignore_empty(self):
        settings = self.settings_widget.get_settings()
        return settings[3]

    @property
    def displayed_field_names(self):
        settings = self.settings_widget.get_settings()
        return settings[4]

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
            if not val and self.ignore_empty:
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
        line = self.draw_line(QgsPointXY(click_point), closest_point)
        ortho_dist = line.geometry().length()
        #Handle Empty Value
        if not start_pos:
            QMessageBox.information(None, self.tr("Value not found"), self.tr("Kilometer value doesn't exist"))
            return

        #Calculate Linear Reference of closest Point

        try:
            if self.field_is_real:
                position = start_pos + dist / 1000
            else:

                position = string_to_real(start_pos) + dist / 1000
        except TypeError:
            QMessageBox.information(None, self.tr("Value format wrong"), self.tr(f"Field '{self.start_pos_field_name}' doesn't match required format"))
            return
        #Create Popup
        self.point_found.emit(position, ortho_dist, self.get_value_list(nearest_feature))

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
        return self.line

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
