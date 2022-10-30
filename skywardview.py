from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QTreeWidgetItem


def create_class_view_item(assignment):
    """
    Creates a class-view item
    :param assignment: Data containing assignment info
    :return: Item for class-view
    """
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
    return item


def create_table_item(data, dark_mode):
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


def load_table_item(data, class_ids):
    table_item = QtWidgets.QTableWidgetItem()
    item = QtWidgets.QListWidgetItem()
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


def hide_items_by_six_weeks(items_list, week_filter_text):
    """
    Hides items in list based on six-weeks filter
    :param items_list: List containing items to hide
    :param week_filter_text: Current six-weeks filter text
    :return: Filtered items list
    """
    for item in items_list:
        item.setHidden(week_filter_text.lower() != 'all' and item.text(3) != week_filter_text.lower())
    return items_list
