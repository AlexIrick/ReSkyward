import sys
from glob import glob

import darkdetect
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QMainWindow, QTreeWidgetItem

from mixin import *
from main import UI

if __name__ == "__main__":
    # Changes the current directory to the directory containing the running script file
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # initialize app
    app = QApplication(sys.argv)
    # disable DPI scaling
    app.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling)

    # set splash screen
    splash_icon = QtGui.QPixmap(WINDOW_ICON)
    splash = QtWidgets.QSplashScreen(splash_icon, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()

    # dark mode palette
    if UI.DARK_MODE:
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
    [
        QtGui.QFontDatabase.addApplicationFont(file)
        for file in glob(join(dirname(__file__), 'fonts/*.ttf'))
    ]

    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # Create window
    MainWindow = QtWidgets.QMainWindow()

    # apply_stylesheet(app, theme='dark_cyan.xml')

    window = UI()
    splash.hide()
    window.show()
    app.exec_()

    # runs after program is closed
    # deletes user data if remember me was not toggled on login
    if not window.rememberMe:
        delete_folder('data')
