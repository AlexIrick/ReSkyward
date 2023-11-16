import contextlib
import queue

# import qdarktheme
from Crypto.Random import get_random_bytes
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QTreeWidgetItem, QListWidgetItem
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic
import sys, os
from glob import glob

import darkdetect
import ctypes as ct

from qfluentwidgets.components.widgets.frameless_window import FramelessWindow

import qfluentwidgets

# import qdarkstyle

version = 'v0.1.0 BETA'

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()


        uic.loadUi("NewMainWindow.ui", self)
        self.setWindowTitle(f'ReSkyward - {version}')
        self.setWindowIcon(QtGui.QIcon('img/logo-min.svg'))



        # dark_title_bar(int(self.winId()))

        splash.hide()
        self.show()




if __name__ == "__main__":
    # initialize app
    app = QApplication(sys.argv)
    # disable DPI scaling
    app.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling)

    # set splash screen
    splash_icon = QtGui.QPixmap('img/logo-min.svg')
    splash = QtWidgets.QSplashScreen(splash_icon, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()

    # dark mode palette
    if dark_mode := (darkdetect.isDark() or True):
        app.setStyle('Fusion')
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(25, 35, 45))
        dark_palette.setColor(QtGui.QPalette.Light, QtGui.QColor(39, 49, 58))
        dark_palette.setColor(QtGui.QPalette.Dark, QtGui.QColor(39, 49, 58))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(39, 49, 58))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(25, 35, 45))
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(25, 35, 45))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.blue)
        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(59, 77, 100))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
        app.setPalette(dark_palette)

    # Apply custom fonts
    [QtGui.QFontDatabase.addApplicationFont(file) for file in glob('fonts/*.ttf')]

    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())


    default_settings = {
        "hideCitizen": True,
    }

    # Create window
    MainWindow = QtWidgets.QMainWindow()

    # apply_stylesheet(app, theme='dark_cyan.xml')

    window = Window()
    app.exec_()

