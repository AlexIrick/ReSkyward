from PyQt5 import QtCore
from PyQt5.QtGui import QMouseEvent, QPainter
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView
from qfluentwidgets import TableWidget, style_sheet
from PyQt5.QtCore import Qt

class PointTableWidget(TableWidget):
    def __init__(self, rows, columns, parent=None):
        super(TableWidget, self).__init__(parent)
        self.setColumnCount(columns)
        self.setRowCount(rows)
        # QAbstractItemView
        self.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setTabKeyNavigation(False)
        self.setDropIndicatorShown(False)
        self.setDragDropOverwriteMode(False)
        # QTableView
        self.setShowGrid(True)
        self.setGridStyle(QtCore.Qt.PenStyle.SolidLine)
        # self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        # self.selectionMode())
        
        # Clicking
        self.lastRowReleased = -1
        self.lastColReleased = -1
        self.currentRowPressed = -1
        self.currentColPressed = -1
        
        # Headers
        h_header = QHeaderView(QtCore.Qt.Orientation.Horizontal)
        h_header.setDefaultSectionSize(40)
        h_header.setMinimumSectionSize(35)
        self.setHorizontalHeader(h_header)
        # self.itemClicked.connect(self.mousePress)
        # self.itemDoubleClicked.connect(self.mouseDoubleClick)
        
        v_header = QHeaderView(QtCore.Qt.Orientation.Vertical)
        v_header.setDefaultSectionSize(35)
        v_header.setMinimumSectionSize(30)
        self.setVerticalHeader(v_header)
        
        
    def paintEvent(self, event):
        super(TableWidget, self).paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setBrush(style_sheet.themeColor())
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.lastRowReleased == -1 and self.lastColReleased == -1:
            return

        item = self.item(self.lastRowReleased, self.lastColReleased)
        if item is not None:
            rect = self.visualItemRect(item)
            # Draw a blue line below the center of the last pressed item 
            w = 15 if not (self.lastRowReleased == self.currentRowPressed and self.lastColReleased == self.currentColPressed) else 10
            rect = QtCore.QRectF(rect.center().x()-w/2, rect.center().y()+10, w, 3)
            painter.drawRoundedRect(rect, 1.5, 1.5)

        
    def mouseReleaseEvent(self, e):
        super(TableWidget, self).mouseReleaseEvent(e)
        # print("current row realeased: " + str(self.currentRow()))
        self.lastRowReleased = self.currentRow()
        self.lastColReleased = self.currentColumn()
        self.currentRowPressed = -1
        self.currentColPressed = -1
        # self.repaint()
        # print("releas")
        
    def mousePressEvent(self, e):
        super(TableWidget, self).mousePressEvent(e)
        self.currentRowPressed = self.currentRow()
        self.currentColPressed = self.currentColumn()
        
    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        super().mouseDoubleClickEvent(e)
        self.currentRowPressed = self.currentRow()
        self.currentColPressed = self.currentColumn()
        self.repaint() # call repaint to ensure dot indicator is drawn correctly
        
