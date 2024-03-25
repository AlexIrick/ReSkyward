from threading import Thread

from PyQt5.QtCore import Qt, QTimer, QEvent, QObject, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QListWidgetItem, QCompleter
from qfluentwidgets import FlowLayout, SearchLineEdit
from qfluentwidgets import FluentIcon as FIF


from ReSkyward.scr import BellSchedule


class CustomEventFilter(QObject):
    focusIn = pyqtSignal()
    def eventFilter(self, object, event):
        if event.type() == QEvent.FocusIn:
            # bring up your custom edit
            # print("focus in")
            self.focusIn.emit()
            return True  # Event is handled
        return False  # Event is not handled, continue normal processing


class BellUI:
    def __init__(self, app):
        self.app = app
        
        # Set up ui
        # app.flow = FlowLayout(app.bellSelectWidget, False)
        # app.flow.addWidget(app.districtWidget)
        # app.flow.addWidget(app.schoolWidget)
        # app.flow.addWidget(app.groupWidget)
        # app.flow.setContentsMargins(0, 0, 0, 0)
        
        # self.set_search_edit(app.schoolSearch)
        # self.set_search_edit(app.groupSearch)
        
        # app.bellSelectPage.setStretch(1)
        

        self.bell_ids = [None, None, None]  # district, school, group
        self.bell_schedule = None

        # Matches ids to BellSchedule scraper info objects
        self.districts_scraper_dict = None
        self.schools_scraper_dict = None
        self.groups_scraper_dict = None
        # self.selected_scraper_objs = [None, None, None]

        # Matches list items to ids
        self.district_items_dict = {}
        self.school_items_dict = {}
        self.group_items_dict = {}

        self.bellData = {}
        
        self.app.bellRefreshTimer = QTimer()
        app.bellRefreshTimer.setInterval(1000)  # 1 seconds
        app.bellRefreshTimer.timeout.connect(self.refresh_view)
        
        app.stack_switched.connect(self.tab_switched)
        
        # District
        app.district_loaded.connect(self.show_bell_districts)
        app.districtNextBtn.clicked.connect(self.district_changed)
        app.districtNextBtn.setIcon(FIF.CHEVRON_RIGHT)
        
        self.filter = CustomEventFilter()
        app.districtSearch.installEventFilter(self.filter)
        # app.districtSearch.textEdited.connect(self.search_text_changed)
        self.filter.focusIn.connect(self.focus_in)
        
        # School
        app.school_loaded.connect(self.show_bell_schools)
        app.schoolNextBtn.clicked.connect(self.school_changed)
        app.schoolNextBtn.setIcon(FIF.CHEVRON_RIGHT)
        
        # Group
        app.group_loaded.connect(self.show_bell_groups)
        app.groupNextBtn.clicked.connect(self.group_changed)
        app.groupNextBtn.setIcon(FIF.CHEVRON_RIGHT)
        
        self.app.schedule_loaded.connect(self.start_bell_timer)

        self.set_stack_view_index(0)
        
        # Start session
        self.sess = BellSchedule.create_session()
        # # Scrape districts
        Thread(target=self.scrape_districts, daemon=True).start()
        
    def focus_in(self):
        #TODO:
        # self.app.districtSearch.setText(" ")
        # self.app.districtSearch._showCompleterMenu()
        # self.app.districtSearch.setText("")
        pass
        
        # if self.app.districtSearch._completerMenu:
        #     self.app.districtSearch._completerMenu.popup()
        # print("text changed")    
    
    
    def tab_switched(self, widget):
        '''
        called when app.stack_switched PyQtSignal is emitted()
        '''
        self.bell_set_enabled(widget==self.app.bellPage)
 
 
    def start_bell_timer(self):
        self.refresh_view()
        self.app.bellRefreshTimer.start()
        
    def set_search_edit(self, search_edit, items):
        self.completer = QCompleter(items, search_edit)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setMaxVisibleItems(7)
        self.completer.setCompletionMode(QCompleter.CompletionMode(0)) # 0-PopupCompletion: only shows search results;
                                                                    #  1-UnfilteredPopupCompletion, shows everything
        search_edit.setCompleter(self.completer)
        # search_edit.setClearButtonEnabled(True)
        # search_edit.setPlaceholderText('Search item')
        

    def set_bell_ids(self, bell_ids):
        """
        Called by config.py on load config
        """
        self.bell_ids = bell_ids

        Thread(
            target=self.config_loading,
            daemon=True,
        ).start()

    def config_loading(self):
        """
        Scrapes districts, schools, and groups
        Called by set_bell_ids called by config.py
        Includes error handling if id is invalid; sets invalid id to None
        """

        self.scrape_districts()

        # scrape Schools if has district id AND district id is found in district scraper object dictionary
        if self.bell_ids[0] is not None and self.bell_ids[0] in self.districts_scraper_dict:
            self.scrape_schools()
            self.app.bellDistrictsList.setCurrentRow(self.get_list_current_row(0))
        else:
            self.bell_ids[0] = None

        # scrape Groups if has district and school id AND school id is found in school scraper object dictionary
        if (
            self.bell_ids[0] is not None
            and self.bell_ids[1] is not None
            and self.bell_ids[1] in self.schools_scraper_dict
        ):
            self.scrape_groups()
            self.app.bellSchoolsList.setCurrentRow(self.get_list_current_row(1))
        else:
            self.bell_ids[1] = None

        # if bell_ids has None in it OR if group id is NOT found in groups scraper object dictionary
        if None not in self.bell_ids and self.bell_ids[2] in self.groups_scraper_dict:
            self.app.bellGroupsList.setCurrentRow(
                self.get_list_current_row(2)
            )  # TODO: (BUG) Not updating current row, returns correct index
        else:
            # reset group id
            self.bell_ids[2] = None

        # Update config
        self.app.config.set_bell_schedule_ids(self.bell_ids)

    def get_list_current_row(self, level_index: int):
        """
        Determines what row a list item is on using an id and 'level_index'
        :param level_index: 0=district level, 1=school level, 2=group level
        Called by config_loading
        """

        sections = [self.district_items_dict, self.school_items_dict, self.group_items_dict]
        i = -1
        for l_id in list(sections[level_index].values()):
            i += 1
            if l_id == self.bell_ids[level_index]:
                return i
        return -1

    def bell_toggle(self):
        """
        Toggles bell schedule view
        """
        self.bell_set_enabled(self.app.bellStackedWidget.isHidden())

    def bell_set_enabled(self, should_enable):
        """
        Updates the UI and populates with data. Starts thread self.get_bell_data if enabled
        """
        if should_enable:
            # Show bell container
            # self.app.bellStackedWidget.show()
            # self.app.bellToggleButton.setText('')
            # self.app.bellToggleButton.setFont(QFont('Segoe MDL2 Assets', 14))
            
            if None in self.bell_ids:
                # If an id is missing, set bell tab view to 'No Schedule Set' Page
                self.set_stack_view_index(0)
                return
            else:
                # Set bell tab view to 'Loading' Page
                self.set_stack_view_index(2)
            
            Thread(
                target=self.get_bell_data,
                daemon=True,
            ).start()
            # self.app.bellRefreshTimer.start()
            # self.get_bell_data()
        else:
            self.app.bellRefreshTimer.stop()
            # self.app.bellStackedWidget.hide()
            # self.app.bellToggleButton.setText('🔔')
            # self.app.bellToggleButton.setFont(QFont('Poppins', 13))

    def refresh_view(self):
        """
        Refreshes bell page but not if on settings page.
        Called by QTimer Event
        """
        # if self.app.bellStackedWidget.currentIndex() == 1:
        #     return
        
        if display_data := BellSchedule.get_relevant_schedule_info(self.bellData):
            if 'selected_school' in self.bellData:
                self.app.bellSchoolLabel.setText(self.bellData['selected_school'].name)
            if 'today' in self.bellData:
                self.app.bellDayLabel.setText(self.bellData['today'].name)
            self.app.bellCurrentLabel.setText(display_data['current_period'])
            self.app.bellCountdownLabel.setText(display_data['time_left'])
            self.app.bellNextLabel.setText(display_data['next_period'])
            self.app.bellThenLabel.setText(display_data['then_period'])
            self.set_stack_view_index(1)
        

    def scrape_districts(self):
        self.districts_scraper_dict = BellSchedule.get_districts(self.sess)
        self.app.district_loaded.emit()

    def district_changed(self):
        """
        When current item in the district list is changed, update the id and populate districts list.
        Also called by list.setCurrentRow()
        """
        if not self.app.districtSearch.text() in self.districts_scraper_dict:
            return
        d_id = self.districts_scraper_dict[self.app.districtSearch.text()].id
        
        if self.bell_ids[0] != d_id:
            self.bell_ids[0] = d_id
            # Clear school and group ids
            self.bell_ids[1] = None
            self.bell_ids[2] = None
            self.app.schoolWidget.setEnabled(False)
            self.app.groupWidget.setEnabled(False)
            
        # Scrape schools
        Thread(
            target=self.scrape_schools,
            daemon=True,
        ).start()

    def scrape_schools(self):
        self.schools_scraper_dict = BellSchedule.get_schools(
            self.sess, self.get_district_scraper_obj()
        )
        
        self.app.school_loaded.emit()

        # Populate scraped schools into school list view
        # self.show_bell_schools()

    def get_district_scraper_obj(self):
        """Returns the bell scraper object of the currently selected district"""
        return self.districts_scraper_dict[self.app.districtSearch.text()]

    def school_changed(self):
        """
        When current item in the school list is changed, update the id and populate groups list
        Also called by list.setCurrentRow()
        """
        
        if self.app.schoolSearch.text() in self.schools_scraper_dict:
            s_id = self.schools_scraper_dict[self.app.schoolSearch.text()].id
        else:
            return
        # this if condition is to prevent clearing other bell level ids when loading config because of setCurrentRow()
        if self.bell_ids[1] != s_id:
            self.bell_ids[1] = s_id
            # Clear group ids
            self.bell_ids[2] = None
            self.app.groupWidget.setEnabled(False)

        # Scrape schools
        Thread(
            target=self.scrape_groups,
            daemon=True,
        ).start()

        # self.row_changed_finish()

    def scrape_groups(self):
        # Scrape schools
        self.groups_scraper_dict, self.bell_schedule = BellSchedule.get_groups(
            self.sess, self.get_school_scraper_obj()
        )
        self.app.group_loaded.emit()
        # Populate scraped groups into group list view
        

    def get_school_scraper_obj(self):
        """Returns the bell scraper object of the currently selected school"""
        return self.schools_scraper_dict[self.app.schoolSearch.text()]
        # return self.schools_scraper_dict[self.bell_ids[1]]

    def group_changed(self):
        """
        When current item in the groups list is changed, update the id
        Also called by list.setCurrentRow()
        """
        
        if self.app.groupSearch.text() in self.groups_scraper_dict:
            g_id = self.groups_scraper_dict[self.app.groupSearch.text()].id
        else:
            return
        # this if condition is to prevent clearing other bell level ids when loading config because of setCurrentRow()
        if self.bell_ids[2] != g_id:
            self.bell_ids[2] = g_id

        self.bell_set_enabled(True)

    def get_group_scraper_obj(self):
        """Returns the bell scraper object of the currently selected group"""
        return self.groups_scraper_dict[self.app.groupSearch.text()]

        # return self.groups_scraper_dict[self.bell_ids[2]]


    def get_bell_data(self):
        """
        Gets bell rules/schedule
        """

        # Scrape rules and schedule
        rules = BellSchedule.get_rules(self.sess, self.get_group_scraper_obj(), self.bell_schedule)
        result = BellSchedule.get_schedule(self.sess, self.get_school_scraper_obj(), rules)

        # Set Bell Tab school name
        # self.app.bellCountdownGroup.setTitle(result[0]['selected_school'].name)

        # Set bell data
        self.bellData = result[0]

        # Update bell data if no school
        if result[1] == "no school":
            self.bellData['is_school'] = False

        # Update bell data if no schedule for today
        if 'today_schedule' in self.bellData and not self.bellData['today_schedule']:
            # If today's schedule is empty (holiday)
            self.bellData['is_school'] = False

        self.app.schedule_loaded.emit()
        


    def show_bell_districts(self):
        # print(districts)
        if self.districts_scraper_dict is None:
            print("districts is None")
            return
        
        district_names = [x.name for x in self.districts_scraper_dict.values()]
        # print(district_names)

        self.set_search_edit(self.app.districtSearch, district_names)

    def show_bell_schools(self):
        if self.schools_scraper_dict is None:
            print("schools is None")
            return
        
        # self.school_items_dict.clear()
        
        school_names = [x.name for x in self.schools_scraper_dict.values()]
        # print(district_names)

        self.set_search_edit(self.app.schoolSearch, school_names)
        
        # self.app.bellSchoolsList.clear()
        # for school in self.schools_scraper_dict.items():
        #     item = QListWidgetItem()
        #     item.setText(school[1].name)
        #     self.school_items_dict[str(item)] = school[0]
        #     self.app.bellSchoolsList.addItem(item)
        
        self.app.schoolWidget.setEnabled(True)

    def show_bell_groups(self):
        if self.groups_scraper_dict is None:
            print("groups is None")
            return
        
        # self.school_items_dict.clear()
        
        group_names = [x.name for x in self.groups_scraper_dict.values()]
        # print(district_names)

        self.set_search_edit(self.app.groupSearch, group_names)
        
        self.app.groupWidget.setEnabled(True)
        
        # self.group_items_dict.clear()
        # self.app.bellGroupsList.clear()
        # for group in groups.items():
        #     item = QListWidgetItem()
        #     item.setText(group[1].name)
        #     self.group_items_dict[str(item)] = group[0]
        #     self.app.bellGroupsList.addItem(item)

    def reset_connection(self):
        self.bell_ids = [None, None, None]  # district, school, group

        self.bell_schedule = None

        # Matches ids to BellSchedule scraper info objects
        # self.districts_scraper_dict = None
        self.schools_scraper_dict = None
        self.groups_scraper_dict = None
        # self.selected_scraper_objs = [None, None, None]

        # Matches list items to ids
        # self.district_items_dict = {}
        self.school_items_dict = {}
        self.group_items_dict = {}

        self.bellData = {}
        
        self.app.districtSearch.clear()
        self.app.schoolSearch.clear()
        self.app.schoolWidget.setEnabled(False)
        self.app.groupSearch.clear()
        self.app.groupWidget.setEnabled(False)
        
        self.app.bellRefreshTimer.stop()
        self.set_stack_view_index(0)
        
    def set_stack_view_index(self, i):
        """ Sets the current index of bell stack

        Args:
            i (int): 0='No Schedule Set' Page; 1='View' Page 2='Loading' Page
        """        
        
        self.app.bellStack.setCurrentIndex(i)