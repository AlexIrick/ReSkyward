from Crypto.Random import get_random_bytes
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
import sys, os
from glob import glob
import json
from threading import Thread
from itertools import chain
from Crypto.Cipher import AES
import skyward
import requests.exceptions
import darkdetect
import ctypes as ct

version = 'v0.1.0 BETA'

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        self.setWindowTitle(f'ReSkyward - {version}')
        self.setWindowIcon(QtGui.QIcon('img/logo-min.svg'))
        # set variables
        self.skywardUsername = ''
        self.skywardPasswordBin = ''

        # set minimum width
        self.weeksFilter.setSpacing(5)
        self.weeksFilter.setFixedWidth((self.weeksFilter.sizeHintForRow(0) + 13) * self.weeksFilter.count() + 2 * self.weeksFilter.frameWidth())
        self.weeksFilter.setFixedHeight(45)
        self.weeksFilterFrame.setBackgroundRole(QtGui.QPalette.Base)
        
        # set button connections
        self.dashboardButton.clicked.connect(lambda x: self.title_bar_button_clicked(0, x))
        self.skywardButton.clicked.connect(lambda x: self.title_bar_button_clicked(1, x))
        self.gpaButton.clicked.connect(lambda x: self.title_bar_button_clicked(2, x))
        self.settingsButton.clicked.connect(lambda x: self.title_bar_button_clicked(3, x))
        self.saveButton.clicked.connect(self.save_button_clicked)
        self.refreshButton.clicked.connect(self.refresh_database)

        self.database_refreshed.connect(self.load_skyward)
        self.error_msg_signal.connect(self.error_msg_signal_handler)

        # set dark title bar
        dark_title_bar(int(self.winId()))
        
        self.load_skyward()
        splash.hide()
        self.show()

    database_refreshed = pyqtSignal()
    error_msg_signal = pyqtSignal(str)

    def error_msg_signal_handler(self, msg):
        self.lastRefreshedLabel.setText(msg)
        self.message_box('ReSkyward - Error', msg)

    def message_box(self, title, text, icon=QtWidgets.QMessageBox.Critical, buttons=QtWidgets.QMessageBox.Ok):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(buttons)
        dark_title_bar(int(msg_box.winId()))
        return msg_box.exec_()

    def load_skyward_data(self):
        if not os.path.exists('data'):
            self.lastRefreshedLabel.setText('Please log into Skyward')
            return
        with open('data/SkywardExport.json') as f:
            skyward_data = json.load(f) # read data
        self.headers = skyward_data[0][0]['headers'][1:]
        self.skyward_data = chain.from_iterable([x[1:] for x in skyward_data])  # merge all classes together, skipping headers
        with open('data/updated.json') as f:
            self.lastRefreshedLabel.setText('Last refreshed: ' + json.load(f)['date'])
        return True
    
    def load_skyward(self):
        if not self.load_skyward_data():
            return
        # load data to table
        self.skywardTable.clear()
        self.classesFilter.clear()
        self.classesFilter.addItem('All')
        for n, data in enumerate(self.headers):
            # add text to table header
            self.skywardTable.setHorizontalHeaderItem(n, self.create_table_item(data))
        for n, data in enumerate(self.skyward_data):
            table_item = QtWidgets.QTableWidgetItem(data['class_info']['class'])
            item = QtWidgets.QListWidgetItem()
            item.setText(data['class_info']['class'])
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.classesFilter.addItem(item)
            for m, data in enumerate(data['grades']):
                self.skywardTable.setItem(n, m, self.create_table_item(data))
            self.skywardTable.setVerticalHeaderItem(n, table_item)
        
    @staticmethod
    def create_table_item(data):
        table_item = QtWidgets.QTableWidgetItem(data.get('text', ''))
        if data.get('highlighted'):
            if dark_mode:
                table_item.setBackground(QtGui.QColor(59, 77, 100))
            else:
                table_item.setBackground(QtGui.QColor(255, 255, 120))
        if data.get('tooltip'):
            table_item.setToolTip(data['tooltip'])
        return table_item

    def title_bar_button_clicked(self, button_index, checked):
        _buttons = [self.dashboardButton, self.skywardButton, self.gpaButton, self.settingsButton]
        if not checked:
            _buttons[button_index].setChecked(True)  # force the button to stay checked
        _buttons.pop(button_index)
        for b in _buttons:
            b.setChecked(False)
        self.tabsStackedWidget.setCurrentIndex(button_index)

    def run_scraper(self, username, password):
        try:
            skyward.GetSkywardPage(username, password)
        except skyward.SkywardLoginFailed:
            self.error_msg_signal.emit('Invalid login. Please try again.')
            self.loginLabel.setText(f'Login failed: {username}')
            self.title_bar_button_clicked(3, False)
        except requests.exceptions.ConnectionError:
            self.error_msg_signal.emit('Network error. Please check your internet connection.')
        else:
            self.database_refreshed.emit()
            self.loginLabel.setText(f'Logged in as {username}')

    def save_button_clicked(self):
        if self.usernameInput.text() and self.passwordInput.text():
            self.login()
        else:
            self.message_box('ReSkyward - Input Error', 'Please enter a username and password.')

    def login(self):
        print('saving')
        self.skywardUsername = self.usernameInput.text()
        self.skywardPasswordBin = self.passwordInput.text()
        # encrypt password
        if not os.path.exists('aes.bin'):
            key = get_random_bytes(32)
            with open('aes.bin', 'wb') as file_out:
                file_out.write(key)
        else:
            with open('aes.bin', 'rb') as f:
                key = f.read()
        # print(key)
        data = json.dumps([self.skywardUsername, self.skywardPasswordBin]).encode()
        cipher = AES.new(key, AES.MODE_EAX)
        # nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data)

        with open("encrypted.bin", "wb") as file_out:
            [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
        self.refresh_database()
        self.usernameInput.clear()
        self.passwordInput.clear()

    def refresh_database(self):
        # get password and decrypt
        # key = b'Sixteen byte key'
        with open("aes.bin", "rb") as file_in:
            key = file_in.read()

        with open("encrypted.bin", "rb") as file_in:
            nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]

        cipher = AES.new(key, AES.MODE_EAX, nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag).decode()
        # run scraper
        self.lastRefreshedLabel.setText('Refreshing...')
        Thread(
            target=self.run_scraper,
            args=json.loads(data),
            daemon=True
        ).start()

        # print(data, type(data))


