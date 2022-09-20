import requests
from bs4 import BeautifulSoup as bs
import time
import yaml
import re
import getpass
import scrape

def GetSkywardPage(username, password):
    session = requests.session()
    headers = {
        "Sec-Ch-Ua": "\"(Not(A:Brand\";v=\"8\", \"Chromium\";v=\"99\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close"
    }
    session.headers = headers.copy()


    ## INITAL PAGE ##

    r_init = session.get("https://skyward-mansfield.iscorp.com:443/scripts/wsisa.dll/WService=wsedumansfieldtx/fwemnu01.w")

    print('SENDING REQUEST 1')
    init_soup = bs(r_init.text, "lxml")
    print('REQUEST 1 SENT')
    print(init_soup.prettify())


    ## LOGIN ##
    def get_form_action(field, soup=init_soup):
        print(field)
        return soup.find("input", id=field)["value"]

    session.headers.update({
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Origin": "https://skyward-mansfield.iscorp.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://skyward-mansfield.iscorp.com/scripts/wsisa.dll/WService=wsedumansfieldtx/fwemnu01.w",
    })
    del session.headers["Upgrade-Insecure-Requests"]

    _1_data = {
        "requestAction": "eel",
        "method": "extrainfo",
        "codeType": "tryLogin",
        "codeValue": username, "login": username,
        "password":   password,
        "Browser": "Chrome", "BrowserVersion": "99",
        "screenWidth": "800", "screenHeight": "600", 
        "userAgent": headers['User-Agent'],
        "osName": "Windows 10",
        "brwsInfo": "Chrome 99", "subversion": "99",
        "supported": "true",
        "lip": "ddaa4eb5-5e6b-4adc-ab6c-df3d03d51bad.local",
        "cUserRole": "family/student",
        "fwtimestamp": str(int(time.time()))
    }

    for key in [
        "SecurityMenuID", "HomePageMenuID", "nameid", "hNavSearchOption", "hSecCache", "CurrentProgram", "CurrentVersion",
        "SuperVersion","PaCVersion","BrowserPlatform","TouchDevice","noheader","duserid","hIPInfo","HomePage","loginID","hUseCGIIP",
        "hScrollBarWidth","UserSecLevel","UserLookupLevel","AllowSpecial","hAnon","pState","pCountry","hDisplayBorder","hAlternateColors",
        "hforgotLoginPage","pageused","recordLimit","disableAnimations","hOpenSave","hAutoOpenPref","hButtonHotKeyIDs","hButtonHotKeys","hLoadTime"
    ]:
        _1_data[key] = get_form_action(key)

    r_login = session.post("https://skyward-mansfield.iscorp.com:443/scripts/wsisa.dll/WService=wsedumansfieldtx/skyporthttp.w", data=_1_data)
    session_data = bs(r_login.text, 'lxml').find('li').text.split('^')


    ## HOME ##

    # update headers
    headers.update({
        "Cache-Control": "max-age=0",
        "Origin": "https://skyward-mansfield.iscorp.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "Sec-Fetch-Site": "same-origin",
        "Referer": "https://skyward-mansfield.iscorp.com/scripts/wsisa.dll/WService=wsedumansfieldtx/fwemnu01.w",
    })
    del headers["Sec-Fetch-User"]       # homepage isnt initated by user interaection, so delete this header
    session.headers = headers.copy()    # copy to session headers

    _2_data = {
        "dwd": session_data[0],
        "wfaacl": session_data[3],
        "encses": session_data[-1],
        "PopupWidth": "1013",
        "PopupHeight": "671",
        "vSelectMode": "N",
        "web-data-recid": session_data[1],
        "wfaacl-recid": session_data[2],
        "User-Type": "2",
        "showTracker": "false",
        "displaySecond": "no",
        "insecure": "no",
        "enc": session_data[-2],
        "lip": "ddaa4eb5-5e6b-4adc-ab6c-df3d03d51bad.local"
    }

    for key in [
        "SecurityMenuID", "HomePageMenuID", "nameid", "hNavSearchOption", "CurrentProgram", "CurrentVersion", "hSecCache",
        "SuperVersion", "PaCVersion", "Browser", "BrowserVersion", "BrowserPlatform", "TouchDevice", "noheader",
        "duserid", "hIPInfo", "HomePage", "loginID", "hUseCGIIP", "hScrollBarWidth", "UserSecLevel", "UserLookupLevel",
        "AllowSpecial", "hAnon", "pState", "pCountry", "hDisplayBorder", "hAlternateColors", "screenWidth", "screenHeight",
        "hforgotLoginPage", "userAgent", "osName", "brwsInfo", "subversion", "supported", "pageused", "recordLimit",
        "disableAnimations", "hOpenSave", "hAutoOpenPref", "hButtonHotKeyIDs", "hButtonHotKeys", "hLoadTime"
    ]:  _2_data[key] = _1_data[key]
    for key in [
        "login", "password", "encsec", "entity", "entities", "LinkNames", "MobileId", "hNavMenus", "hNavSubMenus",
        "LinkData", "passedparams", "vMaintOption", "currentrecord", "encrow", "BrowseRowNumber", "OpenRow",
        "OpenDetails", "PreviousProgram", "RefreshMode", "hExcelRandom", "hBrowseFirstRowid", "hApplyingFilter",
        "hRepositioning", "pDesc", "pProgram", "pParams", "pPath", "pInfo", "pType", "pSrpplmIn", "pPriority",
        "pButtons", "fileUploadLimit", "blobid", "pEnc", "fileInputId", "delAttachReturn", "BrowserName",
        "tempAccess", "redirectTo", "hFilterOpen", "filterElementList", "currentbrowse", "vSelectedColumn",
        "vSelectedColumnDirection",
    ]:  _2_data[key] = ''
    r_home = session.post("https://skyward-mansfield.iscorp.com:443/scripts/wsisa.dll/WService=wsedumansfieldtx/sfhome01.w", data=_2_data)
    home_soup = bs(r_home.text, 'lxml')


    ## GRADEBOOK ##
    session.headers["Sec-Fetch-User"] = '?1'    # mark from here on as user initated

    _3_data = {"sessionid": f"{session_data[1]}\x15{session_data[2]}", "encses": get_form_action("encses", home_soup)}
    r_gradebook = session.post("https://skyward-mansfield.iscorp.com:443/scripts/wsisa.dll/WService=wsedumansfieldtx/sfgradebook001.w", data=_3_data)
    grade_soup = bs(r_gradebook.text, 'lxml') # we will use this later

    # get grid objects
    b = "sff.sv('sf_gridObjects',$.extend((sff.getValue('sf_gridObjects') || {}), "
    data = yaml.load(       # use yaml for more tolerant parsing
        re.search(re.escape(b)+'\\{.*\\}', r_gradebook.text)[0][len(b):],
        Loader=yaml.CLoader,
    )

    # run scraper, write to file
    data_parser = scrape.ParseData(grade_soup, data)
    data_parser.run()


if __name__ == "__main__":
    username = input("> Username: ")
    password = getpass.getpass(prompt='> Password: ', stream=None)
    GetSkywardPage(username, password)