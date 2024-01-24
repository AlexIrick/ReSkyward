import pycreds
import scrape
import requests.exceptions

service = 'ReSkyward'


def save_login(username: str, password: str):
    # Clear to ensure there are no other accounts saved
    clear_all_logins()
    # Store credentials
    pycreds.set_password(service, username, password)


def clear_all_logins():
    for cred in pycreds.find_credentials(service):
        delete_login(cred['account'])


def delete_login(username: str):
    pycreds.delete_password(service, username)


def get_login():
    return pycreds.find_credentials(service)


# UI
def login(app, user, pw):
    app.skywardLoginButton.setEnabled(False)
    app.rememberMe = app.loginRememberCheck.isChecked()

    app.lastRefreshedLabel.setText('Refreshing...')
    # data = self.get_user_info()

    # TODO: improve exception handler
    try:
        # login(self, user, pw)
        scrape.GetSkywardPage(user, pw)
    except scrape.InvalidLogin:
        # INVALID LOGIN:
        app.settings_clicked(0)
        app.error_msg_signal.emit('Invalid login. Please try again.')
        app.loginLabel.setText('Not logged in')
        app.title_bar_button_clicked('settings', False)
        app.skywardUsername = None
        app.skywardPassword = None
        clear_all_logins()
    except requests.exceptions.ConnectionError:
        # CONNECTION ERROR:
        app.error_msg_signal.emit('Network error. Please check your internet connection.')
    else:
        # LOGIN SUCCESSFUL:
        app.database_refreshed.emit()
        app.loginLabel.setText(f'Logged in as {user}')
        app.helloUserLabel.setText(f'Hello {user}!')
        # TODO: determine if we should add saving login
        if app.rememberMe:
            save_login(user, pw)
        app.skywardUsername = user
        app.skywardPassword = pw
    app.skywardLoginButton.setEnabled(True)


if __name__ == "__main__":
    save_login("user", 'pass')
    # clear_all_logins()
    print(get_login())

