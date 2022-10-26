from requests import Session
from datetime import date
from dateutil import parser
from datetime import datetime

"""
PARENT
"""
class BellScheduleParent:
    url = None
    
    def __init__(self, sess):
        self.sess = sess

    def get(self, **args):
        return self.sess.get(self.url.format(**args)).json()

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
        return {d['id']: BellDistrict(d) for d in super().get(id=id, **args)}

class BellPopularDistricts(GetBellDistricts):
    """no params"""
    url = 'https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/district?select=*&order=name.asc.nullslast'

class BellAllDistricts(GetBellDistricts):
    """id: Minimum district id (for paging)"""
    url = 'https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/district_all?select=*&id=gt.{id}&order=name.asc.nullslast&hide=eq.false&limit=20'

"""
SCHOOLS
"""
class GetBellSchool(BellScheduleParent):
    """district: BellDistrict"""
    def get(self, district: BellDistrict):
        return {d['id']: BellSchool(d) for d in super().get(id=district.id)}

class BellSchoolsPerDistrict(GetBellSchool):
    url = 'https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/school?select=*&district=eq.{id}&order=name.asc.nullslast'

"""
SCHEDULE
"""
class GetBellSchedule(BellScheduleParent):
    """school: BellSchool"""
    def get(self, school: BellSchool):
        return {d['id']: BellSchedule(d) for d in super().get(id=school.id)}
    
class BellSchedulePerSchool(GetBellSchedule):
    url = 'https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/schedule?select=*&school=eq.{id}&order=name.asc.nullslast'

"""
GROUP
"""
class GetBellGroup(BellScheduleParent):
    """school: BellSchool"""
    def get(self, school: BellSchool):
        return {d['id']: BellGroup(d) for d in super().get(id=school.id)}

class BellGroupsPerSchool(GetBellGroup):
    url = 'https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/group?select=*&school=eq.{id}&order=name.asc.nullslast'

"""
RULE
"""
class GetBellRule(BellScheduleParent):
    """group: BellGroup"""
    def get(self, group: BellGroup, schedule: dict):
        rules = {}
        resp = super().get(id=group.id, date=str(date.today()))
        for d in resp:
            rule = BellRule(d)
            rule.name = schedule[d['schedule']].name
            rules[rule.date] = rule
        return rules
    
class BellRulesPerGroup(GetBellRule):
    url = 'https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/rule?select=*&group=eq.{id}&type=eq.override&date=gte.{date}'

"""
DAY
"""
class GetBellDay(BellScheduleParent):
    """scheduleId: int"""
    def get(self, scheduleId: int):
        return {d['id']: BellDay(d) for d in super().get(id=scheduleId)}
    
class BellDayPerSchedule(GetBellDay):
    url = 'https://kimdjytfhkfavzkkccxt.supabase.co/rest/v1/bell?select=*&schedule=eq.{id}&order=time.asc.nullslast'


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
        "X-Requested-With": "scott.william.bellschedule"
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
    schedule[0] = BellSchedule({'id': 0, 'name': 'No School'})
    # Get groups (grade levels) per school
    groups = BellGroupsPerSchool(sess).get(school=selectedSchool)
    selectedGroup = groups[prompt_values(groups)]
    # Get rules (a/b days) per group
    rules = BellRulesPerGroup(sess).get(group=selectedGroup, schedule=schedule)
    
    """--- Show information for today ---"""
    
    today = rules[str(date.today())]  # Get today's rule, given the date as YYYY-MM-DD
    print('Today is', today.name)  # Print today's name (A or B day)
    print('Today\'s schedule:')
    # Get today's schedule
    todaySchedule = BellDayPerSchedule(sess).get(today.schedule)
    # Print class times
    for period in todaySchedule.values():
        print('Time:', period.time.strftime('%I:%M %p'), '-', # Time, formatted to 12 hour
              'Names:', period.names, '-',  # Class names
              'Icon:', period.icon)         # Icon svg file name
    
    """--- Get current class right now ---"""
    
    now = datetime.now()
    # now = parser.parse('09:15')  # For testing
    for id, period in todaySchedule.items():
        if period.time > now:  # Find current class. Time can be compared as datetime objects
            print('Current class:', period.names)
            print('Time left:', period.time - now)
            try:
                print('Next class:', todaySchedule[id + 1].names)
            except KeyError:
                print('Last class of the day!')
            break
    else:
        print('No more classes today!')
        
    
if __name__ == "__main__":
    exampleRun()
