# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\SettingsWidget.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(586, 428)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.label__field = QtWidgets.QLabel(Form)
        self.label__field.setObjectName("label__field")
        self.gridLayout.addWidget(self.label__field, 1, 0, 1, 1)
        self.listWidget = QtWidgets.QListWidget(Form)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 5, 0, 1, 2)
        self.label_is_float = QtWidgets.QLabel(Form)
        self.label_is_float.setObjectName("label_is_float")
        self.gridLayout.addWidget(self.label_is_float, 2, 0, 1, 1)
        self.label_layer = QtWidgets.QLabel(Form)
        self.label_layer.setObjectName("label_layer")
        self.gridLayout.addWidget(self.label_layer, 0, 0, 1, 1)
        self.checkBox_ignore_empty = QtWidgets.QCheckBox(Form)
        self.checkBox_ignore_empty.setText("")
        self.checkBox_ignore_empty.setObjectName("checkBox_ignore_empty")
        self.gridLayout.addWidget(self.checkBox_ignore_empty, 3, 1, 1, 1)
        self.checkBox_select_all = QtWidgets.QCheckBox(Form)
        self.checkBox_select_all.setObjectName("checkBox_select_all")
        self.gridLayout.addWidget(self.checkBox_select_all, 4, 0, 1, 2)
        self.checkBox_is_float = QtWidgets.QCheckBox(Form)
        self.checkBox_is_float.setText("")
        self.checkBox_is_float.setObjectName("checkBox_is_float")
        self.gridLayout.addWidget(self.checkBox_is_float, 2, 1, 1, 1)
        self.comboBox_field = QtWidgets.QComboBox(Form)
        self.comboBox_field.setObjectName("comboBox_field")
        self.gridLayout.addWidget(self.comboBox_field, 1, 1, 1, 1)
        self.label_ignore_empty = QtWidgets.QLabel(Form)
        self.label_ignore_empty.setObjectName("label_ignore_empty")
        self.gridLayout.addWidget(self.label_ignore_empty, 3, 0, 1, 1)
        self.comboBox_layer = QtWidgets.QComboBox(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_layer.sizePolicy().hasHeightForWidth())
        self.comboBox_layer.setSizePolicy(sizePolicy)
        self.comboBox_layer.setObjectName("comboBox_layer")
        self.gridLayout.addWidget(self.comboBox_layer, 0, 1, 1, 1)
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 6, 0, 1, 2)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label__field.setText(_translate("Form", "Start_km Field:"))
        self.label_is_float.setText(_translate("Form", "Start_km is Float:"))
        self.label_layer.setText(_translate("Form", "Layer:"))
        self.checkBox_select_all.setText(_translate("Form", "Select All"))
        self.label_ignore_empty.setText(_translate("Form", "Ignore empty Features:"))
        self.pushButton.setText(_translate("Form", "Create Spatial Index"))
