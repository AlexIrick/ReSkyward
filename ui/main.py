import ctypes as ct
import os
import sys
import json
from itertools import chain
from os.path import dirname, join
from threading import Thread

import darkdetect

# import qdarktheme
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QMainWindow, QTreeWidgetItem, QLineEdit

import BellUI
from mixin import *
import config
import login

import experimentmode, skywardview

# from qt_material import list_themes, apply_stylesheet


version = 'v0.1.0 BETA'

try:
    sys.path.append(sys._MEIPASS)
except:
    sys.path.append(os.path.dirname(__file__))


class EditableStyledItemDelegate(QtWidgets.QStyledItemDelegate):
    editFinished = QtCore.pyqtSignal(QtCore.QModelIndex)
    model_index = None

    def __init__(self, parent: QtCore.QObject = None):
        super().__init__(parent)
        self.closeEditor.connect(lambda: self.editFinished.emit(self.model_index))

    def setEditorData(self, editor: QtWidgets.QWidget, model_index: QtCore.QModelIndex):
        self.model_index = model_index
        return super().setEditorData(editor, model_index)


class UI(QMainWindow):
    DARK_MODE = darkdetect.isDark()

    def __init__(self):
        super(UI, self).__init__()

        self.class_assignments = []
        self.assignment_files = None
        self.skyward_data = None
        uic.loadUi(join(dirname(__file__), "MainWindow.ui"), self)
        self.setWindowTitle(f'ReSkyward - {version}')
        self.setWindowIcon(QtGui.QIcon(WINDOW_ICON))

        # set variables
        self.skywardUsername = ''
        self.skywardPassword = ''
        self._class_ids = {}
        self.rememberMe = False
        self.citizenColumns = [1, 4, 7, 12, 15, 18]
        self.experimentItems = []
        self.classViewItems = []

        self.notesSumText = ''

        # BELL SCHEDULE
        self.bellUI = BellUI.BellUI(self)
        # hide bell view
        self.bellStackedWidget.hide()
        self.bellRefreshTimer = QTimer()
        self.bellRefreshTimer.setInterval(1000)  # 1 seconds
        self.bellRefreshTimer.timeout.connect(self.bellUI.refresh_view)
        # self.bellSettingsList.currentRowChanged.connect(lambda: self.bellUI.bell_settings_selected(False))
        self.bellDistrictsList.currentRowChanged.connect(self.bellUI.district_changed)
        self.bellSchoolsList.currentRowChanged.connect(self.bellUI.school_changed)
        self.bellGroupsList.currentRowChanged.connect(self.bellUI.group_changed)
        self.bellToggleButton.clicked.connect(self.bellUI.bell_toggle)

        # UI Finetuning
        # set minimum width
        self.weeksFilter.setSpacing(5)
        self.weeksFilter.setFixedWidth(
            (self.weeksFilter.sizeHintForRow(0) + 13) * self.weeksFilter.count()
            + 2 * self.weeksFilter.frameWidth()
        )
        self.weeksFilter.setFixedHeight(45)
        self.weeksFilterFrame.setBackgroundRole(QtGui.QPalette.Base)
        # set class tree view column sizes
        self.classViewTree.header().resizeSection(0, 250)
        self.classViewTree.header().resizeSection(1, 90)
        self.classViewTree.header().resizeSection(3, 90)

        self.experimentTree.header().resizeSection(1, 50)

        # DASHBOARD
        # set button connections; x = is checked when button is checkable
        self.dashboardButton.clicked.connect(
            lambda x: self.title_bar_button_clicked('dashboard', x)
        )
        self.skywardButton.clicked.connect(lambda x: self.title_bar_button_clicked('skyward', x))
        self.gpaButton.clicked.connect(lambda x: self.title_bar_button_clicked('gpa', x))
        self.notesButton.clicked.connect(lambda x: self.title_bar_button_clicked('notes', x))
        self.settingsButton.clicked.connect(lambda: self.settings_clicked(-1))
        self.settingsLoginButton.clicked.connect(lambda: self.settings_clicked(0))
        self.settingsBellButton.clicked.connect(lambda: self.settings_clicked(4, 1))
        self.skywardLoginButton.clicked.connect(self.login_button)
        self.refreshButton.clicked.connect(self.refresh_button)

        self.clearUserDataButton.clicked.connect(self.clear_all_user_data)

        self.experimentButton.clicked.connect(self.experiment_toggle)
        self.experimentAddButton.clicked.connect(self.experiment_add)
        self.experimentRemoveButton.clicked.connect(self.experiment_remove)

        # list connections; x = item clicked
        self.classesFilter.itemClicked.connect(lambda: self.filter_selected('class'))
        self.weeksFilter.itemClicked.connect(lambda: self.filter_selected('week'))

        # signal to refresh UI after updated database is loaded
        self.database_refreshed.connect(self.load_skyward)
        # signal to display error message
        self.error_msg_signal.connect(self.error_msg_signal_handler)

        class_item_delegate = EditableStyledItemDelegate(self.classesFilter)
        class_item_delegate.editFinished.connect(self.edited_item)
        self.classesFilter.setItemDelegate(class_item_delegate)

        class_view_delegate = EditableStyledItemDelegate(self.classViewTree)
        class_view_delegate.editFinished.connect(self.display_experiment_grades)
        self.classViewTree.setItemDelegate(class_view_delegate)

        # Summarize note taker
        self.notesSummarize.clicked.connect(self.summarize_notes)

        # hide filters
        self.classesFilter.hide()
        self.weeksFilter.hide()
        # hide experiment
        self.experimentGroup.hide()

        # SKYWARD LOGIN
        self.showPasswordCheck.stateChanged.connect(self.set_password_visibility)

        # config
        self.hideCitizenCheck.stateChanged.connect(lambda: self.config.set_hide_citizen(self.hideCitizenCheck.isChecked()))
        self.hideCitizen = False
        self.config = config.Config(self)

        # set dark title bar
        # username = get_user_info()[0]
        # self.loginLabel.setText(f'Logged in as {self.skywardUsername}')
        # self.helloUserLabel.setText(f'Hello {self.skywardUsername}!')

        dark_title_bar(int(self.winId()))

        # Create user folder if needed
        if not os.path.exists('user'):
            os.mkdir('user')

        self.load_creds()

    database_refreshed = pyqtSignal()
    error_msg_signal = pyqtSignal(str)

    """
    ---Experiment---
    """

    def experiment_toggle(self):
        """
        Toggles experiment mode
        """
        if self.experimentGroup.isHidden():
            # Enable experiment
            self.experimentGroup.show()
            self.experimentButton.setText('')
            self.experimentButton.setFont(QFont('Segoe MDL2 Assets', 14))
            self.classViewTree.header().hideSection(2)
            # Generate experiment
            if len(self.experimentItems) == 0:
                periods = ['1st', '2nd', '3rd', 'Sem1', '4th', '5th', '6th', 'Sem2', 'Avg']
                for period in periods:
                    item = QTreeWidgetItem()
                    item.setText(0, period)
                    self.experimentItems.append(item)
                    self.experimentTree.addTopLevelItem(item)

            self.display_experiment_grades()
        else:
            # Disable experiment
            self.experimentGroup.hide()
            self.experimentButton.setText('🖩')
            self.experimentButton.setFont(QFont('Poppins', 25))
            self.classViewTree.header().showSection(2)
            # for item in self.classViewItems:
            #     item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            classes_item_index = self.get_selected_filter_index(self.classesFilter)
            self.load_class_view(
                self.class_assignments[classes_item_index - 1],
                self.weeksFilter.currentItem().text(),
                True,
            )

    def experiment_calculate_grades(self):
        """
        Calculates the six weeks and semester averages
        """
        return experimentmode.calculate_grades(self.classViewItems)

    def experiment_add(self):
        """
        Called when the user presses the add button in the experiment mode
        Adds an item to the class view tree
        """
        item = experimentmode.create_assignment_item(self.weeksFilter.currentItem().text())
        self.classViewItems.append(item)
        self.classViewTree.addTopLevelItem(item)

    def experiment_remove(self):
        """
        Called when user presses the delete button in the experiment mode
        Deletes the selected class view item
        """
        root = self.classViewTree.invisibleRootItem()
        for item in self.classViewTree.selectedItems():
            (item.parent() or root).removeChild(item)
            self.classViewItems.remove(item)

    def display_experiment_grades(self):
        grades = self.experiment_calculate_grades()
        for i, grade in enumerate(grades):
            self.experimentItems[i].setText(1, str(grade))
        # Make items editable
        for item in self.classViewItems:
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

    def get_selected_filter_index(self, list_widget):
        return list_widget.indexFromItem(list_widget.currentItem()).row()

    def get_current_assignments(self):
        classes_item_index = self.get_selected_filter_index(self.classesFilter)
        return self.class_assignments[classes_item_index - 1]

    """
    ---Skyward View---
    """

    def edited_item(self, model_index):
        """
        Runs everytime a class name is edited.
        Updates vertical header and saves to file
        """
        index = model_index.row()  # Get row index
        text = self.classesFilter.item(index).text()
        self._class_ids[self.skyward_data[index - 1]['class_info']['id']] = text
        self.skywardTable.setVerticalHeaderItem(index - 1, QtWidgets.QTableWidgetItem(text))
        with open('data/CustomNames.json', 'w') as f:
            json.dump(self._class_ids, f, indent=4)

    def filter_selected(self, filter_type):
        """
        Runs whenever a filter is clicked
        Changes skyward views
        """
        # Get indexes of selected filter item
        classes_item_index = self.get_selected_filter_index(self.classesFilter)
        # If they are both set to all then change to table view
        if classes_item_index == 0:
            self.skywardViewStackedWidget.setCurrentIndex(2)  # set to skyward table view
        else:
            self.skywardViewStackedWidget.setCurrentIndex(1)  # set to assignments view
            if filter_type == 'class':
                # load the tree view
                self.load_class_view(
                    self.class_assignments[classes_item_index - 1],
                    self.weeksFilter.currentItem().text(),
                    True,
                )
            elif filter_type == 'week':
                # load the tree view
                self.load_class_view(
                    self.class_assignments[classes_item_index - 1],
                    self.weeksFilter.currentItem().text(),
                    not self.classViewItems,
                )

        # Hide skyward table columns according to filters
        self.hide_skyward_table_columns()
        # Calculate and display experiment grades if its not hidden
        if not self.experimentGroup.isHidden():
            self.display_experiment_grades()

    def hide_skyward_table_columns(self):
        """
        Hides/shows skyward table columns depending on filters and settings
        """
        # get weeks filter index
        weeks_item_index = self.get_selected_filter_index(self.weeksFilter)
        for n, h in enumerate(self.headers):
            if weeks_item_index != 0:
                # print(weeks_item_index, h['text'])
                self.skywardTable.setColumnHidden(
                    n,
                    (str(weeks_item_index) not in h['text'])
                    or (self.hideCitizen and (n in self.citizenColumns)),
                )
            else:
                self.skywardTable.setColumnHidden(
                    n, self.hideCitizen and (n in self.citizenColumns)
                )

    def load_class_view(self, assignments, week_filter, should_regen):
        """
        Loads the class view for a class
        :param should_regen: Determines if class view should be fully regenerated from assignments list or just toggle rows
        :param assignments: List of assignments in the selected class
        :param week_filter: Current selected 6-weeks filter (text)
        """
        if should_regen:
            # Clear tree view (does not clear headers)
            self.classViewTree.clear()
            self.classViewItems = []
            for assignment in assignments:
                # Only add assignment if in the correct 6-weeks
                # matching_weeks_filter = week_filter.lower() in [assignment['due'][1].strip('()').lower(), 'all']
                if 'due' in assignment:
                    # Hide weeks column if not in all-weeks filter
                    self.hide_weeks_column(week_filter)
                    # create class view item
                    item = skywardview.create_class_view_item(assignment)

                    self.classViewItems.append(item)
                    # Add assignment to tree
                    self.classViewTree.addTopLevelItem(item)
        else:
            # Hide weeks column if not in all-weeks filter
            self.hide_weeks_column(week_filter)
        self.classViewItems = skywardview.hide_items_by_six_weeks(self.classViewItems, week_filter)

    def hide_weeks_column(self, week_filter):
        """
        Hides weeks column if not in all-weeks filter
        :param week_filter: The text of the selected six-weeks filter
        """
        if week_filter.lower() != 'all':
            self.classViewTree.header().hideSection(3)
        else:
            self.classViewTree.header().showSection(3)

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

    def message_box(
            self, title, text, icon=QtWidgets.QMessageBox.Critical, buttons=QtWidgets.QMessageBox.Ok
    ):
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
            return False
        # Load data from file
        with open('data/SkywardExport.json') as f:
            skyward_data = json.load(f)  # read data
        # Split headers to self.headers, and all class data to self.skyward_data (merges Ben Barber and Home Campus)
        self.headers = skyward_data[0][0]['headers'][1:]
        self.skyward_data = list(
            chain.from_iterable([x[1:] for x in skyward_data])
        )  # merge all classes together, skipping headers
        # Get assignment files directories
        self.assignment_files = [x['assignments'] for x in self.skyward_data]
        # Get assignments
        for file_dir in self.assignment_files:
            with open(file_dir) as f:
                load = json.load(f)
                self.class_assignments.append(load)
                # print([file_dir, load])
        # Get the last updated date of the data
        with open('data/updated.json') as f:
            self.lastRefreshedLabel.setText('Last refreshed: ' + json.load(f)['date'])
        return True  # return True if data was loaded successfully

    def load_skyward(self, reload=True):
        """
        Update the Skyward table UI with the data from the database
        """
        if reload and not self.load_skyward_data():
            return False  # if reload was requested, and failed, return
        self.skywardViewStackedWidget.setCurrentIndex(2)  # set to skyward table
        # show filters
        self.classesFilter.show()
        self.weeksFilter.show()

        # load data to table
        self.load_custom_classnames()  # load custom class names, set to self._class_ids
        # clear data
        self.skywardTable.clear()
        self.classesFilter.clear()
        # add "All" to classes filter
        self.classesFilter.addItem('All')
        self.classesFilter.setCurrentRow(0)
        # set horizontal table headers (grading periods)
        for n, data in enumerate(self.headers):
            # add text to table header
            self.skywardTable.setHorizontalHeaderItem(
                n, skywardview.create_table_item(data, UI.DARK_MODE)
            )

        # set grades, class filter items, and vertical table headers (classes)
        for n, data in enumerate(self.skyward_data):
            # load items
            table_item, item = skywardview.get_class_name_items(data, self._class_ids)
            # add item to table
            self.classesFilter.addItem(item)
            if n >= self.skywardTable.rowCount():
                self.skywardTable.insertRow(self.skywardTable.rowCount())
            # add grades to table
            for m, data in enumerate(data['grades']):
                self.skywardTable.setItem(n, m, skywardview.create_table_item(data, UI.DARK_MODE))
            # set class name vertical header in table
            self.skywardTable.setVerticalHeaderItem(n, table_item)

        return True

    def title_bar_button_clicked(self, button_ref, checked):
        """
        Update stacked widget index when a title bar button is clicked
        """
        # _buttons = []
        _buttons = {
            'dashboard': [self.dashboardButton, 0],
            'skyward': [self.skywardButton, 1],
            'gpa': [self.gpaButton, 2],
            'notes': [self.notesButton, 3],
            'settings': [self.settingsButton, 4],
        }

        # save settings if clicking off of settings tab
        # if (
        #         self.tabsStackedWidget.currentIndex() == _buttons['settings'][1]
        #         and button_ref != 'settings'
        # ):
        #     # self.save_settings()

        # Uncheck all buttons
        for b in _buttons.values():
            b[0].setChecked(False)

        # Check selected button
        _buttons[button_ref][0].setChecked(True)  # force the button to stay checked
        self.tabsStackedWidget.setCurrentIndex(_buttons[button_ref][1])

    """
    ---Settings---
    """

    # TODO: improve this (horrible) system
    def settings_clicked(self, index, bell_index=-1):
        """
        Called when a settings button is clicked. Shows settings page and selects settings category
        :param index: Index of settings category. Set to -1 to not change row
        :param bell_index: Index of bell settings within settings page.
        Set to -1 to not change row or if it does not apply
        """
        self.title_bar_button_clicked('settings', self.settingsButton.isChecked())
        if index != -1:
            self.settingsCategoriesList.setCurrentRow(index)
        if (
                bell_index != -1 and self.settingsCategoriesList.currentRow() == 3
        ):  # only works on bell page
            self.bellSettingsList.setCurrentRow(bell_index)

    def set_password_visibility(self, checked):
        if checked:
            self.passwordInput.setEchoMode(QLineEdit.Normal)
        else:
            self.passwordInput.setEchoMode(QLineEdit.Password)

    # LOGIN SKYWARD

    def login_button(self):
        arguments = [self, self.usernameInput.text(), self.passwordInput.text()]
        self.passwordInput.clear()
        Thread(target=login.login, args=arguments, daemon=True).start()

    def refresh_button(self):
        arguments = [self, self.skywardUsername, self.skywardPassword]
        Thread(target=login.login, args=arguments, daemon=True).start()

    def load_creds(self):
        creds = login.get_login()
        if len(creds) > 0:
            args = [self, creds[0]['account'], creds[0]['password']]
            Thread(target=login.login, args=args, daemon=True).start()

    def clear_all_user_data(self):
        # log out
        # open("user/aes.bin", "wb").close()
        # open("user/encrypted.bin", "wb").close()
        delete_folder('data')
        delete_folder('user')
        login.clear_all_logins()
        self.loginLabel.setText('Not Logged In')
        self.skywardViewStackedWidget.setCurrentIndex(0)  # set to not logged in page
        self.classesFilter.hide()
        self.weeksFilter.hide()
        # self.skywardTable.clear()

    """
    NOTE SUMMARIZER
    """

    def summarize_notes(self):
        pass


def dark_title_bar(hwnd):
    """
    Set a custom color for the title bar
    Windows 11: Sets color RGB (28, 38, 48)
    Windows 10: Sets color to black
    """
    if not (
            UI.DARK_MODE
            and sys.platform == 'win32'
            and (version_num := sys.getwindowsversion()).major == 10
    ):
        return
    set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
    if version_num.build >= 22000:  # windows 11
        color = ct.c_int(0x30261C)  # GBR Hex
        set_window_attribute(hwnd, 35, ct.byref(color), ct.sizeof(color))
    else:
        rendering_policy = 19 if version_num.build < 19041 else 20  # 19 before 20h1
        value = ct.c_int(True)
        set_window_attribute(hwnd, rendering_policy, ct.byref(value), ct.sizeof(value))


def format_round(number, decimal_places):
    return float('{0:.{1}f}'.format(number, decimal_places))
