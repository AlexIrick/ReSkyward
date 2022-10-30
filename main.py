from dateutil import parser
import re
from datetime import datetime, date
from Crypto.Random import get_random_bytes
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QTreeWidgetItem
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
        self.citizenColumns = [1, 4, 7]
        self.experimentItems = []
        self.classViewItems = []

        # create config
        self.settings = {
            "skyward": {
                "hideCitizen": self.hideCitizenCheck.isChecked(),
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
        self.classViewTree.header().resizeSection(0, 290)
        self.classViewTree.header().resizeSection(1, 90)
        self.classViewTree.header().resizeSection(3, 90)

        # set button connections; x = is checked when button is checkable
        self.dashboardButton.clicked.connect(lambda x: self.title_bar_button_clicked(0, x))
        self.skywardButton.clicked.connect(lambda x: self.title_bar_button_clicked(1, x))
        self.gpaButton.clicked.connect(lambda x: self.title_bar_button_clicked(2, x))
        self.settingsButton.clicked.connect(lambda x: self.title_bar_button_clicked(3, x))
        self.saveButton.clicked.connect(self.save_settings)
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
        class_view_delegate.editFinished.connect(self.class_tree_edited)
        self.classViewTree.setItemDelegate(class_view_delegate)

        # hide filters
        self.classesFilter.hide()
        self.weeksFilter.hide()
        # hide experiment
        self.experimentGroup.hide()
        # hide bell
        self.bellStackedWidget.hide()

        self.bellRefreshTimer = QTimer()
        self.bellRefreshTimer.setInterval(500)  # .5 seconds
        self.bellRefreshTimer.timeout.connect(self.refresh_bell_view)

        self.bellData = {}

        # set icons
        # self.bellToggleButton.setIcon(QtGui.QIcon('img/alarm.svg'))

        # set dark title bar
        self.loginLabel.setText(f'Logged in as {get_user_info()[0]}')

        dark_title_bar(int(self.winId()))
        self.load_skyward()
        self.load_config()
        splash.hide()
        self.show()

    database_refreshed = pyqtSignal()
    error_msg_signal = pyqtSignal(str)

    """
    Bell scraper
    """

    def bell_toggle(self):
        """
        Toggles bell schedule view
        """
        if self.bellStackedWidget.isHidden():
            # Show bell container
            self.bellStackedWidget.show()
            self.bellToggleButton.setText('')
            self.bellToggleButton.setFont(QFont('Segoe UI', 14))
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

    def bell_refresh_start_thread(self):
        print('timed out')
        Thread(
            target=self.refresh_bell_view,
            # args=None,
            daemon=True
        ).start()

    def get_bell_data(self):
        """--- Gathering information ---"""
        sess = BellSchedule.createSession()
        # Get district
        districts = BellSchedule.BellPopularDistricts(sess).get()
        selected_district = districts[4]
        # Get school
        schools = BellSchedule.BellSchoolsPerDistrict(sess).get(district=selected_district)
        selected_school = schools[4]
        self.bellData['selected_school'] = selected_school

        # Get schedule names per school
        schedule = BellSchedule.BellSchedulePerSchool(sess).get(school=selected_school)
        schedule[0] = BellSchedule.BellSchedule({'id': 0, 'name': 'No School'})
        # Get groups (grade levels) per school
        groups = BellSchedule.BellGroupsPerSchool(sess).get(school=selected_school)
        selected_group = groups[13]
        # Get rules (a/b days) per group
        rules = BellSchedule.BellRulesPerGroup(sess).get(group=selected_group, schedule=schedule)

        self.bellCountdownGroup.setTitle(selected_school.name)

        """--- Show information for today ---"""
        day = str(date.today())
        # day = "2022-11-11"

        days = sorted(rules.items())  # Listed days

        for listed_day, bell_day in days:
            # If the day is after today and has a schedule
            if listed_day > day and bell_day.schedule:
                self.bellData['next_school_day'] = rules[listed_day]
                break

        try:
            today = rules[day]  # Get today's rule, given the date as YYYY-MM-DD
        except KeyError:
            # No school today; print the next day of school and exit
            self.refresh_bell_view(False)
            return

        self.bellData['today'] = today  # Set today's name (A or B day)

        # Get today's schedule
        today_schedule = BellSchedule.BellDayPerSchedule(sess).get(today.schedule)
        self.bellData['today_schedule'] = today_schedule

    def refresh_bell_view(self, is_school=True):
        if not is_school or ('today_schedule' in self.bellData and not self.bellData['today_schedule']):
            next_day = self.bellData['next_school_day']
            # If there is no school then update labels accordingly
            self.bellDayLabel.setText('No schedule today!')  # No school today

            # Show next school day
            next_day_date = parser.parse(next_day.date)
            num_suffix = lambda n: ("th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}).get(n % 10, "th")
            next_day_date = next_day_date.strftime('%A, %b, %#d') + num_suffix(next_day_date.day)

            self.bellCurrentLabel.setText("It looks like there is no schedule today. Enjoy the day off!")
            self.bellCountdownLabel.setText("")
            self.bellNextLabel.setText(f'The next school day is \"{next_day.name}\", on {next_day_date}.')
            return

        if len(self.bellData) < 4:
            return

        now = datetime.now()
        today_schedule = self.bellData['today_schedule']
        today = self.bellData['today']
        selected_school = self.bellData['selected_school']
        for id, period in today_schedule.items():
            if period.time > now:  # Find current class. Time can be compared as datetime objects
                # print('Current class:', period.names, '\t\t')
                period_name = "Current: " + " / ".join(period.names)
                # print('Time left:', period.time - now, '\t\t')
                time_left = str(period.time - now)
                time_left = re.search(r'(^[0:]+)?(.*)\.', time_left)[2]  # removes microseconds and leading 0 from hours

                try:
                    next_period = "Next: " + " / ".join(today_schedule[id + 1].names)
                except KeyError:
                    next_period = 'Last class of the day!'

                break
        else:
            time_left = ""
            period_name = "After school hours"

            # date_time_str = '10/30/22 07:00:00'
            # tomorrow = datetime.strptime(date_time_str, '%m/%d/%y %H:%M:%S')
            # time_left = str(tomorrow - now)
            # time_left = re.search(r'(^[0:]+)?(.*)\.', time_left)[2]  # removes microseconds and leading 0 from hours
            next_day = self.bellData['next_school_day']
            next_period = f"No more classes today!\nThe next school day is \"{next_day.name}\""

        self.bellCountdownGroup.setTitle(selected_school.name)
        self.bellDayLabel.setText(today.name)
        self.bellCurrentLabel.setText(period_name)
        self.bellCountdownLabel.setText(time_left)
        self.bellNextLabel.setText(next_period)

    """
    Experiment
    """

    def experiment_toggle(self):
        """
        Toggles experiment mode
        """
        if self.experimentGroup.isHidden():
            # Enable experiment
            self.experimentGroup.show()
            self.experimentButton.setText('')
            self.experimentButton.setFont(QFont('Segoe UI', 14))
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
        max_decimal_places = 2
        all_class_grades = {'1st': {}, '2nd': {}, '3rd': {}, '4th': {}, '5th': {}, '6th': {}}
        # Formatted as:  {6-week: {Weight: [100, 100, 75], Weight2: [100, 99]}}
        for item in self.classViewItems:
            if item.text(3) in all_class_grades:
                six_week = item.text(3)
                weight = 1
                grade = item.text(1)
                # Pass/fail handling
                if grade == 'P':
                    grade = '100'
                elif grade == 'F':
                    grade = '0'
                # Make sure grade is numeric
                if grade.isnumeric():
                    grade = float(grade)
                    if weight in all_class_grades[six_week]:
                        all_class_grades[six_week][weight].append(grade)
                    else:
                        all_class_grades[six_week][weight] = [grade]

        # Six weeks
        class_grade = []
        for six_week, value in all_class_grades.items():
            # Calculate six week averages
            six_week_grade = 0
            for weight in value.keys():
                total = sum(all_class_grades[six_week][weight])
                six_week_grade += total / len(all_class_grades[six_week][weight]) * weight
            class_grade.append(format_round(six_week_grade, max_decimal_places))
            # Calculate semester averages
            if len(class_grade) == 3:
                sem1_grade = sum(class_grade[:3]) / 3
                class_grade.append(format_round(sem1_grade, max_decimal_places))
            elif len(class_grade) == 7:
                sem2_grade = sum(class_grade[4:7]) / 3
                class_grade.append(format_round(sem2_grade, max_decimal_places))
            # Calculate final
        return class_grade

    def experiment_add(self):
        """
        Called when the user presses the add button in the experiment mode
        Adds an item to the class view tree
        """
        item = QTreeWidgetItem()
        item.setText(0, '-----')  # Name
        item.setText(1, '---')  # Grade
        item.setText(2, '---')  # Due date (not displayed)
        weeks_filter = self.weeksFilter.currentItem().text()
        if weeks_filter != 'All':  # 6-week
            item.setText(3, weeks_filter)
        else:
            item.setText(3, '---')
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
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

    def class_tree_edited(self):
        # text = self.classViewTree.item(model_index).text()
        self.display_experiment_grades()

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
                self.skywardTable.setColumnHidden(n, str(weeks_item_index) not in h['text']
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
                    # Get assignment data; only if it exists
                    item = QTreeWidgetItem()
                    if 'name' in assignment:
                        # Set assignment name
                        name = assignment['name']
                        item.setText(0, name)
                    if 'row' in assignment and 'grade' in assignment['row']:
                        # Set grade
                        grade = assignment['row']['grade']
                        item.setText(1, grade)
                    else:
                        item.setText(1, '---')

                    # Set due date
                    due_date = assignment['due'][0]
                    item.setText(2, due_date)
                    # Set 6 weeks
                    week = assignment['due'][1].strip('()').lower()
                    item.setText(3, week)

                    self.classViewItems.append(item)
                    # Add assignment to tree
                    self.classViewTree.addTopLevelItem(item)
        else:
            # Hide weeks column if not in all-weeks filter
            self.hide_weeks_column(week_filter)
        for item in self.classViewItems:
            item.setHidden(week_filter.lower() != 'all' and item.text(3) != week_filter.lower())

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
            return
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
                self.class_assignments.append(json.load(f))
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

    def save_settings(self):
        """
        Called when the save button is clicked
        Check if the username and password fields are empty
        """
        # Create user folder if needed
        if not os.path.exists('user'):
            os.mkdir('user')
        if self.usernameInput.text() and self.passwordInput.text():
            self.login()
        elif self.usernameInput.text() or self.passwordInput.text():
            self.message_box('ReSkyward - Input Error', 'Please enter both a username and password.')

        # save to config
        self.hideCitizen = self.hideCitizenCheck.isChecked()
        self.settings["skyward"]["hideCitizen"] = self.hideCitizen
        with open('user/config.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        # load objects
        self.load_config_objects()

    def load_config(self):
        """
        Loads saved settings/config
        """
        if os.path.exists('user/config.json'):
            with open('user/config.json', 'r') as f:
                self.settings = json.load(f)
            self.hideCitizen = self.settings["skyward"]["hideCitizen"]
            self.hideCitizenCheck.setChecked(self.hideCitizen)
            self.load_config_objects()

    def load_config_objects(self):
        """
        Loads items/objects related to settings
        """
        self.hide_skyward_table_columns()

    def login(self, should_refresh=True):
        """
        Saves the username and password as encrypted binary
        """
        print('saving')
        self.skywardUsername = self.usernameInput.text()
        self.skywardPassword = self.passwordInput.text()

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
            data = get_user_info()
            # set text for refresh label
            self.lastRefreshedLabel.setText('Refreshing...')
            # run scraper as thread: inputs user login
            Thread(
                target=self.run_scraper,
                args=data,
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
        self.skywardViewStackedWidget.setCurrentIndex(0)  # set to not logged in page
        self.classesFilter.hide()
        self.weeksFilter.hide()
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
    with open("user/aes.bin", "rb") as file_in:
        key = file_in.read()
    # reads encrypted user info from file
    with open("user/encrypted.bin", "rb") as file_in:
        nonce, tag, ciphertext = [file_in.read(x) for x in (16, 16, -1)]
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

    # dark mode pallette
    if dark_mode := darkdetect.isDark():
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

    default_settings = {
        "hideCitizen": True,
    }

    # Create window
    MainWindow = QtWidgets.QMainWindow()

    window = UI()
    app.exec_()

    # runs after program is closed
    # deletes user data if remember me was not toggled on login
    if not window.rememberMe:
        delete_folder('data')
