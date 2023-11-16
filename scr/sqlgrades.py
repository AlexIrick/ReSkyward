import sqlite3


class GradesDatabase:
    def __init__(self, db_path):
        self.connection = None
        self.cursor = None
        self.open(db_path)

    def open(self, db_path):
        """
        Opens connection and cursor to database
        :param db_path: Path to database
        """
        # connect to database from file
        self.connection = sqlite3.connect(db_path)
        # create cursor
        self.cursor = self.connection.cursor()

    def close(self):
        """
        Closes connection to database
        """
        self.connection.close()

    def create_class_table(self, table_name):
        """
        Creates a table if it doesn't already exist. Must be committed with commit function
        :param table_name:
        """
        self.cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name}(name, due, col, grade, is_highlighted)"
        )

    def insert_list_into_table(self, table_name, data):
        """
        Inserts data as list into table. Must be committed with commit function
        :param table_name: Name of existing table
        :param data: List containing data to insert into table
        """
        self.cursor.executemany(f"INSERT INTO  {table_name} VALUES(?, ?, ?, ?, ?)", data)

    def commit(self):
        """
        Commits any changes to db
        """
        self.connection.commit()

    def get_cursor(self):
        return self.cursor

    def cursor_execute(self, cmd):
        return self.cursor.execute(cmd)


if __name__ == '__main__':
    grades_db = GradesDatabase('data/database.db')
    class_name = 'adv_pre_calculus_b'
    grades_db.create_class_table(class_name)

    data = []
    assignments = [{'name': 'Sequence HW', 'due': ['04/02/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '90', 'highlighted': True}}, {'name': 'Chapter 6 Quiz', 'due': ['03/29/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '98', 'highlighted': True}}, {'name': 'Triangle Story', 'due': ['03/29/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '99', 'highlighted': True}}, {'name': 'Chapter 6 Progress', 'due': ['03/27/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '100', 'highlighted': True}}, {'name': 'Area HW', 'due': ['03/26/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '100', 'highlighted': True}}, {'name': 'Law of Sines & Cosines', 'due': ['03/12/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '100', 'highlighted': True}}, {'name': 'Solving HW', 'due': ['03/06/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '96', 'highlighted': True}}, {'name': 'Chap. 5 Obj 1.', 'due': ['03/06/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '100', 'highlighted': True}}, {'name': 'Chap. 5 Obj. 2', 'due': ['03/06/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '97', 'highlighted': True}}, {'name': 'Sum/Difference Formulas', 'due': ['02/28/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '100', 'highlighted': True}}, {'name': 'Trig Identity', 'due': ['02/24/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '90', 'highlighted': True}}, {'name': 'Trig Identity HW', 'due': ['02/22/2023', '(5TH)'], 'col': '5TH', 'row': {'grade': '95', 'highlighted': True}}, {'name': 'Ferris Wheel Presentations', 'due': ['02/15/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '100'}}, {'name': 'Obj. 1 Chapter 4', 'due': ['02/13/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '94'}}, {'name': 'Obj. 2 Chapter 4', 'due': ['02/13/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '88'}}, {'name': 'Obj. 3 Chapter 4', 'due': ['02/13/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '100'}}, {'name': 'Ferris Wheel Testing', 'due': ['02/13/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '100'}}, {'name': 'Chapter 4 HW 2', 'due': ['02/12/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '100'}}, {'name': 'Take - Home Quiz', 'due': ['01/22/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '90'}}, {'name': 'Graph Analysis', 'due': ['01/20/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '90'}}, {'name': 'Week 2 Participation', 'due': ['01/20/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '100'}}, {'name': 'Critical Friends Presentations', 'due': ['01/20/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '84'}}, {'name': 'Trig Homework', 'due': ['01/15/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '94'}}, {'name': 'Week 1 Participation', 'due': ['01/13/2023', '(4TH)'], 'col': '4TH', 'row': {'grade': '100'}}]

    for a in assignments:
        tup = (a['name'], a['due'][0], a['col'], a['row']['grade'], 'highlighted' in a['row'])
        data.append(tup)

    grades_db.insert_list_into_table(class_name, data)
    grades_db.commit()

    for row in grades_db.get_cursor().execute("SELECT * FROM adv_pre_calculus_b ORDER BY due"):  # WHERE col = '4TH'
        print(row)

    grades_db.close()
