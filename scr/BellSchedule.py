import re
from datetime import date, datetime, timedelta

from dateutil import parser, rrule
from pytz import utc
from requests import Session

"""
PARENT
"""


class BellScheduleParent:
    url = None

    def __init__(self, sess):
        self.sess = sess

    def get(self, **args):
        return self.sess.get(
            f"https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/{self.url}".format(**args)
        ).json()


"""
SPECIFICS
"""


class BellSpecific:
    def __init__(self, data):
        for key, value in data.items():
            if key == 'created_at':  # Remove creation time
                continue
            elif key == 'time':  # Parse times
                setattr(self, key, parser.parse(value))
                continue
            setattr(self, key, value)


class BellDistrict(BellSpecific):
    pass


class BellSchool(BellSpecific):
    pass


class BellGroup(BellSpecific):
    pass


class BellSchedule(BellSpecific):
    pass


class BellRule(BellSpecific):
    pass


class BellDay(BellSpecific):
    pass


"""
DISTRICTS
"""


class GetBellDistricts(BellScheduleParent):
    def get(self, id=0, **args):
        return {d['name']: BellDistrict(d) for d in super().get(id=id, **args)}


class BellPopularDistricts(GetBellDistricts):
    """no params"""

    url = 'district?select=*&order=name.asc.nullslast'


class BellAllDistricts(GetBellDistricts):
    """id: Minimum district id (for paging)"""

    url = 'district_all?select=*&id=gt.{id}&order=name.asc.nullslast&hide=eq.false&limit=20'


"""
SCHOOLS
"""


class GetBellSchool(BellScheduleParent):
    """district: BellDistrict"""

    def get(self, district: BellDistrict):
        return {d['name']: BellSchool(d) for d in super().get(id=district.id)}


class BellSchoolsPerDistrict(GetBellSchool):
    url = 'school?select=*&district=eq.{id}&order=name.asc.nullslast'


"""
SCHEDULE
"""


class GetBellSchedule(BellScheduleParent):
    """school: BellSchool"""

    def get(self, school: BellSchool):
        schedule = {d['id']: BellSchedule(d) for d in super().get(id=school.id)}
        schedule[0] = BellSchedule(
            {'id': 0, 'name': 'No School - Holiday'}
        )  # Normally school today, but there isn't
        return schedule


class BellSchedulePerSchool(GetBellSchedule):
    url = 'schedule?select=*&school=eq.{id}&order=name.asc.nullslast'


"""
GROUP
"""


class GetBellGroup(BellScheduleParent):
    """school: BellSchool"""

    def get(self, school: BellSchool):
        return {d['name']: BellGroup(d) for d in super().get(id=school.id)}


class BellGroupsPerSchool(GetBellGroup):
    url = 'group?select=*&school=eq.{id}&order=name.asc.nullslast'


"""
RULE
"""


class GetBellRule(BellScheduleParent):
    pass


class BellDefaultRulesPerGroup(GetBellRule):
    url = 'rule?select=*&group=eq.{id}&type=eq.default'
    _re_byday = re.compile(r'BYDAY=([\w,]+);?')
    _re_dtstart = re.compile(r'DTSTART:(.*)')

    def get_dtstart(self, rrule_str):
        return parser.parse(re.search(self._re_dtstart, rrule_str)[1]).replace(tzinfo=utc)

    def _get_next_dt(self, resp, compare, index):
        if index == len(resp) - 1:
            return self.get_dtstart(resp[index]['rule']) + timedelta(weeks=52)
        for r in resp[index + 1 :]:
            if re.search(self._re_byday, r['rule'])[1] == compare:
                return self.get_dtstart(r['rule'])
        return self.get_dtstart(r['rule']) + timedelta(weeks=52)

    def get(self, group: BellGroup, schedule: dict):
        rules = {}
        resp = super().get(id=group.id)
        resp = sorted(resp, key=lambda x: re.search(self._re_dtstart, x['rule'])[1])
        for n, d in enumerate(resp):
            next_time = self._get_next_dt(resp, re.search(self._re_byday, d['rule'])[1], n)
            daterule = rrule.rrulestr(d['rule'])
            for dt in daterule:
                if next_time and dt >= next_time:
                    break
                # Add rule to rules dict
                rules[dt.strftime(r'%Y-%m-%d')] = BellRule(
                    {
                        'name': schedule[d['schedule']].name,
                        'schedule': schedule[d['schedule']].id,
                        'id': d['id'],
                    }
                )
        return rules


