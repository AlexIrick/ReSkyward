import getpass
import re
import time
from functools import cached_property
from typing import Dict, Optional

import yaml
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer as ss
from tls_client import Session

from ReSkyward.scr import parser


class InvalidLogin(Exception):
    """Raised when the Skyward login fails"""

    pass


class Page:
    post: bool = True
    _soup: Optional[bs] = None

    def __init__(self, parent: 'Page' = None) -> None:
        self.response = None
        self.session = (
            parent.session
            if parent
            else Session(client_identifier="chrome_120", random_tls_extension_order=True)
        )

    def get_form_action(self, field) -> str:
        return self.soup.find("input", id=field)['value']

    def send(self) -> None:
        req = self.session.post if self.post else self.session.get
        self.response = req(self.url, headers=self.headers, data=self.data or None)
        print('PROPAGATING:', self.__class__.__name__)

    @property
    def soup(self) -> bs:
        if self._soup is None:
            self._soup = bs(self.response.text, "lxml", parse_only=ss("input"))
        return self._soup

    @cached_property
    def data(self) -> Dict[str, str]:
        ...


class HomePage(Page):
    url: str = "https://skyward-mansfield.iscorp.com/scripts/wsisa.dll/WService=wsedumansfieldtx/fwemnu01.w"
    headers: dict = {
        "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Priority": "u=0, i",
        "Connection": "close",
    }
    post: bool = False


class SkyPort(Page):
    def __init__(self, username: str, password: str, parent: Page):
        self.username: str = username
        self.password: str = password
        super().__init__()
        # dependency page
        self.page: HomePage = HomePage(parent=parent)

    url: str = "https://skyward-mansfield.iscorp.com/scripts/wsisa.dll/WService=wsedumansfieldtx/skyporthttp.w"

    updated_headers: Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Origin": "https://skyward-mansfield.iscorp.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://skyward-mansfield.iscorp.com/scripts/wsisa.dll/WService=wsedumansfieldtx/fwemnu01.w",
    }

    @cached_property
    def headers(self) -> Dict[str, str]:
        return {**self.page.headers, **self.updated_headers}

    @cached_property
    def extracted_fields(self) -> Dict[str, str]:
        # list of data items that need to be searched via get_form_action
        data_items = (
            'hNavSearchOption',
            'hSecCache',
            'CurrentProgram',
            'CurrentVersion',
            'SuperVersion',
            'PaCVersion',
            'hIPInfo',
            'hAnon',
            'pState',
            'pCountry',
            'hforgotLoginPage',
            'hButtonHotKeys',
            'hLoadTime',
            'hButtonHotKeyIDs',
        )
        return {item: self.page.get_form_action(item) for item in data_items}

    @cached_property
    def data(self) -> Dict[str, str]:
        self.page.send()
        data = {
            "requestAction": "eel",
            "method": "extrainfo",
            "codeType": "tryLogin",
            "codeValue": self.username,
            "login": self.username,
            "password": self.password,
            "SecurityMenuID": "0",
            "HomePageMenuID": "0",
            "nameid": "-1",
            "Browser": "Chrome",
            "BrowserVersion": "120",
            "BrowserPlatform": "Win32",
            "TouchDevice": "false",
            "noheader": "yes",
            "duserid": "-1",
            "HomePage": "sepadm01.w",
            "loginID": "-1",
            "hUseCGIIP": "yes",
            "hScrollBarWidth": "17",
            "UserSecLevel": "5",
            "UserLookupLevel": "5",
            "AllowSpecial": "false",
            "hDisplayBorder": "true",
            "hAlternateColors": "true",
            "screenWidth": "1707",
            "screenHeight": "1067",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36",
            "osName": "Windows 10",
            "brwsInfo": "Chrome 120",
            "subversion": "120",
            "supported": "true",
            "pageused": "Desktop",
            "recordLimit": "30",
            "disableAnimations": "yes",
            "hOpenSave": "no",
            "hAutoOpenPref": "no",
            "lip": "17c0f264-4170-4642-ac30-1dfed185bdf9.local",
            "cUserRole": "family/student",
            "fwtimestamp": str(int(time.time())),
        }

        # update
        data.update(self.extracted_fields)

        return data

    def send(self) -> None:
        super().send()
        if "We are unable to validate the information entered" in self.response.text:
            raise InvalidLogin("Invalid Login")

    @cached_property
    def extracted_skyport(self) -> Dict[str, str]:
        # Regex to capture the content inside <li> tags
        match = re.search(r'<li>\s*?([^<]+)\s*?</li>', self.response.text)
        values = match[1].split('^')
        # this has really weird formatting
        # here is an example:
        # 256842^513684^80444170^79098768^17765^ex123456^2^sfhome01.w^false^no ^no^no^^enc^encses^LoginHistoryIdentifier...
        # 0     1      2        3        4     5        6 7          8     9   0 1   23   4      ...

        # mapping
        return {
            "dwd": values[0],  # 256842
            "web-data-recid": values[1],  # 513684
            "wfaacl-recid": values[2],  # 80444170
            "wfaacl": values[3],  # 79098768
            "nameid": values[4],  # 17765
            "duserid": values[5],  # ex123456
            "User-Type": values[6],  # 2
            "PreviousProgram": values[7],  # sfhome01.w
            "TouchDevice": values[8],  # false
            # "OpenRow": 'no',  # assuming 'no' maps to 'OpenRow'
            # "OpenDetails": 'no',  # assuming 'no' maps to 'OpenDetails'
            "enc": values[13],  # enc
            "encses": values[14],  # encses
        }


