# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StreckenkmFinder
                                 A QGIS plugin
 Klicke auf eine Karte und erhalte den nähsten Streckenkm
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-11-15
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Christoph Mellüh
        email                : christoph.mellueh@deutschebahn.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsSpatialIndex

from .db_streckenkm.point_finder import NearestPointFinder
from .ui.settingswidget import SettingsWidget
from . import get_icon_path

class StreckenkmFinder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'StreckenkmFinder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&DB_Streckenkm')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.canvas = iface.mapCanvas()
        self.spatial_index = None

        self.iface.mapCanvas().mapToolSet.connect(self.map_tool_changed)

        # Create Settings Widget
        self.settings_widget = SettingsWidget()
        self.layer = None
        self.field_name = None
        self.field_is_real = None
        self.ignore_sidings = None
        self.displayed_fields = list()
        self.connect_settings_widget()
         # Declare MapTool
        self.map_tool: NearestPointFinder | None = None

    def create_spatial_index(self):
        # Build spatial index for the point layer
        self.spatial_index = QgsSpatialIndex(self.layer.getFeatures())

        # noinspection PyMethodMayBeStatic

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('StreckenkmFinder', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = get_icon_path()

        # Add Toolbar Action
        self.add_action(
            icon_path,
            text=self.tr(u'Streckenkilometer'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True)

        # Add Settings Action
        self.add_action(
            icon_path,
            text=self.tr(u'Settings'),
            callback=self.open_settings,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False)

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&DB_Streckenkm'),
                action)
            self.iface.removeToolBarIcon(action)

    def connect_settings_widget(self):
        self.settings_widget.accept.connect(self.update_settings)

    def update_settings(self):
        layer, self.field_name, self.field_is_real, self.ignore_sidings, self.displayed_fields = self.settings_widget.get_selected_settings()
        if layer != self.layer:
            self.layer = layer
            self.create_spatial_index()
        self.activate_maptool()

    def open_settings(self):
        self.settings_widget.reload_layer_combobox(self.layer)
        self.settings_widget.layer_changed()
        self.settings_widget.show()
        self.settings_widget.activateWindow()

    def map_tool_changed(self):
        if self.map_tool is not None:
            self.map_tool.hide_highlight()
            self.map_tool.delete_lines()

    def activate_maptool(self):
        self.map_tool = NearestPointFinder(self.iface, self.spatial_index, self.layer, self.field_name,
                                           self.field_is_real, self.ignore_sidings,self.displayed_fields)
        self.iface.mapCanvas().setMapTool(self.map_tool)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.spatial_index is None:
            self.open_settings()
        else:
            self.activate_maptool()
            # Fetch the currently loaded layers
