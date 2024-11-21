import os

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QWidget,QMessageBox

from .. import get_icon_path
from ..ui.ui_DataWidget import Ui_DataWidget




class DataWidget(QWidget, Ui_DataWidget):
    ui_rows = 3  # Rows that are defined in the UI

    def __init__(self, km_value, orthogonal_distance):
        super().__init__()
        self.setupUi(self)
        self.label_km_val.setText(str(km_value))
        self.label_ortho_val.setText(str(orthogonal_distance))
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icons", "icon_copy.png")
        self.copy_icon = QIcon(icon_path)
        self.setWindowIcon(QIcon(get_icon_path()))
        self.setWindowTitle(self.tr("StreckenKM"))
        self.ui_rows = self.value_layout.rowCount()

        self.pushButton_km.clicked.connect(self.copy_km)
        self.pushButton_km.setIcon(self.copy_icon)
        self.pushButton_km.setText("")

        self.pushButton_ortho.clicked.connect(self.copy_ortho)
        self.pushButton_ortho.setIcon(self.copy_icon)
        self.pushButton_ortho.setText("")

        self.pushButton_sum.clicked.connect(self.copy_sum)
        self.pushButton_sum.setIcon(self.copy_icon)
        self.pushButton_sum.setText("")

        self.tableWidgetsum.table_updated.connect(self.update_sum)
        self.set_measure_tab_visible(False)



    def clear_layout(self):
        """Clear all items in the layout."""
        while self.value_layout.count():
            item = self.value_layout.takeAt(0)  # Take the first item
            widget = item.widget()  # Get the widget, if it's a widget
            if widget is not None:
                widget.deleteLater()  # Delete the widget
            else:
                del item  # Delete layout items if it's not a widget

    def update_sum(self,value:float):
        self.label_sum_val.setText(str(round(value,4)))
        if self.tableWidgetsum.distance_factor == self.tableWidgetsum.KILOMETER:
            self.label_sum.setText(self.tr("Sum [km]:"))
        else:
            self.label_sum.setText(self.tr("Sum [m]:"))
    def set_measure_tab_visible(self,state:bool):
        self.tableWidgetsum.setVisible(state)
        self.label_sum.setVisible(state)
        self.pushButton_sum.setVisible(state)
        self.label_sum_val.setVisible(state)

    def fill_value_list(self, value_list):
        index = 0
        self.clear_layout()
        for index, (value_name, value) in enumerate(value_list):
            self.value_layout.addWidget(QLabel(value_name), index + self.ui_rows, 0, 1, 1)
            self.value_layout.addWidget(QLabel(str(value)), index + self.ui_rows, 1, 1, 1)
            button = QPushButton()
            button.setText("")
            button.setMaximumSize(QSize(24, 24))
            button.setIcon(self.copy_icon)
            button.clicked.connect(lambda b, t=value: self.copy_to_clipboard(t))
            self.value_layout.addWidget(button, index + self.ui_rows, 2, 1, 1)

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(str(text))

    def set_km(self, km_value):
        self.label_km_val.setText(str(km_value))

    def set_ortho(self, orthogonal_distance):
        self.label_ortho_val.setText(str(orthogonal_distance))

    def copy_km(self):
        self.copy_to_clipboard(self.label_km_val.text())

    def copy_ortho(self):
        self.copy_to_clipboard(self.label_ortho.text())

    def copy_sum(self):
        self.copy_to_clipboard(self.label_sum.text())