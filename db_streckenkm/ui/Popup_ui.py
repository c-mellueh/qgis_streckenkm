# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Popup.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtWidgets import QGridLayout,QLabel,QPushButton,QSizePolicy,QFrame
from PyQt5.QtCore import QSize,Qt,QMetaObject,QCoreApplication

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(284, 81)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushButton_ortho = QPushButton(Form)
        self.pushButton_ortho.setObjectName(u"pushButton_ortho")
        self.pushButton_ortho.setMaximumSize(QSize(24, 24))

        self.gridLayout.addWidget(self.pushButton_ortho, 1, 2, 1, 1)

        self.label_text_ortho = QLabel(Form)
        self.label_text_ortho.setObjectName(u"label_text_ortho")

        self.gridLayout.addWidget(self.label_text_ortho, 1, 0, 1, 1)

        self.label_text_km = QLabel(Form)
        self.label_text_km.setObjectName(u"label_text_km")

        self.gridLayout.addWidget(self.label_text_km, 0, 0, 1, 1)

        self.pushbutton_km = QPushButton(Form)
        self.pushbutton_km.setObjectName(u"pushbutton_km")
        self.pushbutton_km.setMaximumSize(QSize(24, 24))

        self.gridLayout.addWidget(self.pushbutton_km, 0, 2, 1, 1)

        self.label_value_km = QLabel(Form)
        self.label_value_km.setObjectName(u"label_value_km")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_value_km.sizePolicy().hasHeightForWidth())
        self.label_value_km.setSizePolicy(sizePolicy)
        self.label_value_km.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.gridLayout.addWidget(self.label_value_km, 0, 1, 1, 1)

        self.label_value_ortho = QLabel(Form)
        self.label_value_ortho.setObjectName(u"label_value_ortho")

        self.gridLayout.addWidget(self.label_value_ortho, 1, 1, 1, 1)

        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 2, 0, 1, 3)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.pushButton_ortho.setText("")
        self.label_text_ortho.setText(QCoreApplication.translate("Form", u"Orthogonal Distance", None))
        self.label_text_km.setText(QCoreApplication.translate("Form", u"Kilometer", None))
        self.pushbutton_km.setText("")
        self.label_value_km.setText(QCoreApplication.translate("Form", u"Value", None))
        self.label_value_ortho.setText(QCoreApplication.translate("Form", u"Value", None))
    # retranslateUi

