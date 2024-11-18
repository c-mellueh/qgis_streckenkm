from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QDockWidget

from db_streckenkm.db_streckenkm.settings_widget import SettingsWidget
from db_streckenkm.db_streckenkm.data_widget import DataWidget

from PyQt5.QtCore import Qt

from .. import get_icon_path
class DockWidget(QDockWidget):
    def __init__(self, parent=None,iface = None):
        super(DockWidget, self).__init__(parent)
        self.iface = iface
        self.setWindowTitle("SteckenKM")
        self.setWindowIcon(QIcon(get_icon_path()))
        self.setLayout(QVBoxLayout())
        self.tab_widget = QTabWidget(self)
        self.setWidget(self.tab_widget)
        self.settings_widget = SettingsWidget()
        self.settings_widget.setLayout(QVBoxLayout())
        self.settings_widget_index = self.tab_widget.addTab(self.settings_widget,QIcon(),"Settings")
        self.data_widget = DataWidget(0.,0.)
        self.data_widget_index = self.tab_widget.addTab(self.data_widget,QIcon(),"Data")
        self.setFloating(True)
        self.tab_widget.setTabEnabled(self.data_widget_index,False)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

    def is_maptool_available(self):
        layer = self.settings_widget.get_settings()[0]
        return self.settings_widget.spatial_index_dict.get(layer) is not None

    def point_found(self, position, ortho_dist, value_list):
        self.tab_widget.setCurrentIndex(self.data_widget_index)
        self.tab_widget.setTabEnabled(self.data_widget_index, True)
        self.data_widget.fill_value_list(value_list)
        self.data_widget.set_km(round(position,3))
        self.data_widget.set_ortho(round(ortho_dist,3))
