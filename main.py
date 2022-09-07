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

        # find the widgets in the xml file

        # show ui
        self.show()


if __name__ == "__main__":
    # initialize app
    app = QApplication(sys.argv)
    # set style and fonts
    app.setStyle('Fusion')
    [QtGui.QFontDatabase.addApplicationFont(file) for file in glob('fonts/*.ttf')]
    
    MainWindow = QtWidgets.QMainWindow()
    
    window = UI()
    app.exec_()
