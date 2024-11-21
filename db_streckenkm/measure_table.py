from PyQt5.QtCore import pyqtSignal,Qt
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QTableWidgetItem, QMessageBox, QTableWidget,QMenu,QAction

class MeasureTable(QTableWidget):
    KILOMETER = 1
    METER = 1000
    table_updated = pyqtSignal(float)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.values:list[float] = []
        self.differences:list[float] = []
        self.output_factor = self.KILOMETER
        self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.show_header_context_menu)
        self.position_factor = self.KILOMETER
        self.distance_factor = self.KILOMETER

    def show_header_context_menu(self,pos):
        index = self.horizontalHeader().logicalIndexAt(pos)
        menu = QMenu(self)
        action = QAction(menu)
        action.setText(self.tr("Toggle Unit"))
        menu.addAction(action)
        action.triggered.connect(lambda: self.toggle_unit(index))
        menu.exec(self.horizontalHeader().mapToGlobal(pos))

    def toggle_unit(self,column):
        if column == 0:
            self.position_factor = self.METER if self.position_factor == self.KILOMETER else self.KILOMETER
        if column == 1:
            self.distance_factor = self.METER if self.distance_factor == self.KILOMETER else self.KILOMETER
        self.refresh_table()

    def refresh_table(self):
        self.setRowCount(len(self.values))
        model = self.model()
        for row,(value,distance) in enumerate(zip(self.values,self.differences)):
            model.setData(model.index(row,0),value*self.position_factor)
            model.setData(model.index(row,1), distance * self.distance_factor)

        pos_title = self.tr("Position [km]") if self.position_factor == self.KILOMETER else self.tr("Position [m]")
        distance_title = self.tr("Distance [km]") if self.distance_factor == self.KILOMETER else self.tr("Distance [m]")
        self.setHorizontalHeaderLabels([pos_title,distance_title])
        self.table_updated.emit(self.get_sum())

    def clear_table(self):
        for row in reversed(range(self.rowCount())):
            self.removeRow(row)
        self.values = []
        self.differences = []

    def add_row(self,value):
        difference = value-self.values[-1] if self.values else 0.
        self.values.append(value)
        self.differences.append(difference)
        self.refresh_table()

    def get_sum(self):
        return sum(self.differences)*self.distance_factor