import pycreds
import requests.exceptions

from ReSkyward.scr import scrape


class LoginManager:
    
    def __init__(self, app, service='ReSkyward'):
        self.app = app
        self.service = service
        
    
    def save_login(self, username: str, password: str) -> None:
        # Clear to ensure there are no other accounts saved
        self.clear_all_logins()
        # Store credentials
        pycreds.set_password(self.service, username, password)


    def clear_all_logins(self) -> None:
        for cred in pycreds.find_credentials(self.service):
            self.delete_login(cred['account'])


    def delete_login(self, username: str) -> None:
        pycreds.delete_password(self.service, username)


    def get_login(self):
        return pycreds.find_credentials(self.service)


    def has_saved_logins(self) -> bool:
        return len(self.get_login()) > 0


    # UI
    def login(self, user, pw):
        self.app.loginButton.setEnabled(False)
        # TODO: self.app.lastRefreshedLabel.setText('Refreshing...')
        
        # data = self.get_user_info()

        # TODO: improve exception handler
        try:
            # login(self, user, pw)
            scrape.GetSkywardPage(user, pw)
        except scrape.InvalidLogin:
            # INVALID LOGIN:
            print("Invalid Login")
            # TODO: add invalid login error message
            # app.settings_clicked(0)
            # app.error_msg_signal.emit('Invalid login. Please try again.')
            # app.loginLabel.setText('Not logged in')
            # app.title_bar_button_clicked('settings', False)
            self.app.skywardUsername = None
            self.app.skywardPassword = None
            self.clear_all_logins()
        except requests.exceptions.ConnectionError:
            # CONNECTION ERROR:
            print("Connection error")
            # TODO: add connection error
            # app.error_msg_signal.emit('Network error. Please check your internet connection.')
        else:
            # LOGIN SUCCESSFUL:
            self.app.database_refreshed.emit() # goes to skywardView.load_skyward_view()
            print(f'Logged in as {user}')
            # TODO: app.loginLabel.setText(f'Logged in as {user}')
            # TODO: app.helloUserLabel.setText(f'Hello {user}!')

            if self.app.rememberMeCheck.isChecked():
                self.save_login(user, pw)
            self.app.skywardUsername = user
            self.app.skywardPassword = pw
        self.app.loginButton.setEnabled(True)


if __name__ == "__main__":
    loginManager = LoginManager('Login Manager Test')
    loginManager.save_login("user", 'pass')
    print(loginManager.get_login())
    # clear_all_logins()
