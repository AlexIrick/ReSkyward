import json
import os
import re
from datetime import datetime

from bs4 import BeautifulSoup as bs
from titlecase import titlecase

import sqlgrades


class ParseData:
    def __init__(self, soup, data):
        self.soup = soup
        self.data = data

    def get_h_div(self, h, t):
        return bs(h, 'lxml').find(t)

    def get_row_info(self, h_div, text_name='text'):
        return {
            key: value
            for key, value in {
                text_name: h_div.text.strip(),
                'tooltip': h_div.get('tooltip'),
                'highlighted': ('sf_highlightYellow' in h_div['class']),
            }.items()
            if value
        }

    @staticmethod
    def abbreviations(word, **kwargs):
        if len(word) < 3 and word.upper() != 'OF':
            return word.upper()
        elif word.upper() == 'ADVANCED':
            return 'Adv'

    def get_assign_row_info(self, a_div):
        a = a_div.find('a')
        return {
            key: value
            for key, value in {
                'grade': a_div.text.strip(),
                'highlighted': ('sf_highlightYellow' in a_div['class']),
                'info': a and a.get('data-info'),
            }.items()
            if value
        }

    def get_class_info(self, cId):
        class_div = self.soup.find('div', id=cId)
        class_name = titlecase(class_div.find('span').text.strip(), callback=self.abbreviations)
        return {
            'class': class_name,
            'id': cId,
            'dropped': (dropped.text.strip() == "(Dropped)")
            if (dropped := class_div.find('span', class_='fXs'))
            else False,
            'period': ' '.join(class_div.find_all('td')[2].text.split()),
            'teacher': class_div.find_all('td')[3].text.strip(),
        }

    def get_assignment_info(self, a_name, a_div):
        return {
            key: value
            for key, value in {
                'name': a_name,
                'due': a_div.find('span').text.split('\xa0\xa0'),
                'highlighted': ('sf_highlightYellow' in a_div['class']),
            }.items()
            if value
        }

    def only_rows_with_content(self, rows):
        return (
            [
                {'col': self._headers_row[n + 1]['text'], 'row': i}
                for n, i in enumerate(rows)
                if i.get('grade')
            ][0]
            if any(('grade' in i) for i in rows)
            else {}
        )

    def handle_tb(self, tb, th_only=False):
        rows = []
        for d in tb:
            # TABLE HEADER
            if th_only:
                self._headers_row = [
                    self.get_row_info(self.get_h_div(c['h'], 'th')) for c in d['c']
                ]
                rows.append({'headers': self._headers_row})
            # CLASSES
            elif cId := d['c'][0].get('cId'):
                class_row_index = len(rows)
                rows.append(
                    {
                        'class_info': self.get_class_info(cId),
                        'grades': [
                            self.get_row_info(self.get_h_div(c['h'], 'td')) for c in d['c'][1:]
                        ],
                        'assignments': [],
                    }
                )
            # ASSIGNMENTS
            elif a_name := (a_div := self.get_h_div(d['c'][0]['h'], 'td')).find(
                'a', id='showAssignmentInfo'
            ):
                rows[class_row_index]['assignments'].append(
                    {
                        **self.get_assignment_info(a_name.text.strip(), a_div),
                        **self.only_rows_with_content(
                            [
                                self.get_assign_row_info(self.get_h_div(c['h'], 'td'))
                                for c in d['c'][1:]
                            ]
                        ),
                    }
                )
        return rows

    def grid_object_to_grid(self, table, db):
        tab_dict = []
        tab_dict.extend(self.handle_tb(table['th']['r'], th_only=True))
        tab_dict.extend(self.handle_tb(table['tb']['r']))
        # remove dropped classes
        tab_dict = [
            k for k in tab_dict if not (k.get('class_info') and k['class_info'].get('dropped'))
        ]
        for j, class_ in enumerate(tab_dict):  # for every class
            if "headers" in class_:
                continue
            file_name = (
                'data/' + re.sub(r'[\W_]+', '-', class_['class_info']['class'].lower()) + '.json'
            )
            # print('class: ' + str(class_['assignments']))
            # db.create_class_table(file_name)
            # db.insert_list_into_table(file_name, class_['assignments'])
            # db.commit()
            with open(file_name, 'w') as f:
                json.dump(class_['assignments'], f, indent=4)
            tab_dict[j]['assignments'] = file_name
        return tab_dict

    def run(self):
        if not os.path.exists('data'):
            os.mkdir('data')
        grades_db = sqlgrades.GradesDatabase('grades.db')
        tables = [self.grid_object_to_grid(table, grades_db) for table in self.data.values()]
        with open('data/SkywardExport.json', 'w') as f:
            json.dump(tables, f, indent=4)
        print('Done!')
        # Store the refresh date
        with open('data/updated.json', 'w') as f:
            json.dump({'date': datetime.now().strftime(r"%b %#d, %#I:%M:%S %p")}, f, indent=4)


if __name__ == "__main__":
    import argparse
    import os
    import sys

    # parser
    parser = argparse.ArgumentParser(description='Parse data')
    parser.add_argument('--html', help='HTML file')
    parser.add_argument('-d', '--data', help='JSON data file')
    args = parser.parse_args()

    with open(args.html, 'r') as htm:
        soup = bs(htm.read(), 'lxml')
    with open(args.data, 'r') as f:
        data = json.load(f)
    ParseData(soup, data).run()
