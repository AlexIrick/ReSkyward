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
import json
from threading import Thread
from itertools import chain
from Crypto.Cipher import AES
import skyward
import requests.exceptions
import darkdetect
import ctypes as ct
import shutil
import BellSchedule
import experimentmode
import skywardview
import speechrec
# from qt_material import list_themes, apply_stylesheet

# import qdarkstyle

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
    def __init__(self):
        super(UI, self).__init__()
        self.current_selected_school = None
        self.current_selected_district = None
        self.selected_school = None
        self.bell_schedule = None
        self.bell_group_id = None
        self.bell_groups = None
        self.bell_school_id = None
        self.bell_schools = None
        self.bell_districts = None
        self.sess = None
        self.bell_district_id = None
        self.bell_districts_dict = {}
        self.bell_schools_dict = {}
        self.bell_groups_dict = {}
        self.class_assignments = []
        self.assignment_files = None
        self.skyward_data = None
        uic.loadUi("MainWindow.ui", self)
        self.setWindowTitle(f'ReSkyward - {version}')
        self.setWindowIcon(QtGui.QIcon('img/logo-min.svg'))
        # set variables
        self.skywardUsername = ''
        self.skywardPassword = ''
        self._class_ids = {}
        self.rememberMe = True
        self.citizenColumns = [1, 4, 7, 12, 15, 18]
        self.experimentItems = []
        self.classViewItems = []

        self.notesSumText = ''

        # create config
        self.settings = {
            "skyward": {
                "hideCitizen": self.hideCitizenCheck.isChecked(),
            },
            "bellSchedule": {
                "districtID": None,
                "schoolID": None,
                "groupID": None,
            }
        }
        self.hideCitizen = False

        # set minimum width
        self.weeksFilter.setSpacing(5)
        self.weeksFilter.setFixedWidth(
            (self.weeksFilter.sizeHintForRow(0) + 13) * self.weeksFilter.count() + 2 * self.weeksFilter.frameWidth())
        self.weeksFilter.setFixedHeight(45)
        self.weeksFilterFrame.setBackgroundRole(QtGui.QPalette.Base)
        # set class tree view column sizes
        self.classViewTree.header().resizeSection(0, 250)
        self.classViewTree.header().resizeSection(1, 90)
        self.classViewTree.header().resizeSection(3, 90)

        self.experimentTree.header().resizeSection(1, 50)

        # set button connections; x = is checked when button is checkable
        self.dashboardButton.clicked.connect(lambda x: self.title_bar_button_clicked('dashboard', x))
        self.skywardButton.clicked.connect(lambda x: self.title_bar_button_clicked('skyward', x))
        self.gpaButton.clicked.connect(lambda x: self.title_bar_button_clicked('gpa', x))
        self.notesButton.clicked.connect(lambda x: self.title_bar_button_clicked('notes', x))
        self.settingsButton.clicked.connect(lambda: self.settings_clicked(-1))
        self.settingsLoginButton.clicked.connect(lambda: self.settings_clicked(0))
        self.settingsBellButton.clicked.connect(lambda: self.settings_clicked(4, 1))
        self.skywardLoginButton.clicked.connect(self.login_button_pressed)
        self.refreshButton.clicked.connect(self.refresh_database)
        self.clearUserDataButton.clicked.connect(self.clear_all_user_data)

        self.experimentButton.clicked.connect(self.experiment_toggle)
        self.experimentAddButton.clicked.connect(self.experiment_add)
        self.experimentRemoveButton.clicked.connect(self.experiment_remove)

        self.bellToggleButton.clicked.connect(self.bell_toggle)

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
        # hide bell
        self.bellStackedWidget.hide()

        self.bellRefreshTimer = QTimer()
        self.bellRefreshTimer.setInterval(1000)  # 1 seconds
        self.bellRefreshTimer.timeout.connect(self.refresh_bell_view)

        self.bellDistrictsList.currentRowChanged.connect(self.bell_schedule_changed)
        self.bellSettingsList.currentRowChanged.connect(self.bell_settings_selected)

        self.bellData = {}

        # set icons
        # self.bellToggleButton.setIcon(QtGui.QIcon('img/alarm.svg'))

        # set dark title bar
        # username = get_user_info()[0]
        self.loginLabel.setText(f'Logged in as {self.skywardUsername}')
        self.helloUserLabel.setText(f'Hello {self.skywardUsername}!')

        dark_title_bar(int(self.winId()))

        # Create user folder if needed
        if not os.path.exists('user'):
            os.mkdir('user')

        self.logged_in = self.load_skyward(True)
        self.load_config()
        splash.hide()
        self.show()

    database_refreshed = pyqtSignal()
    error_msg_signal = pyqtSignal(str)

    """
    ---Bell scraper---
    """
    def bell_set_enabled(self, should_enable):
        if should_enable:
            # Show bell container
            self.bellStackedWidget.show()
            self.bellToggleButton.setText('')
            self.bellToggleButton.setFont(QFont('Segoe MDL2 Assets', 14))
            Thread(
                target=self.get_bell_data,
                # args=None,
                daemon=True
            ).start()
            self.bellRefreshTimer.start()
            # self.get_bell_data()
        else:
            self.bellStackedWidget.hide()
            self.bellToggleButton.setText('🔔')
            self.bellToggleButton.setFont(QFont('Poppins', 13))
            self.bellRefreshTimer.stop()

    def bell_toggle(self):
        """
        Toggles bell schedule view
        """
        self.bell_set_enabled(self.bellStackedWidget.isHidden())

    def bell_refresh_start_thread(self):
        # print('timed out')
        Thread(
            target=self.refresh_bell_view,
            # args=None,
            daemon=True
        ).start()

    def bell_settings_selected(self, from_config=False):

        # Create session
        if not self.sess:
            self.sess = BellSchedule.create_session()

        # Get districts
        if not self.bell_districts:
            self.bell_districts = BellSchedule.get_districts(self.sess)
            # Add districts to list view in settings
            self.show_bell_districts(self.bell_districts)
        # Get district id
        if self.bellDistrictsList.currentRow() != -1 and not from_config:
            self.bell_district_id = self.bell_districts_dict[str(self.bellDistrictsList.currentItem())][0]

        if not self.bell_district_id:
            return
        selected_district = self.bell_districts[self.bell_district_id]

        # Get Schools
        if not self.bell_schools or \
                (self.current_selected_district is not None and self.current_selected_district != selected_district):
            self.current_selected_district = selected_district
            self.bell_schools = BellSchedule.get_schools(self.sess, selected_district)
            # Add schools to list view in settings
            self.show_bell_schools(self.bell_schools)
            if not from_config:
                self.bell_school_id = None
        # Get school id
        if self.bellSchoolsList.currentRow() != -1 and not from_config:
            self.bell_school_id = self.bell_schools_dict[str(self.bellSchoolsList.currentItem())][0]
        if not self.bell_school_id:
            return
        selected_school = self.bell_schools[self.bell_school_id]

        # Get groups
        if not self.bell_groups or \
                (self.current_selected_school is not None and self.current_selected_school != selected_school):
            self.current_selected_school = selected_school
            self.bell_groups, self.bell_schedule = BellSchedule.get_groups(self.sess, selected_school)
            # Add groups to list view in settings
            self.show_bell_groups(self.bell_groups)
            if not from_config:
                self.bell_group_id = None
        self.bell_set_enabled(False)

    def get_bell_data(self):
        """
        Gets bell schedule data
        """
        # Get selected group id
        if self.bellGroupsList.currentRow() != -1:
            self.bell_group_id = self.bell_groups_dict[str(self.bellGroupsList.currentItem())][0]
        if not self.bell_group_id:
            self.bellStackedWidget.setCurrentIndex(1)
            return
        else:
            self.bellStackedWidget.setCurrentIndex(2)
        selected_group = self.bell_groups[self.bell_group_id]

        rules = BellSchedule.get_rules(self.sess, selected_group, self.bell_schedule)
        result = BellSchedule.get_schedule(self.sess, self.current_selected_school, rules)

        self.bellCountdownGroup.setTitle(result[0]['selected_school'].name)
        self.bellData = result[0]
        if result[1] == "no school":
            self.bellData['is_school'] = False

        if 'today_schedule' in self.bellData and not self.bellData['today_schedule']:
            # If today's schedule is empty (holiday)
            self.bellData['is_school'] = False
        self.refresh_bell_view()

    def show_bell_districts(self, districts):
        for district in districts.items():
            item = QListWidgetItem()
            item.setText(district[1].name.strip())
            self.bell_districts_dict[str(item)] = district
            self.bellDistrictsList.addItem(item)

    def show_bell_schools(self, schools):
        self.bell_schools_dict.clear()
        self.bellSchoolsList.clear()
        # self.bellSchoolsList.setCurrentRow(-1)
        for school in schools.items():
            item = QListWidgetItem()
            item.setText(school[1].name)
            self.bell_schools_dict[str(item)] = school
            self.bellSchoolsList.addItem(item)

    def show_bell_groups(self, groups):
        self.bell_groups_dict.clear()
        self.bellGroupsList.clear()
        for group in groups.items():
            item = QListWidgetItem()
            item.setText(group[1].name)
            self.bell_groups_dict[str(item)] = group
            self.bellGroupsList.addItem(item)

    def bell_schedule_changed(self):
        Thread(
            target=self.get_bell_data,
            # args=None,
            daemon=True
        ).start()

    def refresh_bell_view(self):
        """
        Refreshes bell page but not if on settings page.
        Called by QTimer Event
        """
        if self.bellStackedWidget.currentIndex() == 1:
            return
        if display_data := BellSchedule.get_relevant_schedule_info(self.bellData):
            if 'selected_school' in self.bellData:
                self.bellCountdownGroup.setTitle(self.bellData['selected_school'].name)
            if 'today' in self.bellData:
                self.bellDayLabel.setText(self.bellData['today'].name)
            self.bellCurrentLabel.setText(display_data['current_period'])
            self.bellCountdownLabel.setText(display_data['time_left'])
            self.bellNextLabel.setText(display_data['next_period'])
            self.bellStackedWidget.setCurrentIndex(0)

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
            self.load_class_view(self.class_assignments[classes_item_index - 1], self.weeksFilter.currentItem().text(),
                                 True)

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
                self.load_class_view(self.class_assignments[classes_item_index - 1],
                                     self.weeksFilter.currentItem().text(), True)
            elif filter_type == 'week':
                # load the tree view
                self.load_class_view(self.class_assignments[classes_item_index - 1],
                                     self.weeksFilter.currentItem().text(), not self.classViewItems)

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
                self.skywardTable.setColumnHidden(n, (str(weeks_item_index) not in h['text'])
                                                  or (self.hideCitizen and (n in self.citizenColumns)))
            else:
                self.skywardTable.setColumnHidden(n, self.hideCitizen and (n in self.citizenColumns))

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
            return False
        # Load data from file
        with open('data/SkywardExport.json') as f:
            skyward_data = json.load(f)  # read data
        # Split headers to self.headers, and all class data to self.skyward_data (merges Ben Barber and Home Campus)
        self.headers = skyward_data[0][0]['headers'][1:]
        self.skyward_data = list(
            chain.from_iterable([x[1:] for x in skyward_data]))  # merge all classes together, skipping headers
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

        self.rememberMe = self.loginRememberCheck.isChecked()

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
            self.skywardTable.setHorizontalHeaderItem(n, skywardview.create_table_item(data, dark_mode))

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
                self.skywardTable.setItem(n, m, skywardview.create_table_item(data, dark_mode))
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
        if self.tabsStackedWidget.currentIndex() == _buttons['settings'][1] and button_ref != 'settings':
            self.save_settings()

        # Uncheck all buttons
        for b in _buttons.values():
            b[0].setChecked(False)

        # Check selected button
        _buttons[button_ref][0].setChecked(True)  # force the button to stay checked
        self.tabsStackedWidget.setCurrentIndex(_buttons[button_ref][1])

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
            self.title_bar_button_clicked('settings', False)
        except requests.exceptions.ConnectionError:
            self.error_msg_signal.emit('Network error. Please check your internet connection.')
        else:
            self.database_refreshed.emit()
            self.loginLabel.setText(f'Logged in as {username}')
            self.helloUserLabel.setText(f'Hello {username}!')

    """
    ---Settings---
    """
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
        if bell_index != -1 and self.settingsCategoriesList.currentRow() == 3:  # only works on bell page
            self.bellSettingsList.setCurrentRow(bell_index)

    def save_settings(self):
        # save to config
        self.hideCitizen = self.hideCitizenCheck.isChecked()
        if 'skyward' not in self.settings:
            self.settings["skyward"] = {}
        self.settings["skyward"]["hideCitizen"] = self.hideCitizen
        # if self.settingsCategoriesList.currentRow() == 3:  # only works on bell page

        self.bell_settings_selected()
        self.get_bell_data()
        if 'bellSchedule' not in self.settings:
            self.settings["bellSchedule"] = {}
        self.settings["bellSchedule"]["districtID"] = self.bell_district_id
        self.settings["bellSchedule"]["schoolID"] = self.bell_school_id
        self.settings["bellSchedule"]["groupID"] = self.bell_group_id

        with open('user/config.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        # load objects
        self.load_config_objects()

    def login_button_pressed(self):
        """
        Called when the save button is clicked
        Check if the username and password fields are empty
        """
        if self.usernameInput.text() and self.passwordInput.text():
            self.skywardUsername = self.usernameInput.text()
            self.skywardPassword = self.passwordInput.text()
            self.usernameInput.clear()
            self.passwordInput.clear()

            # TODO: ONLY SAVE LOGIN IF REFRESH IS SUCCESSFUL
            # refreshes database
            self.refresh_database()

            self.save_login()


        elif self.usernameInput.text() or self.passwordInput.text():
            self.message_box('ReSkyward - Input Error', 'Please enter both a username and password.')

    def load_config(self):
        """
        Loads saved settings/config
        """
        if os.path.exists('user/config.json'):
            with open('user/config.json', 'r') as f:
                self.settings = json.load(f)
            if "skyward" in self.settings:
                if 'hideCitizen' in self.settings["skyward"]:
                    self.hideCitizen = self.settings["skyward"]["hideCitizen"]

            if "bellSchedule" in self.settings:
                if 'districtID' in self.settings["bellSchedule"]:
                    self.bell_district_id = self.settings["bellSchedule"]["districtID"]
                if 'schoolID' in self.settings["bellSchedule"]:
                    self.bell_school_id = self.settings["bellSchedule"]["schoolID"]
                if 'groupID' in self.settings["bellSchedule"]:
                    self.bell_group_id = self.settings["bellSchedule"]["groupID"]
            self.load_config_objects()
            self.save_settings()

    def load_config_objects(self):
        """
        Loads items/objects related to settings
        """
        if self.logged_in:
            self.hideCitizenCheck.setChecked(self.hideCitizen)
            self.hide_skyward_table_columns()

        # self.sess = BellSchedule.create_session()
        # selected_school = self.bell_schools[self.bell_school_id]
        # self.bell_groups, self.bell_schedule = BellSchedule.get_groups(self.sess, selected_school)

        self.bell_settings_selected(True)
        self.get_bell_data()

    def save_login(self):
        """
        Saves the username and password as encrypted binary
        """

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


    def refresh_database(self):
        """
        Get password and decrypt
        """
        if self.loginRememberCheck.isChecked():
            data = get_user_info()
            if data:
                # set text for refresh label
                self.lastRefreshedLabel.setText('Refreshing...')
                # run scraper as thread: inputs user login
                Thread(
                    target=self.run_scraper,
                    args=data,
                    daemon=True
                ).start()
            else:
                self.settings_clicked(0)
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
    if not (dark_mode and sys.platform == 'win32' and (version_num := sys.getwindowsversion()).major == 10):
        return
    set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
    if version_num.build >= 22000:  # windows 11
        color = ct.c_int(0x30261C)  # GBR Hex
        set_window_attribute(hwnd, 35, ct.byref(color), ct.sizeof(color))
    else:
        rendering_policy = 19 if version_num.build < 19041 else 20  # 19 before 20h1
        value = ct.c_int(True)
        set_window_attribute(hwnd, rendering_policy, ct.byref(value), ct.sizeof(value))


def delete_folder(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)


def format_round(number, decimal_places):
    return float('{0:.{1}f}'.format(number, decimal_places))


def get_user_info():
    # reads key from file
    if os.path.exists('user/aes.bin'):
        with open("user/aes.bin", "rb") as file_in:
            key = file_in.read()
    else:
        return False

    if os.path.exists('user/encrypted.bin'):
        # reads encrypted user info from file
        with open("user/encrypted.bin", "rb") as file_in:
            nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
    else:
        return False


    # generate cypher from key
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    # decrypts user login
    return json.loads(cipher.decrypt_and_verify(ciphertext, tag).decode())


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

    window = UI()
    app.exec_()

    # runs after program is closed
    # deletes user data if remember me was not toggled on login
    if not window.rememberMe:
        delete_folder('data')
