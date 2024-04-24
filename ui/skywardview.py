import os
from os.path import dirname, join
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QListWidgetItem
import json
from itertools import chain
from PyQt5.QtCore import Qt
from ReSkyward.ui import pointTableWidget as ptw
import re


class SkywardView():
    def __init__(self, app):
        self.app = app
        
        self.CITIZEN_COLUMNS = [1, 4, 7, 12, 15, 18]

        # Override the qfluent widgets default stylesheet
        app.skywardTable = ptw.PointTableWidget(3, 22)
        app.tableHLayout.addWidget(app.skywardTable)
        app.skywardTable.setStyleSheet('')
        app.skywardTable.setBorderVisible(True)
        app.classTable.setStyleSheet('')
        app.classBackButton.clicked.connect(self.backButtonClicked)
        
        self.app.classTable.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)
        
        # Data variables
        self.class_assignments = []
        self._class_ids = {}
        self.classViewItems = []
        
        app.skywardTable.currentCellChanged.connect(self.currentCellChanged)
        app.skywardTable.itemClicked.connect(self.preLoadAssignmentView)
        app.skywardTable.itemDoubleClicked.connect(self.openAssignmentView)
        
    def backButtonClicked(self):
        """
        Switches to table view upon clicking back button
        """
        self.app.skywardStack.setCurrentIndex(0)
        
    def openAssignmentView(self):
        """
        Switches to assignment view upon double clicking on a table item
        """
        
        
        if (len(self.classViewItems) > 0):
            self.app.skywardStack.setCurrentIndex(1)
            
    def preLoadAssignmentView(self):
        classes_item_index = self.app.skywardTable.currentRow()
        col_text = self.app.skywardTable.horizontalHeaderItem(self.app.skywardTable.currentColumn()).text()
        row_text = self.app.skywardTable.verticalHeaderItem(self.app.skywardTable.currentRow()).text()

        self.load_class_view(
                    self.class_assignments[classes_item_index],
                    col_text, #self.weeksFilter.currentItem().text()
                    row_text,
                )

        
    def currentCellChanged(self):
        col = self.app.skywardTable.currentColumn()
        row = self.app.skywardTable.currentRow()
        # self.app.skywardTable.item
        print("Column: " + str(col) + " Row: " + str(row))
    
   
    def load_skyward_view(self, reload=True):
        # TODO: fix this; kinda convoluted
        """
        Update the Skyward table UI with the data from the database
        """
        if reload and not self.load_skyward_data():
            return False  # if reload was requested, and failed, return
        # TODO: self.skywardViewStackedWidget.setCurrentIndex(2)  # set to skyward table
        # show filters
        # TODO: self.classesFilter.show()
        # TODO: self.weeksFilter.show()

        # load data to table
        # TODO: self.load_custom_classnames()  # load custom class names, set to self._class_ids
        # clear data
        self.app.skywardTable.clear()
        # TODO: self.classesFilter.clear()
        # add "All" to classes filter
        # TODO: self.classesFilter.addItem('All')
        # TODO: self.classesFilter.setCurrentRow(0)
        # set horizontal table headers (grading periods)
        for n, data in enumerate(self.headers):
            # add text to table header
            self.app.skywardTable.setHorizontalHeaderItem(
                n, self.create_table_item(data, n==(len(self.headers)-1) )
            )
            

        # set grades, class filter items, and vertical table headers (classes)
        for n, data in enumerate(self.skyward_data):
            # load items
            table_item, item = self.get_class_name_items(data, self._class_ids)
            # add item to table
            # TODO: self.classesFilter.addItem(item)
            if n >= self.app.skywardTable.rowCount():
                self.app.skywardTable.insertRow(self.app.skywardTable.rowCount())
            # add grades to table
            for m, grade in enumerate(data['grades']):
                self.app.skywardTable.setItem(n, m, self.create_table_item(grade, n==(len(self.skyward_data)-1) ))
            # set class name vertical header in table
            table_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.app.skywardTable.setVerticalHeaderItem(n, table_item)

        # TODO: self.filter_selected('')
  
        # self.app.skywardTable.setFixedSize(self.app.skywardTable.horizontalHeader().length(), self.app.skywardTable.verticalHeader().length())
        
        return True
    
    def load_skyward_data(self):
        """
        Loads the Skyward data from database
        """
        # Return error in status bar if no data already exists
        if not os.path.exists('data'):
            self.app.lastRefreshedLabel.setText('Please log into Skyward')
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
            self.app.lastRefreshedLabel.setText('Last refreshed: ' + json.load(f)['date'])
        return True  # return True if data was loaded successfully
    
    def create_table_item(self, data, is_last_item):
        """
        Returns a table item with the given data
        """
        
        if not is_last_item:
            table_item = QTableWidgetItem(data.get('text', ''))
        else:
            table_item = QTableWidgetItem(data.get('text', ''))
        
        if data.get('tooltip'):
            # set tooltip
            table_item.setToolTip(data['tooltip'])
        
        
        table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return table_item
    
    def get_class_name_items(self, data, class_ids):
        table_item = QTableWidgetItem()
        item = QListWidgetItem()
        if data['class_info']['id'] in class_ids:
            # if the class has a custom name saved, use it
            table_item.setText(class_ids[data['class_info']['id']])
            item.setText(class_ids[data['class_info']['id']])
        else:
            # otherwise, use the class name from Skyward
            table_item.setText(data['class_info']['class'])
            item.setText(data['class_info']['class'])
        # make item editable
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        return table_item, item
    
    # def filter_selected(self, filter_type):
        """
        Runs whenever a filter is clicked
        Changes skyward views
        """
        # Get indexes of selected filter item
        classes_item_index = self.get_selected_filter_index(self.classesFilter)
        # If they are both set to all then change to table view
        if classes_item_index == 0:
            self.app.skywardStack.setCurrentIndex(2)  # set to skyward table view
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

    def hide_skyward_table_columns(self, hide_citizen):
        """
        Hides/shows skyward table columns depending on filters and settings
        """
        # get weeks filter index
        # weeks_item_index = self.get_selected_filter_index(self.weeksFilter)
        
        for n, h in enumerate(self.headers):
            self.app.skywardTable.setColumnHidden(n, (hide_citizen and (n in self.CITIZEN_COLUMNS)))
            # if weeks_item_index != 0:
                
            #     # print(weeks_item_index, h['text'])
            #     self.skywardTable.setColumnHidden(
            #         n,
            #         (str(weeks_item_index) not in h['text'])
            #         or (self.hideCitizen and (n in self.citizenColumns)),
            #     )
            # else:
            #     self.skywardTable.setColumnHidden(
            #         n, self.hideCitizen and (n in self.citizenColumns)
            #     )

    def load_class_view(self, assignments, week_num: str, class_name: str):
        """
        Loads the class view for a class
        :param assignments: List of assignments in the selected class
        :param week_num: Current selected 6-weeks filter (text)
        """
        
        # self.app.classTable.clearContents()

        current_row = 0
        items = []
        self.classViewItems = []
        for assignment in assignments:
            # Only add assignment if in the correct 6-weeks
            # matching_weeks_filter = week_filter.lower() in [assignment['due'][1].strip('()').lower(), 'all']
            if 'col' in assignment and assignment['col'] == week_num:
                current_row += 1
                self.app.classTable.setRowCount(current_row)
                # print(assignment['name'])
                # Hide weeks column if not in all-weeks filter
                # self.hide_weeks_column(week_filter)
                
                # create class view item
                items = self.create_class_view_items(self.classViewItems, current_row-1, assignment, class_name)
                print(len(self.classViewItems))
                
                for i in range(0, len(items)):
                    self.classViewItems.append(items[i])
                    # if not self.app.classTable.item(current_row-1, i):
                    #     self.app.classTable.setItem(current_row-1, i, items[i]) # type: ignore
                    self.app.classTable.setItem(current_row-1, i, items[i]) # type: ignore
                    # self.classViewItems.append(items[i])
                    
                
                # self.classViewItems.append(item)
                # # Add assignment to tree
                # self.classViewTree.addTopLevelItem(item)
        self.app.classTable.setRowCount(current_row)
        
        
        # self.hide_weeks_column(week_filter)
        # self.classViewItems = hide_items_by_six_weeks(self.classViewItems, week_filter)
        
    def create_class_view_items(self, current_items, row, assignment, class_name:str):
        """
        Creates a class-view item
        :param assignment: Data containing assignment info
        :return: Item for class-view
        """
        # Get assignment data; only if it exists
        items = [QTableWidgetItem(), QTableWidgetItem(), QTableWidgetItem(), QTableWidgetItem(), QTableWidgetItem()]
        # for i in range(0, 6):
        #     if len(current_items) < (5*(row) + i+1):
        #         item = QTableWidgetItem()
        #         item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        #         items.append(item)
        #     else:
        #         print(5*(row) + i)
        #         items.append(current_items[5*(row) + i])

        
        # items[0].
        items[0].setText(class_name)
        
        if 'name' in assignment:
            # Set assignment name
            name = assignment['name']
            items[1].setText(name)
        if 'row' in assignment and 'grade' in assignment['row']:
            # Set grade
            grade = assignment['row']['grade']
            items[2].setText(grade)
        else:
            items[2].setText('---')

        # Set due date
        due_date = assignment['due'][0]
        items[3].setText(due_date)
        # Set 6 weeks
        week = assignment['col'][0] #.strip('()').lower()
        items[4].setText(week)
        
        return items

    def hide_weeks_column(self, week_filter):
        """
        Hides weeks column if not in all-weeks filter
        :param week_filter: The text of the selected six-weeks filter
        """
        if week_filter.lower() != 'all':
            self.classViewTree.header().hideSection(3)
        else:
            self.classViewTree.header().showSection(3)





def hide_items_by_six_weeks(items_list, week_filter_text):
    """
    Hides items in list based on six-weeks filter
    :param items_list: List containing items to hide
    :param week_filter_text: Current six-weeks filter text
    :return: Filtered items list
    """
    for item in items_list:
        item.setHidden(
            week_filter_text.lower() != 'all' and item.text(3) != week_filter_text.lower()
        )
    return items_list
