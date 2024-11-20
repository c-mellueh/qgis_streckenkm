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

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import Qgis, QgsSpatialIndex, QgsVectorLayer
from qgis.gui import QgsFieldComboBox, QgsMapLayerComboBox

from .. import get_icon_path
from ..ui.ui_SettingsWidget import Ui_SettingsWidget


class SettingsWidget(QtWidgets.QWidget, Ui_SettingsWidget):
    spatial_index_created = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(SettingsWidget, self).__init__(parent)

        self.setupUi(self)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tableWidget.itemChanged.connect(self.item_changed)
        self.comboBox_layer: QgsMapLayerComboBox
        self.comboBox_field: QgsFieldComboBox

        self.comboBox_layer.setShowCrs(True)
        self.comboBox_layer.setFilters(Qgis.LayerFilter.VectorLayer)

        self.comboBox_layer.layerChanged.connect(self.layer_changed)
        self.comboBox_layer_output.layerChanged.connect(self.update_output)
        self.setWindowIcon(QtGui.QIcon(get_icon_path()))
        self.spatial_index_dict: dict[QgsVectorLayer, QgsSpatialIndex] = dict()
        self.settings_dict: dict[QgsVectorLayer, tuple[
            QgsVectorLayer, QgsVectorLayer, str, str, bool, bool, list[str], dict[str, str], bool]] = dict()

        self.pushButton.clicked.connect(self.create_spatial_index)
        self.checkBox_select_all.clicked.connect(self.select_all_clicked)
        self.checkBox_save_points.clicked.connect(self.save_points_toggled)
        self.comboBox_layer_output.setFilters(Qgis.LayerFilter.PointLayer)
        self.comboBox_field.currentIndexChanged.connect(self.save_settings)
        self.comboBox_field_output.currentIndexChanged.connect(self.save_settings)
        self.checkBox_is_float.stateChanged.connect(self.save_settings)
        self.checkBox_ignore_empty.stateChanged.connect(self.save_settings)

        self.save_points_toggled()
        self.layer_changed()
        self.settings_save_is_blocked = False

    def save_points_toggled(self):
        cs = self.checkBox_save_points.isChecked()
        items = [ self.comboBox_layer_output,self.comboBox_field_output,self.label_input,self.label_output]


        if cs:
            [i.show() for i in items]
            self.tableWidget.showColumn(1)
            self.tableWidget.horizontalHeader().show()

        else:
            [i.hide() for i in items]
            self.tableWidget.hideColumn(1)
            self.tableWidget.horizontalHeader().hide()
    def select_all_clicked(self):
        cs = self.checkBox_select_all.checkState()
        for i in range(self.tableWidget.rowCount()):
            self.tableWidget.item(i, 0).setCheckState(cs)

    @property
    def layer(self) -> QgsVectorLayer | None:
        return self.comboBox_layer.currentLayer()

    @property
    def output_layer(self):
        return self.comboBox_layer_output.currentLayer()

    @property
    def start_field(self):
        return self.comboBox_field.currentField()

    @property
    def output_field(self):
        return self.comboBox_field_output.currentField()

    def create_spatial_index(self):
        # Build spatial index for the point layer
        self.spatial_index_dict[self.layer] = QgsSpatialIndex(self.layer.getFeatures())
        self.spatial_index_created.emit()

    def item_changed(self, focus_item: QtWidgets.QListWidgetItem):
        new_checkstate = focus_item.checkState()
        items = self.tableWidget.selectedItems()
        for item in items:
            item.setCheckState(new_checkstate)
        self.save_settings()
        if self.all_items_are_checked():
            self.checkBox_select_all.setChecked(True)
        else:
            self.checkBox_select_all.setChecked(False)

    def all_items_are_checked(self):
        items = [self.tableWidget.item(i, 0) for i in range(self.tableWidget.rowCount())]
        checkstates = set(item.checkState() for item in items if item is not None)
        return checkstates == {QtCore.Qt.CheckState.Checked}

    def get_field_matchup(self):
        output_dict = dict()
        for row in range(self.tableWidget.rowCount()):
            if not self.tableWidget.item(row,0):
                continue
            input = self.tableWidget.item(row, 0).text()
            if not self.tableWidget.cellWidget(row,1):
                continue
            output = self.tableWidget.cellWidget(row, 1).currentField()
            if output:
                output_dict[input] = output
        return output_dict

    def get_current_settings(self) -> tuple[
        QgsVectorLayer, QgsVectorLayer, str, str, bool, bool, list[str], dict[str, str], bool]:
        """
        :return: (
        0:Layer,                1:Output-Layer,
        2:Start Field,          3:Output-Field,
        4:Attribute Is Float,   5:Ignore Empty,
        6:checked_fields,       7:Matchup,
        8:save to PointLayer)
        """
        attribute_is_real = self.checkBox_is_float.isChecked()
        ignore_sidings = self.checkBox_ignore_empty.isChecked()
        checked_fields = self.get_checked_field_names()
        matchup = self.get_field_matchup()
        return (self.layer, self.output_layer,
                self.start_field, self.output_field,
                attribute_is_real, ignore_sidings,
                checked_fields, matchup,
                self.checkBox_save_points.isChecked())

    def get_checked_field_names(self):
        checked_fields = list()
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if not item:
                continue
            if item.checkState() == QtCore.Qt.Checked:
                checked_fields.append(item.text())
        return checked_fields

    def clear_table_widget(self):
        for row in reversed(range(self.tableWidget.rowCount())):
            self.tableWidget.removeRow(row)

    def layer_changed(self):
        if not isinstance(self.layer, QgsVectorLayer):
            return
        self.settings_save_is_blocked = True
        self.comboBox_field.setLayer(self.layer)
        settings =  self.get_saved_setting(self.layer)
        if settings[0] is None:
            if "VON_KM_V" in [f.name() for f in self.comboBox_field.fields()]:
                self.comboBox_field.setCurrentText("VON_KM_V")

        output_layer = settings[1]
        output_field = settings[3]
        write_to_layer = settings[8]
        if write_to_layer is not None:
            self.checkBox_save_points.setChecked(write_to_layer)
        if output_layer:
            self.comboBox_layer_output.setLayer(output_layer)
        if output_field:
            self.comboBox_field_output.setField(output_field)

        self.checkBox_is_float.setChecked(True if settings[4] else False)
        self.checkBox_ignore_empty.setChecked(True if settings[5] else False)
        self.clear_table_widget()
        self.checkBox_select_all.setChecked(False)
        self.fill_field_table()
        self.update_output()
        self.settings_save_is_blocked = False

    def fill_field_table(self):
        checked_fields = self.get_saved_setting(self.layer)[6]
        matchup = self.get_saved_setting(self.layer)[7]

        if not checked_fields:
            checked_fields = []
        if not matchup:
            matchup = dict()

        field_names = [field.name() for field in self.layer.fields()]
        self.clear_table_widget()
        self.tableWidget.setRowCount(len(field_names))
        for row, name in enumerate(field_names):
            item = QtWidgets.QTableWidgetItem(name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            if name in checked_fields:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            self.tableWidget.setItem(row, 0, item)
            field_cb = QgsFieldComboBox()
            field_cb.setAllowEmptyFieldName(True)
            field_cb.setLayer(self.output_layer)
            field_cb.currentIndexChanged.connect(self.save_settings)
            self.tableWidget.setCellWidget(row, 1, field_cb)
            match = matchup.get(name)
            if match is not None:
                field_cb.setField(match)

    def update_output(self):
        self.settings_save_is_blocked = True
        settings = self.get_saved_setting(self.layer)
        self.comboBox_field_output.setLayer(self.output_layer)
        if self.output_layer != settings[1]:
            settings = self.get_saved_setting(None)
        if settings[3] is not None:
            self.comboBox_field_output.setField(settings[3])
        matchup = self.get_saved_setting(self.layer)[7] or {}

        for row in range(self.tableWidget.rowCount()):
            widget:QgsFieldComboBox = self.tableWidget.cellWidget(row,1)
            widget.setLayer(self.output_layer)
            if not widget:
                continue
            match = matchup.get(self.tableWidget.item(row,0).text()) or ""
            if not match:
                widget.setCurrentIndex(0)
            else:
                widget.setField(match)
        self.settings_save_is_blocked = False


    def save_settings(self):
        if self.settings_save_is_blocked:
            return


        self.settings_dict[self.layer] = self.get_current_settings()

    def is_setting_existing(self, layer: QgsVectorLayer):
        return True if self.settings_dict.get(layer) else False

    def get_saved_setting(self, layer: QgsVectorLayer|None) -> tuple[QgsVectorLayer,QgsVectorLayer,str,str,bool,bool,list[str],dict[str,str],bool]|tuple:
        if not self.is_setting_existing(layer) or layer is None:
            return None, None, None, None, None,None,None,None,None
        return self.settings_dict[layer]