class BellRulesPerGroup(GetBellRule):
    """group: BellGroup"""

    url = 'rule?select=*&group=eq.{id}&type=eq.override&date=gte.{date}'

    def get(self, group: BellGroup, schedule: dict):
        rules = {}
        resp = super().get(id=group.id, date=str(date.today()))
        for d in resp:
            rule = BellRule(d)
            rule.name = schedule[d['schedule']].name
            rules[rule.date] = rule
        return rules


"""
DAY
"""


class GetBellDay(BellScheduleParent):
    """scheduleId: int"""

    def get(self, scheduleId: int):
        return {d['id']: BellDay(d) for d in super().get(id=scheduleId)}


class BellDayPerSchedule(GetBellDay):
    url = 'bell?select=*&schedule=eq.{id}&order=time.asc.nullslast'


def createSession():
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Profile": "public",
        "Apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpbWRqeXRmaGtmYXZ6a2tjY3h0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2NTUyNDMxMDYsImV4cCI6MTk3MDgxOTEwNn0.-OpsTQyMsGBjqF8Gr_3ckVV1PY1ZGIJ4ovP5vZQ8LPk",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpbWRqeXRmaGtmYXZ6a2tjY3h0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2NTUyNDMxMDYsImV4cCI6MTk3MDgxOTEwNn0.-OpsTQyMsGBjqF8Gr_3ckVV1PY1ZGIJ4ovP5vZQ8LPk",
        "Connection": "keep-alive",
        "Host": "kimdjytfhkfavzkkccxt.supabase.co",
        "Origin": "http://localhost",
        "Referer": "http://localhost/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 5 Build/SQ3A.220705.003.A1; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.71 Safari/537.36",
        "X-Client-Info": "supabase-js/1.35.3",
        "X-Requested-With": "scott.william.bellschedule",
    }
    sess = Session()
    sess.headers = headers
    return sess


def exampleRun():
    """
    API usage example
    """
    sess = createSession()

    def prompt_values(specifics):
        # Simple function to list id's and values
        for s in specifics.values():
            print(f'{s.id}:\t{s.name}')
        return int(input('Select an ID: '))

    """--- Gathering information ---"""

    # Get district
    districts = BellPopularDistricts(sess).get()
    selectedDistrict = districts[prompt_values(districts)]
    # Get school
    schools = BellSchoolsPerDistrict(sess).get(district=selectedDistrict)
    selectedSchool = schools[prompt_values(schools)]
    # Get schedule names per school
    schedule = BellSchedulePerSchool(sess).get(school=selectedSchool)
    # Get groups (grade levels) per school
    groups = BellGroupsPerSchool(sess).get(school=selectedSchool)
    selectedGroup = groups[prompt_values(groups)]
    # Get rules (a/b days) per group
    rules = {
        **BellDefaultRulesPerGroup(sess).get(group=selectedGroup, schedule=schedule),
        **BellRulesPerGroup(sess).get(group=selectedGroup, schedule=schedule),
    }
    print('---')

    """--- Show information for today ---"""
    day = str(date.today())
    try:
        today = rules[day]  # Get today's rule, given the date as YYYY-MM-DD
    except KeyError:
        # No school today; print the next day of school and exit
        print('No school today!')  # No school today
        print('Next day of school:', end=' ')
        days = sorted(rules.items())  # Listed days
        for listed_day, bell_day in days:
            # If the day is after today and has a schedule
            if listed_day > day and bell_day.schedule:
                print(listed_day)
                return  # exit

    print('Today is', today.name)  # Print today's name (A or B day)
    # Get today's schedule
    todaySchedule = BellDayPerSchedule(sess).get(today.schedule)
    # Print class times
    for period in todaySchedule.values():
        print(
            'Time:',
            period.time.strftime('%I:%M %p'),
            '-',  # Time, formatted to 12 hour
            'Names:',
            period.names,
            '-',  # Class names
            'Icon:',
            period.icon,
        )  # Icon svg file name
    print('---')

    """--- Get current class right now ---"""

    t = Terminal()
    while True:
        now = datetime.now()
        for id, period in todaySchedule.items():
            if period.time > now:  # Find current class. Time can be compared as datetime objects
                print('Current class:', period.names, '\t\t')
                print('Time left:', period.time - now, '\t\t')
                try:
                    print('Next class:', todaySchedule[id + 1].names, '\t\t')
                except KeyError:
                    print('Last class of the day!')
                break
        else:
            print('No more classes today!')
        # Move terminal up 3 lines
        print(t.move_up(3), end='')


