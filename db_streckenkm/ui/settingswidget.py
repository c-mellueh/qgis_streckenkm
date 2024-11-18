# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StreckenkmFinderDialog
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

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QListWidgetItem
from qgis.PyQt import QtCore, QtWidgets
from qgis.core import QgsProject, QgsVectorLayer,QgsMessageLog,Qgis
from PyQt5 import QtWidgets
from .SettingsWidget_ui import Ui_SettingsWidget
from .. import get_icon_path

class SettingsWidget(QtWidgets.QWidget, Ui_SettingsWidget):
    accept = QtCore.pyqtSignal()
    reject = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(SettingsWidget, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listWidget.itemChanged.connect(self.item_changed)
        self.layer_dict = dict()
        self.comboBox_layer.currentTextChanged.connect(self.layer_changed)
        self.reload_layer_combobox()
        self.accept.connect(self.hide)
        self.reject.connect(self.hide)
        self.accept.connect(self.save_settings)
        QgsMessageLog.logMessage(f"Icon Path: {get_icon_path()}", "StreckenKM", Qgis.Info)
        self.setWindowIcon(QIcon(get_icon_path()))

    def item_changed(self,focus_item:QListWidgetItem):
        new_checkstate = focus_item.checkState()
        items = self.listWidget.selectedItems()
        for item in items:
            item.setCheckState(new_checkstate)


    def reload_layer_combobox(self, selected_layer=None):
        layers = QgsProject.instance().layerTreeRoot().children()
        # Clear the contents of the comboBox from previous runs
        self.comboBox_layer.clear()
        # Populate the comboBox with names of all the loaded layers
        self.comboBox_layer.addItems([layer.name() for layer in layers if isinstance(layer.layer(), QgsVectorLayer)])
        if selected_layer:
            self.comboBox_layer.setCurrentText(selected_layer.name())

    def get_selected_settings(self):
        layer_name = self.comboBox_layer.currentText()
        layers = QgsProject.instance().mapLayers().values()
        layer: QgsVectorLayer | None = None
        for layer in layers:
            if layer.name() == layer_name:
                layer = layer
                break
        field_name = self.comboBox_field.currentText()
        attribute_is_real = self.checkBox_real.isChecked()
        ignore_sidings = self.checkBox_ignore_siding.isChecked()
        checked_fields = self.get_checked_field_names()
        return layer, field_name, attribute_is_real, ignore_sidings, checked_fields

    def get_checked_field_names(self):
        checked_fields = list()
        for row in range(self.listWidget.count()):
            item = self.listWidget.item(row)
            if item.checkState() == QtCore.Qt.Checked:
                checked_fields.append(item.text())
        return checked_fields

    def layer_changed(self):
        layer, _, _, _, _ = self.get_selected_settings()
        if not isinstance(layer, QgsVectorLayer):
            return
        if self.layer_dict.get(layer) is None:
            field_name, attribute_is_real, ignore_sidings, checked_fields = None, None, None, None
        else:
            field_name, attribute_is_real, ignore_sidings, checked_fields = self.layer_dict[layer]

        field_names = [field.name() for field in layer.fields()]
        self.comboBox_field.clear()
        self.comboBox_field.addItems(field_names)
        if field_name:
            self.comboBox_field.setCurrentText(field_name)
        self.checkBox_real.setChecked(True if attribute_is_real else False)
        self.checkBox_ignore_siding.setChecked(True if ignore_sidings else False)

        self.listWidget.clear()
        if not checked_fields:
            checked_fields = []
        for name in field_names:
            item = QtWidgets.QListWidgetItem(name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            if name in checked_fields:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            self.listWidget.addItem(item)

    def save_settings(self):
        layer, field_name, attribute_is_real, ignore_sidings, checked_fields = self.get_selected_settings()
        self.layer_dict[layer] = [field_name, attribute_is_real, ignore_sidings, checked_fields]
