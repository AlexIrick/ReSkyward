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
import shutil

version = 'v0.1.0 BETA'

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))


class EditableListStyledItemDelegate(QtWidgets.QStyledItemDelegate):
    editFinished = QtCore.pyqtSignal(int)
    index = None
    
    def __init__(self, parent: QtCore.QObject=None):
        super().__init__(parent)
        self.closeEditor.connect(lambda: self.editFinished.emit(self.index.row()))

    def setEditorData(self, editor: QtWidgets.QWidget, index: QtCore.QModelIndex):
        self.index = index
        return super().setEditorData(editor, index)


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        self.setWindowTitle(f'ReSkyward - {version}')
        self.setWindowIcon(QtGui.QIcon('img/logo-min.svg'))
        # set variables
        self.skywardUsername = ''
        self.skywardPassword = ''
        self._class_ids = {}
        self.rememberMe = True

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
        self.clearUserDataButton.clicked.connect(self.clear_all_user_data)

        # signal to refresh UI after updated database is loaded
        self.database_refreshed.connect(self.load_skyward)
        # signal to display error message
        self.error_msg_signal.connect(self.error_msg_signal_handler)

        item_delegate = EditableListStyledItemDelegate(self.classesFilter)
        item_delegate.editFinished.connect(self.edited_item)
        self.classesFilter.setItemDelegate(item_delegate)

        # set dark title bar
        dark_title_bar(int(self.winId()))
        # self.login(False)
        self.load_skyward()
        splash.hide()
        self.show()

    database_refreshed = pyqtSignal()
    error_msg_signal = pyqtSignal(str)

    def edited_item(self, index):
        """
        Runs everytime a class name is edited.
        Updates vertical header and saves to file
        """
        text = self.classesFilter.item(index).text()
        self._class_ids[self.skyward_data[index-1]['class_info']['id']] = text
        self.skywardTable.setVerticalHeaderItem(index-1, QtWidgets.QTableWidgetItem(text))
        with open('data/CustomNames.json', 'w') as f:
            json.dump(self._class_ids, f, indent=4)

    def load_custom_classnames(self):
        """
        Loads custom class names from file to self._class_ids
        """
        if not os.path.exists('data/CustomNames.json'):
            return
        with open('data/CustomNames.json') as f:
            self._class_ids = json.load(f)

    def error_msg_signal_handler(self, msg):
        """
        Handles signals from self.error_msg_signal
        """
        self.lastRefreshedLabel.setText(msg)
        self.message_box('ReSkyward - Error', msg)

    def message_box(self, title, text, icon=QtWidgets.QMessageBox.Critical, buttons=QtWidgets.QMessageBox.Ok):
        """
        Displays a message box with the given title, text, icon, and buttons
        Needed to set the title bar color of the error message window
        """
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(buttons)
        dark_title_bar(int(msg_box.winId()))  # set custom dark title bar color
        return msg_box.exec_()  # returns the button clicked (ex: QtWidgets.QMessageBox.Ok)

    def load_skyward_data(self):
        """
        Loads the Skyward data from database
        """
        # Return error in status bar if no data already exists
        if not os.path.exists('data'):
            self.lastRefreshedLabel.setText('Please log into Skyward')
            return
        # Load data from file
        with open('data/SkywardExport.json') as f:
            skyward_data = json.load(f) # read data
        # Split headers to self.headers, and all class data to self.skyward_data (merges Ben Barber and Home Campus)
        self.headers = skyward_data[0][0]['headers'][1:]
        self.skyward_data = list(chain.from_iterable([x[1:] for x in skyward_data]))  # merge all classes together, skipping headers
        # Get the last updated date of the data
        with open('data/updated.json') as f:
            self.lastRefreshedLabel.setText('Last refreshed: ' + json.load(f)['date'])
        return True  # return True if data was loaded successfully

    def load_skyward(self, reload=True):
        """
        Update the Skyward table UI with the data from the database
        """
        if reload and not self.load_skyward_data():
            return  # if reload was requested, and failed, return
        self.skywardViewStackedWidget.setCurrentIndex(2)  # set to skyward table
        self.rememberMe = self.loginRememberCheck.isChecked()

        # load data to table
        self.load_custom_classnames()  # load custom class names, set to self._class_ids
        # clear data
        self.skywardTable.clear()
        self.classesFilter.clear()
        # add "All" to classes filter
        self.classesFilter.addItem('All')
        # set horizontal table headers (grading periods)
        for n, data in enumerate(self.headers):
            # add text to table header
            self.skywardTable.setHorizontalHeaderItem(n, self.create_table_item(data))

        # set grades, class filter items, and vertical table headers (classes)
        for n, data in enumerate(self.skyward_data):
            table_item = QtWidgets.QTableWidgetItem()
            item = QtWidgets.QListWidgetItem()
            if data['class_info']['id'] in self._class_ids:
                # if the class has a custom name saved, use it
                table_item.setText(self._class_ids[data['class_info']['id']])
                item.setText(self._class_ids[data['class_info']['id']])
            else:
                # otherwise, use the class name from Skyward
                table_item.setText(data['class_info']['class'])
                item.setText(data['class_info']['class'])
            # make item editable
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            # add item to table
            self.classesFilter.addItem(item)
            # add grades to table
            for m, data in enumerate(data['grades']):
                self.skywardTable.setItem(n, m, self.create_table_item(data))
            # ser class name vertical header in table
            self.skywardTable.setVerticalHeaderItem(n, table_item)

    @staticmethod
    def create_table_item(data):
        """
        Returns a table item with the given data
        """
        table_item = QtWidgets.QTableWidgetItem(data.get('text', ''))
        if data.get('highlighted'):
            if dark_mode:
                # set dark mode highlight color
                table_item.setBackground(QtGui.QColor(52, 79, 113))
            else:
                # set light mode highlight color
                table_item.setBackground(QtGui.QColor(255, 255, 120))
        if data.get('tooltip'):
            # set tooltip
            table_item.setToolTip(data['tooltip'])
        return table_item

    def title_bar_button_clicked(self, button_index, checked):
        """
        Update stacked widget index when a title bar button is clicked
        """
        _buttons = [self.dashboardButton, self.skywardButton, self.gpaButton, self.settingsButton]
        if not checked:
            _buttons[button_index].setChecked(True)  # force the button to stay checked
        _buttons.pop(button_index)
        for b in _buttons:
            b.setChecked(False)
        self.tabsStackedWidget.setCurrentIndex(button_index)

    def run_scraper(self, username, password):
        """
        (RUNS IN THREAD)
        Run scraper and return any errors
        Sends a signal to self.database_refreshed when the scraper is done
        """
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
        """
        Called when the save button is clicked
        Check if the username and password fields are empty
        """
        if self.usernameInput.text() and self.passwordInput.text():
            self.login()
        else:
            self.message_box('ReSkyward - Input Error', 'Please enter a username and password.')

    def login(self, should_refresh=True):
        """
        Saves the username and password as encrypted binary
        """
        print('saving')
        self.skywardUsername = self.usernameInput.text()
        self.skywardPassword = self.passwordInput.text()

        # Create user folder if needed
        if not os.path.exists('user'):
            os.mkdir('user')
        # Checks if key has already been generated
        if not os.path.exists('user/aes.bin'):
            # If key does not exist, generate and write to file a new 32-byte key
            key = get_random_bytes(32)
            with open('user/aes.bin', 'wb') as file_out:
                file_out.write(key)
        else:
            with open('user/aes.bin', 'rb') as f:
                key = f.read()

        if self.rememberMe:
            # encodes a json-formatted list containing the username and password (user login)
            data = json.dumps([self.skywardUsername, self.skywardPassword]).encode()
            # create cipher
            cipher = AES.new(key, AES.MODE_EAX)
            # encrypt user login
            ciphertext, tag = cipher.encrypt_and_digest(data)
            # writes encrypted user login to file
            with open("user/encrypted.bin", "wb") as file_out:
                [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]
        else:
            # clears user info file
            open("user/encrypted.bin", "wb").close()
        # refreshes database
        if should_refresh:
            self.refresh_database()
        self.usernameInput.clear()
        self.passwordInput.clear()

    def refresh_database(self):
        """
        Get password and decrypt
        """
        if self.loginRememberCheck.isChecked():
            # reads key from file
            with open("user/aes.bin", "rb") as file_in:
                key = file_in.read()
            # reads encrypted user info from file
            with open("user/encrypted.bin", "rb") as file_in:
                nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
            # generate cypher from key
            cipher = AES.new(key, AES.MODE_EAX, nonce)
            # decrypts user login
            data = cipher.decrypt_and_verify(ciphertext, tag).decode()
            # set text for refresh label
            self.lastRefreshedLabel.setText('Refreshing...')
            # run scraper as thread: inputs user login
            Thread(
                target=self.run_scraper,
                args=json.loads(data),
                daemon=True
            ).start()
        else:
            # set text for refresh label
            self.lastRefreshedLabel.setText('Refreshing...')
            # run scraper as thread: inputs user login
            Thread(
                target=self.run_scraper,
                args=[self.skywardUsername, self.skywardPassword],
                daemon=True
            ).start()

    def clear_all_user_data(self):
        # log out
        # open("user/aes.bin", "wb").close()
        # open("user/encrypted.bin", "wb").close()
        delete_folder('data')
        delete_folder('user')
        self.loginLabel.setText('Not Logged In')
        self.skywardViewStackedWidget.setCurrentIndex(0)  # set to skyward table
        # self.skywardTable.clear()


def dark_title_bar(hwnd):
    """
    Set a custom color for the title bar
    Windows 11: Sets color RGB (28, 38, 48)
    Windows 10: Sets color to black
    """
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


def delete_folder(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)



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
    
    # Apply custom fonts
    [QtGui.QFontDatabase.addApplicationFont(file) for file in glob('fonts/*.ttf')]
    # Create window
    MainWindow = QtWidgets.QMainWindow()
    
    window = UI()
    app.exec_()

    # runs after program is closed
    # deletes user data if remember me was not toggled on login
    if not window.rememberMe:
        delete_folder('data')
