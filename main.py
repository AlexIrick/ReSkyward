from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5 import uic
import sys, os
from glob import glob
import json
from itertools import chain
from Crypto.Cipher import AES

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
        self.skywardPassword = ''

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
        self.refreshButton.clicked.connect(self.refresh_button_clicked)

        self.show()
        self.load_skyward()

    def load_skyward(self):
        with open('SkywardExport.json') as f:
            skyward_data = json.load(f) # read data
        self.headers = skyward_data[0][0]['headers'][1:]
        self.skyward_data = chain.from_iterable([x[1:] for x in skyward_data])  # merge all classes together, skipping headers
        # load data to table
        self.skywardTable.clear()
        for n, data in enumerate(self.headers):
            # add text to table header
            self.skywardTable.setHorizontalHeaderItem(n, self.create_table_item(data))
        for n, data in enumerate(self.skyward_data):
            table_item = QtWidgets.QTableWidgetItem(data['class_info']['class'])
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

    def save_button_clicked(self):
        self.skywardUsername = self.usernameInput.text()
        self.skywardPassword = self.passwordInput.text().encode()
        # encrypt password
        key = b'Sixteen byte key'
        data = self.skywardPassword
        cipher = AES.new(key, AES.MODE_EAX)
        # nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data)

        with open("encrypted.bin", "wb") as file_out:
            [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]

    def refresh_button_clicked(self):
        # self.load_skyward()
        # get password and decrypt
        key = b'Sixteen byte key'
        file_in = open("encrypted.bin", "rb")
        nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        print(data)


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
