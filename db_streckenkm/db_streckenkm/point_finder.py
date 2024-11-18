
import os.path
import re

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator, Qt
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsDistanceArea, QgsPointXY, QgsSpatialIndex,QgsMessageLog,Qgis
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsSimpleLineSymbolLayer, QgsVectorLayer
from qgis.gui import QgsHighlight, QgsMapToolEmitPoint
from . import string_to_real

NEIGHBOR_SAMPLE_SIZE = 100

class NearestPointFinder(QgsMapToolEmitPoint):
    def __init__(self, iface, spatial_index, layer: QgsVectorLayer,field_name,field_is_real,ignore_sidings):
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
        QgsMessageLog.logMessage("Point finder will be deleted","Custom Log",Qgis.Info)

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
        strecken_nr = nearest_feature[
            "GKA_STRECKEGLEISNR"] if "GKA_STRECKEGLEISNR" in nearest_feature.fields().names() else "No StreckengleisNr"
        strecken_km_text = nearest_feature[
            "VON_KM_V"] if "VON_KM_V" in nearest_feature.fields().names() else "No StreckenKm"

        self.draw_line(QgsPointXY(click_point), closest_point)
        if not strecken_km_text:
            QMessageBox.information(None, "Kein Hauptgleis", "Streckenkilometer nicht vorhanden")
            return
        position = string_to_real(strecken_km_text) + dist / 1000

        # Display information
        QMessageBox.information(None, "StreckenNr",
                                f"Name: {strecken_nr}\nStrecken Km: {position:.3f}\n index: {next_index}")

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
