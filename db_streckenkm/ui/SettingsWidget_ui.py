# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\SettingsWidget_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SettingsWidget(object):
    def setupUi(self, SettingsWidget):
        SettingsWidget.setObjectName("SettingsWidget")
        SettingsWidget.resize(503, 158)
        self.gridLayout = QtWidgets.QGridLayout(SettingsWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(SettingsWidget)
        self.label_2.setEnabled(True)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.button_box = QtWidgets.QDialogButtonBox(SettingsWidget)
        self.button_box.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.button_box.setObjectName("button_box")
        self.gridLayout.addWidget(self.button_box, 4, 0, 1, 2)
        self.label = QtWidgets.QLabel(SettingsWidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox_layer = QtWidgets.QComboBox(SettingsWidget)
        self.comboBox_layer.setObjectName("comboBox_layer")
        self.gridLayout.addWidget(self.comboBox_layer, 0, 1, 1, 1)
        self.comboBox_field = QtWidgets.QComboBox(SettingsWidget)
        self.comboBox_field.setEnabled(True)
        self.comboBox_field.setObjectName("comboBox_field")
        self.gridLayout.addWidget(self.comboBox_field, 1, 1, 1, 1)
        self.checkBox_real = QtWidgets.QCheckBox(SettingsWidget)
        self.checkBox_real.setEnabled(True)
        self.checkBox_real.setObjectName("checkBox_real")
        self.gridLayout.addWidget(self.checkBox_real, 2, 0, 1, 2)
        self.checkBox_ignore_siding = QtWidgets.QCheckBox(SettingsWidget)
        self.checkBox_ignore_siding.setEnabled(True)
        self.checkBox_ignore_siding.setObjectName("checkBox_ignore_siding")
        self.gridLayout.addWidget(self.checkBox_ignore_siding, 3, 0, 1, 1)

        self.retranslateUi(SettingsWidget)
        self.button_box.accepted.connect(SettingsWidget.accept) # type: ignore
        self.button_box.rejected.connect(SettingsWidget.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(SettingsWidget)

    def retranslateUi(self, SettingsWidget):
        _translate = QtCore.QCoreApplication.translate
        SettingsWidget.setWindowTitle(_translate("SettingsWidget", "DB_Streckenkm"))
        self.label_2.setText(_translate("SettingsWidget", "Start_km Field"))
        self.label.setText(_translate("SettingsWidget", "Select a Layer"))
        self.checkBox_real.setText(_translate("SettingsWidget", "Attribut ist Dezimalzahl"))
        self.checkBox_ignore_siding.setText(_translate("SettingsWidget", "Nebengleise ignorieren"))