from PyQt5 import QtCore
from PyQt5.QtWidgets import QTreeWidgetItem


def calculate_grades(class_view_items):
    """
    Calculates the six weeks and semester averages
    """
    max_decimal_places = 2
    all_class_grades = {'1st': {}, '2nd': {}, '3rd': {}, '4th': {}, '5th': {}, '6th': {}}
    # Formatted as:  {6-week: {Weight: [100, 100, 75], Weight2: [100, 99]}}
    for item in class_view_items:
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
        class_grade.append(round(six_week_grade, max_decimal_places))
        # Calculate semester averages
        if len(class_grade) == 3:
            sem1_grade = sum(class_grade[:3]) / 3
            class_grade.append(round(sem1_grade, max_decimal_places))
        elif len(class_grade) == 7:
            sem2_grade = sum(class_grade[4:7]) / 3
            class_grade.append(round(sem2_grade, max_decimal_places))
        # Calculate final
    return class_grade


def create_assignment_item(weeks_filter):
    item = QTreeWidgetItem()
    item.setText(0, '-----')  # Name
    item.setText(1, '---')  # Grade
    item.setText(2, '---')  # Due date (not displayed)
    if weeks_filter != 'All':  # 6-week
        item.setText(3, weeks_filter)
    else:
        item.setText(3, '---')
    item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
    return item