def dark_title_bar(hwnd):
    if not (dark_mode and sys.platform == 'win32' and (version_num := sys.getwindowsversion()).major == 10):
        return
    set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
    if version_num.build >= 22000: # windows 11
        color = ct.c_int(0x30261C) # GBR Hex
        set_window_attribute(hwnd, 35, ct.byref(color), ct.sizeof(color))
    else:
        rendering_policy = 19 if version_num.build < 19041 else 20 # 19 before 20h1
        value = ct.c_int(True)
        set_window_attribute(hwnd, rendering_policy, ct.byref(value), ct.sizeof(value))


if __name__ == "__main__":
    # initialize app
    app = QApplication(sys.argv)
    # disable DPI scaling
    app.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling)
    
    # set splash screen
    splash_icon = QtGui.QPixmap('img/logo-min.svg')
    splash = QtWidgets.QSplashScreen(splash_icon, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()
    
    # dark mode pallette
    if dark_mode := darkdetect.isDark():
        app.setStyle('Fusion')
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(25,35,45))
        dark_palette.setColor(QtGui.QPalette.Light, QtGui.QColor(39, 49, 58))
        dark_palette.setColor(QtGui.QPalette.Dark, QtGui.QColor(39, 49, 58))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(39, 49, 58))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(25,35,45))
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(25,35,45))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.blue)
        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(59, 77, 100))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
        app.setPalette(dark_palette)
    
    [QtGui.QFontDatabase.addApplicationFont(file) for file in glob('fonts/*.ttf')]
    MainWindow = QtWidgets.QMainWindow()
    
    window = UI()
    app.exec_()