def create_session():
    """--- Gathering information ---"""
    return createSession()


def get_districts(sess):
    return BellPopularDistricts(sess).get()  # returns popular districts


def get_schools(sess, selected_district):
    # Get school
    return BellSchoolsPerDistrict(sess).get(district=selected_district)  # returns schools


def get_groups(sess, selected_school):
    # Get schedule names per school
    schedule = BellSchedulePerSchool(sess).get(school=selected_school)
    schedule[0] = BellSchedule({'id': 0, 'name': 'No School'})
    # Get groups (grade levels) per school
    groups = BellGroupsPerSchool(sess).get(school=selected_school)
    return groups, schedule


def get_rules(sess, selected_group, schedule):
    # Get rules (a/b days) per group
    return BellRulesPerGroup(sess).get(group=selected_group, schedule=schedule)  # return rules


def get_schedule(sess, selected_school, rules):
    """
    Gets the schedule data
    :return: Returns schedule data and string denoting if there is school or not
    """

    data = {'selected_school': selected_school}

    """--- Show information for today ---"""
    day = str(date.today())
    # day = "2022-11-11"

    days = sorted(rules.items())  # Listed days
    for listed_day, bell_day in days:
        # If the day is after today and has a schedule
        if listed_day > day and bell_day.schedule:
            data['next_school_day'] = rules[listed_day]
            break

    try:
        today = rules[day]  # Get today's rule, given the date as YYYY-MM-DD
    except KeyError:
        # No school today; print the next day of school and exit
        # self.refresh_bell_view(False)
        return [data, "no school"]

    data['today'] = today  # Set today's name (A or B day)

    # Get today's schedule
    today_schedule = BellDayPerSchedule(sess).get(today.schedule)
    data['today_schedule'] = today_schedule
    return [data, "school"]


def get_relevant_schedule_info(schedule_data):
    """
    Gets info from schedule and current period
    :param schedule_data: Dictionary containing info from get_schedule()
    :return:
    """
    if not schedule_data:
        return

    display_data = {}
    if 'is_school' in schedule_data and not schedule_data['is_school']:
        if 'next_school_day' in schedule_data:
            next_day = schedule_data['next_school_day']
            # Show next school day
            next_day_date = parser.parse(next_day.date)
            num_suffix = lambda n: (
                "th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            )
            next_day_date = next_day_date.strftime('%A, %b, %#d') + num_suffix(next_day_date.day)
            display_data[
                'next_period'
            ] = f'The next school day is \"{next_day.name}\", on {next_day_date}.'
        else:
            display_data['next_period'] = 'Cannot find the next school day.'
        # If there is no school then update labels accordingly
        display_data['today'] = 'No schedule today!'  # No school today
        display_data[
            'current_period'
        ] = 'It looks like there is no schedule today. Enjoy the day off!'
        display_data['time_left'] = ''
        return display_data

    now = datetime.now()
    today_schedule = schedule_data['today_schedule']
    # today = schedule_data['today']
    # selected_school = schedule_data['selected_school']
    for id, period in today_schedule.items():
        if period.time > now:  # Find current class. Time can be compared as datetime objects
            # print('Current class:', period.names, '\t\t')
            display_data['current_period'] = "Current: " + " / ".join(period.names)
            # print('Time left:', period.time - now, '\t\t')
            time_left = str(period.time - now)
            # remove microseconds and leading 0 from hours
            display_data['time_left'] = re.search(r'(^[0:]+)?(.*)\.', time_left)[2]

            try:
                display_data['next_period'] = "Next: " + " / ".join(today_schedule[id + 1].names)
            except KeyError:
                display_data['next_period'] = 'Last class of the day!'

            break
    else:
        display_data['time_left'] = ""
        display_data['current_period'] = "After school hours"

        # date_time_str = '10/30/22 07:00:00'
        # tomorrow = datetime.strptime(date_time_str, '%m/%d/%y %H:%M:%S')
        # time_left = str(tomorrow - now)
        # time_left = re.search(r'(^[0:]+)?(.*)\.', time_left)[2]  # removes microseconds and leading 0 from hours
        next_day = schedule_data['next_school_day']
        display_data[
            'next_period'
        ] = f"No more classes today! The next school day is \"{next_day.name}\""
    return display_data


if __name__ == "__main__":
    from blessed import Terminal

    exampleRun()
