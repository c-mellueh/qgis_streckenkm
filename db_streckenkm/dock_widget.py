from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDockWidget, QTabWidget, QVBoxLayout
from qgis.core import QgsCoordinateTransform, QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer
from qgis.gui import QgisInterface
from .data_widget import DataWidget
from .settings_widget import SettingsWidget
from .. import get_icon_path
from .point_finder import NearestPointFinder
if TYPE_CHECKING:
    from .map_tool import MapTool


class DockWidget(QDockWidget):
    def __init__(self, parent=None, iface:QgisInterface=None):
        super(DockWidget, self).__init__(parent)
        self.iface = iface
        self.setWindowTitle("SteckenKM")
        self.setWindowIcon(QIcon(get_icon_path()))
        self.setLayout(QVBoxLayout())
        self.tab_widget = QTabWidget(self)
        self.setWidget(self.tab_widget)
        self.settings_widget = SettingsWidget()
        self.settings_widget.setLayout(QVBoxLayout())
        self.settings_widget_index = self.tab_widget.addTab(self.settings_widget, QIcon(), "Settings")
        self.data_widget = DataWidget(0., 0.)
        self.data_widget_index = self.tab_widget.addTab(self.data_widget, QIcon(), "Data")
        self.setFloating(True)
        self.tab_widget.setTabEnabled(self.data_widget_index, False)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.maptool: MapTool | None = None

    def is_maptool_available(self):
        layer = self.settings_widget.get_current_settings()[0]
        return self.settings_widget.spatial_index_dict.get(layer) is not None

    def get_value_list(self, feature: QgsFeature) -> list[tuple[str, str]]:
        value_tuples = list()
        for name in self.settings_widget.get_current_settings()[6]:
            value = feature[name] if name in feature.fields().names() else ""
            if isinstance(value, float):
                value = round(value, 3)
            value_tuples.append((name, value))
        return value_tuples

    def activate(self):
        self.show()
        self.raise_()
        self.focusWidget()
        self.activateWindow()

    def point_found(self, click_point: QgsPointXY, line_point, position, ortho_dist, input_feature: QgsFeature):
        self.activate()
        self.tab_widget.setCurrentIndex(self.data_widget_index)
        self.tab_widget.setTabEnabled(self.data_widget_index, True)

        if self.maptool.measure_between_points:
            self.data_widget.set_measure_tab_visible(True)
            self.data_widget.tableWidgetsum.add_row(position)
        else:
            self.data_widget.set_measure_tab_visible(False)
            self.data_widget.tableWidgetsum.clear_table()

        value_list = self.get_value_list(input_feature)
        self.data_widget.fill_value_list(value_list)
        self.data_widget.set_km(round(position, 5))
        self.data_widget.set_ortho(round(ortho_dist, 5))
        if click_point is None or not self.settings_widget.checkBox_save_points.isChecked():
            return

        source_crs = QgsProject.instance().crs()
        output_layer = self.settings_widget.comboBox_layer_output.currentLayer()
        target_crs = output_layer.crs()
        transform_context = QgsProject.instance().transformContext()

        # Create the coordinate transformer
        transformer = QgsCoordinateTransform(source_crs, target_crs, transform_context)
        click_point = transformer.transform(click_point)

        output_layer: QgsVectorLayer
        output_layer.startEditing()
        feature = QgsFeature()
        feature.setFields(output_layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(click_point))

        settings = self.settings_widget.get_current_settings()
        matchup = settings[7]

        feature[settings[3]] = position
        for input_field_name, ouput_field_name in matchup.items():
            feature[ouput_field_name] = input_feature[input_field_name]
        output_layer.dataProvider().addFeature(feature)
        output_layer.commitChanges()

    def run_layer_transform(self):
        search_layer: QgsVectorLayer = self.settings_widget.output_layer
        field_name: str = self.settings_widget.output_field
        km_layer = self.settings_widget.layer
        spatial_index = self.settings_widget.spatial_index_dict.get(km_layer)
        input_field_name = self.settings_widget.start_field
        ignore_empty = self.settings_widget.checkBox_ignore_empty.isChecked()
        field_is_real = self.settings_widget.checkBox_is_float.isChecked()
        field_map = self.settings_widget.get_field_matchup()
        point_finder = NearestPointFinder(km_layer,spatial_index,input_field_name,ignore_empty,field_is_real)

        search_layer.startEditing()
        for feature in search_layer.getFeatures():
            feature.fields()
            index = feature.fields().indexOf(field_name)
            nearest_feature, closest_point, position = point_finder.find_closest_point(feature.geometry().asPoint(),search_layer.crs())
            search_layer.changeAttributeValue(feature.id(),index,str(position))
            for input_field_name, ouput_field_name in field_map.items():
                value = nearest_feature.attribute(input_field_name)
                index = feature.fields().indexOf(ouput_field_name)
                search_layer.changeAttributeValue(feature.id(), index, value)
        search_layer.commitChanges()