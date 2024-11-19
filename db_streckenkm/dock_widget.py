from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDockWidget, QTabWidget, QVBoxLayout
from qgis.core  import QgsPointXY,QgsFeature,QgsGeometry,QgsProject,QgsCoordinateTransform,QgsVectorLayer
from .data_widget import DataWidget
from .settings_widget import SettingsWidget
from .. import get_icon_path


class DockWidget(QDockWidget):
    def __init__(self, parent=None, iface=None):
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


    def point_found(self, click_point:QgsPointXY, line_point, position, ortho_dist, input_feature:QgsFeature):
        self.tab_widget.setCurrentIndex(self.data_widget_index)
        self.tab_widget.setTabEnabled(self.data_widget_index, True)

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
        click_point =  transformer.transform(click_point)

        output_layer:QgsVectorLayer
        output_layer.startEditing()
        feature = QgsFeature()
        feature.setFields(output_layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(click_point))


        settings = self.settings_widget.get_current_settings()
        matchup = settings[7]

        feature[settings[3]] = position
        for input_field_name,ouput_field_name in matchup.items():
            feature[ouput_field_name] = input_feature[input_field_name]
        output_layer.dataProvider().addFeature(feature)
        output_layer.commitChanges()