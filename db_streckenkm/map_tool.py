from PyQt5.QtCore import Qt, pyqtSignal,QVariant
from PyQt5.QtGui import QColor,QFont
from PyQt5.QtWidgets import QMessageBox
from PyQt5.uic.Compiler.qtproxies import QtCore
from qgis.gui import QgsHighlight, QgsMapToolEmitPoint,QgsMapMouseEvent
from qgis.core import Qgis, QgsDistanceArea, QgsMessageLog  , QgsPointXY,QgsPalLayerSettings,QgsField, QgsTextFormat,QgsTextBufferSettings,QgsVectorLayerSimpleLabeling
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsSimpleLineSymbolLayer, QgsVectorLayer

from  .point_finder import NearestPointFinder
from .data_widget import DataWidget
from .settings_widget import SettingsWidget
LAYER_NAME = "DB_StreckenKm_Line_Layer"

class MapTool(QgsMapToolEmitPoint):
    point_found = pyqtSignal(QgsPointXY,QgsPointXY,float, float, QgsFeature)

    def __init__(self, iface, settings_widget: SettingsWidget):
        self.canvas = iface.mapCanvas()
        self.highlight: QgsHighlight | None = None

        super().__init__(self.canvas)
        self.iface = iface
        self.settings_widget = settings_widget
        self.line_layer: QgsVectorLayer | None = None
        self.create_line_layer()

        self.line: QgsFeature | None = None
        self.distance_calc = QgsDistanceArea()
        self.distance_calc.setEllipsoid(self.search_layer.crs().authid())
        self.data_widget: DataWidget | None = None
        self.measure_between_points = False
        self.last_dataset = None

    @property
    def output_layer(self):
        if self.settings_widget.checkBox_save_points.isChecked():
            return self.settings_widget.comboBox_output.currentLayer()
        return None

    @property
    def spatial_index(self):
        return self.settings_widget.spatial_index_dict.get(self.settings_widget.layer)

    @property
    def search_layer(self) -> QgsVectorLayer:
        return self.settings_widget.layer

    @property
    def start_pos_field_name(self):
        return self.settings_widget.get_current_settings()[2]

    @property
    def field_is_float(self) -> bool:
        return self.settings_widget.get_current_settings()[4]

    @property
    def ignore_empty(self):
        return self.settings_widget.get_current_settings()[5]

    @property
    def checked_fields(self):
        return self.settings_widget.get_current_settings()[6]

    def __del__(self):
        """Remove the layer from the project."""
        QgsProject.instance().removeMapLayer(self.line_layer)
        QgsMessageLog.logMessage("Point finder will be deleted", "StreckenKM", Qgis.Info)

        if self.highlight:
            self.highlight.hide()
        self.delete_lines()
    def canvasReleaseEvent(self, event:QgsMapMouseEvent):
        if not self.search_layer or not self.spatial_index:
            QMessageBox.warning(None, self.tr("Warning"), self.tr("No valid point layer or spatial index."))
            return

        self.measure_between_points = True if event.modifiers() & Qt.ControlModifier else False

        click_point = QgsPointXY(self.toMapCoordinates(event.pos()))
        calculator = NearestPointFinder(self.search_layer, self.spatial_index, self.start_pos_field_name, self.ignore_empty,
                                        self.field_is_float)

        nearest_feature, closest_point, position = calculator.find_closest_point(click_point,QgsProject.instance().crs())

        if nearest_feature == NearestPointFinder.NO_POINTS_FOUND:
            QMessageBox.information(None, self.tr("Info"), self.tr("No points found nearby."))
            return

            # Highlight nearest Feature
        self.highlight_feature(nearest_feature)
        # Draw Line to Closest Point
        line = self.draw_line(QgsPointXY(click_point), closest_point)
        ortho_dist = line.geometry().length()
        # Handle Empty Value
        if position == NearestPointFinder.START_POS_NOT_FOUND:
            QMessageBox.information(None, self.tr("Value not found"), self.tr("Kilometer value doesn't exist"))
            return

        # Calculate Linear Reference of closest Point
        if position == NearestPointFinder.VALUE_FORMAT_WRONG:
            QMessageBox.information(None, self.tr("Value format wrong"),
                                    self.tr(f"Field '{self.start_pos_field_name}' doesn't match required format"))
            return

        # Create Popup
        self.point_found.emit(click_point,closest_point,position, ortho_dist, nearest_feature)
        self.last_dataset = (click_point,position,nearest_feature)

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
        if self.line_layer.isValid():
            self.line_layer.dataProvider().truncate()
            self.line_layer.updateExtents()
            self.line_layer.triggerRepaint()

    def draw_line(self, start_point, end_point):
        """
        Draws line between start_point and end_point
        """
        # Delete the existing line
        if not self.measure_between_points or not self.data_widget.tableWidgetsum.values:
            self.delete_lines()

        # Create a line feature
        line_geom = QgsGeometry.fromPolylineXY([start_point, end_point])
        line_feature = QgsFeature()

        if self.measure_between_points:
            line_feature.setFields(self.line_layer.fields())
            line_feature.setAttribute("id",self.line_layer.dataProvider().featureCount()+1)
        line_feature.setGeometry(line_geom)

        # Add the line feature to the temporary layer
        self.line_layer.dataProvider().addFeature(line_feature)
        self.line_layer.updateExtents()
        self.line_layer.triggerRepaint()
        self.line = line_feature
        return self.line

    def create_line_layer(self):
        # Create Layer
        epsg_code = QgsProject.instance().crs().authid()
        self.line_layer = QgsVectorLayer(f"LineString?crs={epsg_code}", LAYER_NAME, "memory")
        self.line_layer.setCustomProperty("isScratchLayer",False)
        field = QgsField("id",QVariant.Int)
        if self.line_layer.dataProvider().addAttributes([field]):
            self.line_layer.updateFields()

        QgsProject.instance().addMapLayer(self.line_layer)
        self.line_layer.setLabelsEnabled(True)
        tree_view = self.iface.layerTreeView()
        model = self.iface.layerTreeView().layerTreeModel()
        root = QgsProject().instance().layerTreeRoot()
        node = root.findLayer(self.line_layer.id())
        index = model.node2index(node)

        # Hide Layer from TreeView
        tree_view.setRowHidden(index.row(), index.parent(), True)
        tree_view.setCurrentIndex(model.node2index(root))

        # Style Layer
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

        settings = QgsPalLayerSettings()
        settings.fieldName = "name"  # Attribute to use for labels
        settings.placement = Qgis.LabelPlacement.PerimeterCurved

        # Configure text format
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(10)
        text_format.setColor(QColor("blue"))

        # Configure text buffer
        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setSize(1.5)
        buffer.setColor(QColor("white"))
        text_format.setBuffer(buffer)

        settings.setFormat(text_format)
        settings.fieldName="id"
        # Apply labeling to the layer
        labeling = QgsVectorLayerSimpleLabeling(settings)
        self.line_layer.setLabelsEnabled(True)
        self.line_layer.setLabeling(labeling)
