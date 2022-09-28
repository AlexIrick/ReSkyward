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

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("MainWindow.ui", self)

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
        self.error_msg_signal.connect(lambda x: self.lastRefreshedLabel.setText(x))

        self.show()
        self.load_skyward()

    database_refreshed = pyqtSignal()
    error_msg_signal = pyqtSignal(str)

    def load_skyward_data(self):
        if not os.path.exists('data'):
            self.lastRefreshedLabel.setText('Please log into Skyward')
            return False
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
            table_item.setBackground(QtGui.QColor(255, 255, 120))
        if data.get('tooltip'):
            table_item.setToolTip(data['tooltip'])
        return table_item

    def title_bar_button_clicked(self, button, checked):
        _buttons = [self.dashboardButton, self.skywardButton, self.gpaButton, self.settingsButton]
        if not checked:
            _buttons[button].setChecked(True)  # force the button to stay checked
        _buttons.pop(button)
        for b in _buttons:
            b.setChecked(False)
        self.tabsStackedWidget.setCurrentIndex(button)

    def run_scraper(self, username, password):
        try:
            skyward.GetSkywardPage(username, password)
        except skyward.SkywardLoginFailed:
            self.error_msg_signal.emit('Invalid login. Please try again.')
        except requests.exceptions.ConnectionError:
            self.error_msg_signal.emit('Network error. Please check your internet connection.')
        else:
            self.database_refreshed.emit()

    def save_button_clicked(self):
        if self.skywardUsername != self.usernameInput.text() or \
                self.skywardPasswordBin != self.passwordInput.text().encode():
            self.login()

    def login(self):
        print('saving')
        self.skywardUsername = self.usernameInput.text()
        self.skywardPasswordBin = self.passwordInput.text().encode()
        # encrypt password
        if not os.path.exists('aes.bin'):
            key = get_random_bytes(32)
            with open('aes.bin', 'wb') as file_out:
                file_out.write(key)
        else:
            with open('aes.bin', 'rb') as f:
                key = f.read()
        # print(key)
        data = self.skywardPasswordBin
        cipher = AES.new(key, AES.MODE_EAX)
        # nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data)

        with open("encrypted.bin", "wb") as file_out:
            [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
        self.loginLabel.setText(f'Logged in as {self.skywardUsername}')
        self.usernameInput.setText('')
        self.passwordInput.setText('')

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
            args=(self.skywardUsername, data),
            daemon=True
        ).start()

        # print(data, type(data))


if __name__ == "__main__":
    # initialize app
    app = QApplication(sys.argv)
    # set style and fonts
    # app.setStyle('Fusion')
    [QtGui.QFontDatabase.addApplicationFont(file) for file in glob('fonts/*.ttf')]
    MainWindow = QtWidgets.QMainWindow()
    
    # disable DPI scaling
    app.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling)
    
    window = UI()
    app.exec_()
