from typing_extensions import Self
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

    def load_skyward(self):


        with open('SkywardExport.json') as f:
            skyward_data = json.load(f.read()) # read data
        self.headers = {
            i['text']: {'tooltip': i['tooltip'], 'highlighted': i['highlighted']}
            for i in skyward_data[0][0]['headers'][1:]  # get student data
        }
        self.skyward_data = chain.from_iterable([x[1:] for x in self.skyward_data])  # merge all classes together, skipping headers

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

        file_out = open("encrypted.bin", "wb")
        [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
        file_out.close()

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
