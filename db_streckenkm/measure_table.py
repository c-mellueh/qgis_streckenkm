from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTableWidgetItem, QWidget, QTableWidget

class MeasureTable(QTableWidget):
    row_added = pyqtSignal(float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.values:list[float] = []
        self.differences:list[float] = []
    def clear_table(self):
        for row in reversed(range(self.rowCount())):
            self.removeRow(row)
        self.values = []
        self.differences = []

    def add_row(self,value):
        self.insertRow(self.rowCount())
        self.setItem(self.rowCount()-1, 0, QTableWidgetItem(str(round(value,4))))
        difference = self.values[-1] - value if self.values else 0.
        self.setItem(self.rowCount()-1, 1, QTableWidgetItem(str(round(difference,4))))
        self.values.append(value)
        self.differences.append(difference)
        self.row_added.emit(self.get_sum())

    def get_sum(self):
        return sum(self.differences)