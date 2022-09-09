from typing_extensions import Self
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5 import uic
import sys, os
from glob import glob

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        
        # set minimum width
        self.weeksFilter.setSpacing(5)
        self.weeksFilter.setFixedWidth((self.weeksFilter.sizeHintForRow(0) + 13) * self.weeksFilter.count() + 2 * self.weeksFilter.frameWidth())
        self.weeksFilter.setFixedHeight(45)
        self.weeksFilterFrame.setBackgroundRole(QtGui.QPalette.Base)
        
        # set button connections
        self.dashboardButton.clicked.connect(lambda x: self.title_bar_button_clicked(0, x))
        self.skywardButton.clicked.connect(lambda x: self.title_bar_button_clicked(1, x))
        self.gpaButton.clicked.connect(lambda x: self.title_bar_button_clicked(2, x))
        
        # show ui
        self.show()

    def title_bar_button_clicked(self, button, checked):
        _buttons = [self.dashboardButton, self.skywardButton, self.gpaButton]
        if not checked:
            _buttons[button].setChecked(True)  # force the button to stay checked
        _buttons.pop(button)
        for b in _buttons:
            b.setChecked(False)


if __name__ == "__main__":
    # initialize app
    app = QApplication(sys.argv)
    # set style and fonts
    app.setStyle('Fusion')
    [QtGui.QFontDatabase.addApplicationFont(file) for file in glob('fonts/*.ttf')]
    
    MainWindow = QtWidgets.QMainWindow()
    
    # disable DPI scaling
    app.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling)
    
    window = UI()
    app.exec_()