class SfGradebook(Page):
    url: str = "https://skyward-mansfield.iscorp.com/scripts/wsisa.dll/WService=wsedumansfieldtx/sfgradebook001.w"

    updated_headers: Dict[str, str] = {
        "Cache-Control": "max-age=0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        # dependency page
        self.page = SkyPort(*args, **kwargs, parent=self)

    @cached_property
    def headers(self) -> Dict[str, str]:
        return {**self.page.headers, **self.updated_headers}

    @cached_property
    def data(self) -> Dict[str, str]:
        self.page.send()

        data = {
            "login": '',
            "password": '',
            "cUserRole": "family/student",
            # "dwd": "291807",
            # "wfaacl": "79122477",
            # "encses": "nplndFbBvpliibpb",
            "entity": '',
            "entities": '',
            "SecurityMenuID": "0",
            "HomePageMenuID": "0",
            "LinkNames": '',
            # "nameid": "17765",
            "MobileId": '',
            "hNavMenus": '',
            "hNavSubMenus": '',
            # "hNavSearchOption": "all",
            # "hSecCache": "0 items in 0 entities",
            "LinkData": '',
            "passedparams": '',
            "vMaintOption": '',
            # "CurrentProgram": "skyportlogin.w",
            # "CurrentVersion": "010197",
            # "SuperVersion": "012157",
            # "PaCVersion": "05.23.10.00.08",
            "currentrecord": '',
            "encrow": '',
            "BrowseRowNumber": '',
            "Browser": "Chrome",
            "BrowserVersion": "120",
            "BrowserPlatform": "Win32",
            # "TouchDevice": "false",
            "OpenRow": '',
            "OpenDetails": '',
            "PopupWidth": "1013",
            "PopupHeight": "671",
            "noheader": "yes",
            "vSelectMode": "N",
            # "PreviousProgram": '',
            # "duserid"
            "RefreshMode": '',
            "hExcelRandom": '',
            # "hIPInfo"
            "hBrowseFirstRowid": '',
            "HomePage": "sepadm01.w",
            "hApplyingFilter": '',
            "hRepositioning": '',
            "loginID": "-1",
            "pDesc": '',
            "pProgram": '',
            "pParams": '',
            "pPath": '',
            "pInfo": '',
            "pType": '',
            "pSrpplmIn": '',
            "pPriority": '',
            "pButtons": '',
            "fileUploadLimit": '',
            "blobid": '',
            "pEnc": '',
            "fileInputId": '',
            "delAttachReturn": '',
            "hUseCGIIP": "yes",
            "hScrollBarWidth": "17",
            "UserSecLevel": "5",
            "UserLookupLevel": "5",
            "AllowSpecial": "false",
            # "hAnon": "bjlbYpAByjicxUsV",
            # "pState": "TX",
            # "pCountry": "US",
            "hDisplayBorder": "true",
            "hAlternateColors": "true",
            "BrowserName": '',
            # "web-data-recid": "583614",
            # "wfaacl-recid": "80469124",
            # "User-Type": "2",
            "tempAccess": '',
            "screenWidth": "1707",
            "screenHeight": "1067",
            "showTracker": "false",
            "displaySecond": "no",
            "insecure": "no",
            "redirectTo": '',
            # "enc": "kUncFrlcNcvckfkj",
            # "hforgotLoginPage": "fwemnu01",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36",
            "osName": "Windows 10",
            "brwsInfo": "Chrome 120",
            "subversion": "120",
            "supported": "true",
            "pageused": "Desktop",
            "recordLimit": "30",
            "hFilterOpen": '',
            "filterElementList": '',
            "currentbrowse": '',
            "vSelectedColumn": '',
            "vSelectedColumnDirection": '',
            "disableAnimations": "yes",
            "hOpenSave": "no",
            "hAutoOpenPref": "no",
            # "hButtonHotKeyIDs": "bCancel",
            # "hButtonHotKeys": "B",
            # "hLoadTime": ".036",
            "lip": "17c0f264-4170-4642-ac30-1dfed185bdf9.local",
        }

        data.update(self.page.extracted_skyport)
        data.update(self.page.extracted_fields)

        return data


def GetSkywardPage(username: str, password: str):
    page: Page = SfGradebook(username, password)
    page.send()

    # get grid objects
    print('PARSING: Grid objects')
    b: str = "sff.sv('sf_gridObjects',$.extend((sff.getValue('sf_gridObjects') || {}), "
    data = yaml.load(  # use yaml for more tolerant parsing
        re.search(re.escape(b) + '\\{.*\\}', page.response.text)[0][len(b) :],
        Loader=yaml.CLoader,
    )

    # parse html tables
    print('PARSING: HTML tables')
    grade_soup = bs(page.response.text, 'lxml')
    data_parser = parser.ParseData(grade_soup, data)
    data_parser.run()


if __name__ == "__main__":
    username = input("> Username: ")
    password = getpass.getpass(prompt='> Password: ', stream=None)
    GetSkywardPage(username, password)
