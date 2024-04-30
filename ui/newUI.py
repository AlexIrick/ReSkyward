from cgi import test
import os
import sys
from os.path import dirname, join

# import qdarktheme

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import (QApplication, QWidget)
# from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qfluentwidgets import (NavigationInterface,NavigationItemPosition, setTheme, Theme, qrouter, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow
import qtsass

from ReSkyward.ui import skywardview, settingsview, BellUI, customTitleBar

# import qdarkstyle

version = 'v0.1.0 BETA'

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))

    
class Window(FramelessWindow):
    def __init__(self, app):
        super().__init__()
        
        uic.loadUi(join(dirname(__file__), "NewMainWindow2.ui"), self)
        
        self.setTitleBar(customTitleBar.CustomTitleBar(self))
        setTheme(Theme.DARK)
        
        self.setWindowTitle(f'ReSkyward - {version}')
        self.setWindowIcon(QtGui.QIcon('img/logo-min.svg'))
        
        self.currentWidget = None
        
        # Connect focus gained/lost
        app.focusChanged.connect(self.onFocusChanged)
        
        # Create navigation interface
        self.navInterface = NavigationInterface(
            self, showMenuButton=True, showReturnButton=True)
        self.navContainer.addWidget(self.navInterface)
        
        # init views
        self.skywardView = skywardview.SkywardView(self)
        self.settingsView = settingsview.SettingsView(self)

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
    stack_switched = pyqtSignal(QWidget)
        
        
    def addSubInterface(self, interface: QWidget, icon, text: str, position=NavigationItemPosition.TOP):   
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
        self.setWindowTitle('ReSkyward')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        self.setQss()
        # self.setQss('titlebar')
        
        
    def switchTo(self, widget: QWidget):
        self.tabsStack.setCurrentWidget(widget)   
        self.currentWidget = widget 
        self.stack_switched.emit(widget)
       
            
    def setQss(self, in_focus=True):
        
        color = 'dark' if isDarkTheme() else 'light'
        
        # style = ''
        # with open(f'resource/{color}/main.scss', encoding='utf-8') as f:
        #     style = f.read()
        
        style=''
        # for sheet in ['main', 'titlebar', 'skyward', 'bell']:
        #     with open(f'resource/{color}/{sheet}.scss', encoding='utf-8') as f:
        #         style += f.read()
        # if not in_focus:
        #     with open(f'resource/{color}/focusout.scss', encoding='utf-8') as f:
        #         style += f.read()        
        
        # style = qtsass.compile(string=style)
        
        # style=''
        for sheet in ['main', 'titlebar', 'skyward', 'bell']:
            with open(f'resource/{color}/{sheet}.qss', encoding='utf-8') as f:
                style += f.read()
        if not in_focus:
            with open(f'resource/{color}/focusout.qss', encoding='utf-8') as f:
                style += f.read()
        # print(style)
        self.setStyleSheet(style)
    
    def onFocusChanged(self):
        '''
        Called when window focus is gained or lost. 
        Updates the qss so that the title bar labels/buttons become partially transparent if focus is lost  
        '''
        self.in_focus = self.isActiveWindow()
        self.setQss(self.in_focus)

        
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
