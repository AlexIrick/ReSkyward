from cgi import test
import os
import sys
from os.path import dirname, join

# import qdarktheme

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QTableWidget)
# from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qfluentwidgets import (NavigationInterface,NavigationItemPosition, setTheme, Theme, qrouter, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, TitleBar

from ReSkyward.ui import skywardview, settingsview, config, BellUI

# import qdarkstyle

version = 'v0.1.0 BETA'

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))

    
class CustomTitleBar(TitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)
        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(16, 32) # width, height
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.insertSpacing(0, 16)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.titleLabel.setObjectName('titleLabel')
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.window().windowTitleChanged.connect(self.setTitle)
        
        

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(16, 16))
        


    
class Window(FramelessWindow):
    def __init__(self, app):
        super().__init__()
        
        uic.loadUi(join(dirname(__file__), "NewMainWindow2.ui"), self)
        
        self.setTitleBar(CustomTitleBar(self))
        setTheme(Theme.DARK)
        
        self.setWindowTitle(f'ReSkyward - {version}')
        self.setWindowIcon(QtGui.QIcon('img/logo-min.svg'))
        
        # Connect focus gained/lost
        app.focusChanged.connect(self.onFocusChanged)
        
        # Create navigation interface
        self.navInterface = NavigationInterface(
            self, showMenuButton=True, showReturnButton=True)
        self.navContainer.addWidget(self.navInterface)
        
        # init views
        self.skywardView = skywardview.SkywardView(self)
        self.settingsView = settingsview.SettingsView(self)
        self.config = config.Config(self)
        self.bell = BellUI.BellUI(self)

        self.initLayout()
        
        self.initNav()
        
        self.initWindow()

        self.show()
        
        
    database_refreshed = pyqtSignal()
    district_loaded = pyqtSignal()
    school_loaded = pyqtSignal()
    group_loaded = pyqtSignal()
    schedule_loaded = pyqtSignal()
        
        
    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP):   
        # self.stackWidget.addWidget(interface)
        self.navInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text
        )
        
        
    def initLayout(self):
        # self.hBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.hBoxLayout.setStretchFactor(self.tabsStack, 1)
        self.titleBar.raise_()
        self.navInterface.displayModeChanged.connect(self.titleBar.raise_)

        
    def initNav(self):
        # self.navInterface.showReturnButton(True)
        self.addSubInterface(self.dashPage, FIF.APPLICATION, 'Dashboard')
        # self.tabsStack.addWidget(self.skywardPage)
        self.addSubInterface(self.skywardPage, FIF.DICTIONARY, 'Skyward')
        self.addSubInterface(self.bellPage, FIF.RINGER, 'Bell Schedule')
        
        self.addSubInterface(self.settingsPage, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)
        
        # set the maximum width
        # self.navInterface.setExpandWidth(300)

        #Set the default route key
        qrouter.setDefaultRouteKey(self.tabsStack, self.dashPage.objectName())
        
        self.tabsStack.currentChanged.connect(self.onCurrentInterfaceChanged)
        
        # Set default page
        self.tabsStack.setCurrentIndex(0)
        self.onCurrentInterfaceChanged(0)
        
            
    def onCurrentInterfaceChanged(self, index):
        widget = self.tabsStack.widget(index)
        self.navInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.tabsStack, widget.objectName())
        
        
    def initWindow(self):
        self.resize(900, 700)
        # self.setWindowIcon(QIcon('resource/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        self.setQss()
        # self.setQss('titlebar')
        
        
    def switchTo(self, widget):
        self.tabsStack.setCurrentWidget(widget)        
        
            
    def setQss(self, focus_style=''):
        color = 'dark' if isDarkTheme() else 'light'
        style=''
        for sheet in ['main', 'titlebar', 'skyward', 'bell']:
            with open(f'resource/{color}/{sheet}.qss', encoding='utf-8') as f:
                style += f.read()
        self.setStyleSheet(style+focus_style)
    
    def onFocusChanged(self):
        '''
        Called when window focus is gained or lost. 
        Updates the qss so that the title bar labels/buttons become partially transparent if focus is lost  
        '''
        self.in_focus = self.isActiveWindow()
        if not self.in_focus:
            color = 'dark' if isDarkTheme() else 'light'
            with open(f'resource/{color}/focusout.qss', encoding='utf-8') as f:
                self.setQss(f.read())
        else:
            self.setQss()

        
    def resizeEvent(self, e):
        self.titleBar.move(0, 0)
        self.titleBar.resize(self.width()-0, self.titleBar.height())
    
        
    def get_skyward_view(self): 
        return self.skywardView
      

        
    




# if __name__ == "__main__":
#     # initialize app
#     app = QApplication(sys.argv)
#     # disable DPI scaling
#     app.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling)

#     # set splash screen
#     splash_icon = QtGui.QPixmap('img/logo-min.svg')
#     splash = QtWidgets.QSplashScreen(splash_icon, QtCore.Qt.WindowStaysOnTopHint)
#     splash.show()
    
#     # Create window
#     MainWindow = QtWidgets.QMainWindow()

#     # apply_stylesheet(app, theme='dark_cyan.xml')

#     window = Window()
#     app.exec_()
