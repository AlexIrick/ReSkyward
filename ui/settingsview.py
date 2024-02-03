from qfluentwidgets import ExpandSettingCard, SwitchSettingCard
from qfluentwidgets import FluentIcon as FIF
# from qfluentwidgets import 
from typing import Union
from PyQt5.QtGui import QIcon
from threading import Thread
from ReSkyward.ui import login, config

class FixedExpandSettingCard(ExpandSettingCard):
    """ Expandable setting card """

    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None, parent=None):
        super().__init__(icon, title, content, parent)
        # Set margins
        self.viewLayout.setContentsMargins(48, 10, 32, 16)
        self.viewLayout.setSpacing(8)
        
        
    def addWidgetToView(self, widget):
        self.viewLayout.addWidget(widget)
        self._adjustViewSize()


class SettingsView():
    def __init__(self, app):
        self.app = app
        
        # Variables
        self.skywardUsername = None
        self.skywardPassword = None
        
        # Skyward Refresh
        app.refreshBtn.setIcon(FIF.SYNC)
        app.refreshBtn.setText('')
        app.refreshBtn.clicked.connect(self.refresh_connect)
        
        # Skwyard Login Card
        app.loginCard = FixedExpandSettingCard(FIF.APPLICATION, "Log in", "Log in to Skyward")
        app.loginCard.addWidgetToView(app.usernameInput)
        app.loginCard.addWidgetToView(app.passwordInput)
        app.loginCard.addWidgetToView(app.loginButton)
        app.loginCard.addWidgetToView(app.rememberMeCheck)
        app.settingsContent.addWidget(app.loginCard)
        
        app.citizenCard = SwitchSettingCard(FIF.FILTER, "Hide Citizen", "Hide the citizen columns of the Skyward table")
        app.settingsContent.addWidget(app.citizenCard)
        app.citizenCard.checkedChanged.connect(self.hideCitizenChanged)
        
        # TODO: self.hideCitizenCheck.stateChanged.connect(self.set_hide_citizen)
        # TODO: self.refreshOnLaunchCheck.stateChanged.connect(
        #     lambda: self.config.set_refresh_on_launch(self.refreshOnLaunchCheck.isChecked())
        # )
        
        
        # Config Setup
        self.config = config.Config(self)
        # Login Setup
        self.loginManager = login.LoginManager(app)
        app.loginButton.clicked.connect(self.login_connect)
        # signal to refresh UI after updated database is loaded
        self.app.database_refreshed.connect(self.app.get_skyward_view().load_skyward_view)
        
        self.load_saved_creds()
        
    def hideCitizenChanged(self, checked: bool):
        self.config.set_hide_citizen(checked)
        print(checked)
        
    
    def login_connect(self):
        password = self.app.passwordInput.text()
        self.app.passwordInput.clear()
        self.login(self.app.usernameInput.text(), password)
        

    def refresh_connect(self):
        if self.skywardUsername is not None and self.skywardPassword is not None: 
            self.login(self.skywardUsername, self.skywardPassword)
        # TODO: Add exception handling that indicates to the user that they didnt have a login saved 

    def load_saved_creds(self):
        if self.loginManager.has_saved_logins():
            creds = self.loginManager.get_login()
            if False and self.ref_on_launch: # TODO: setup refresh on launch
                # load skyward if refresh on launch (setting) is enabled
                self.login(creds[0]['account'], creds[0]['password'])
            else:
                # else just save the pass and username as a variable so that the user can just click refresh
                self.skywardUsername = creds[0]['account']
                self.skywardPassword = creds[0]['password']
                # TODO: add exception handling
                self.app.get_skyward_view().load_skyward_view()
        else:
            # TODO: add exception handling
            self.app.get_skyward_view().load_skyward_view()
            
    def login(self, username: str, password: str):
        arguments = [username, password]
        Thread(target=self.loginManager.login, args=arguments, daemon=True).start()
        
            
