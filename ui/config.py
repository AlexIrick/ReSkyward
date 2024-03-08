from pyqtconfig import ConfigManager


class Config:
    def __init__(self, app):
        self.config = ConfigManager(filename="/user/settings_config.json")
        self.config.set_defaults(
            {
                'hideCitizen': False,
                'refreshOnLaunch': False,
                'lastRefreshed': None,
                'bellIDs': [None, None, None],
            }
        )
        self.app = app

    def load(self):
        # TODO
        hide_citizen = self.get('hideCitizen')
        self.app.citizenCard.setChecked(hide_citizen)
        self.app.get_skyward_view().hide_skyward_table_columns(hide_citizen)

        # self.app.ref_on_launch = self.config.get('refreshOnLaunch')
        # self.app.refreshOnLaunchCheck.setChecked(self.app.ref_on_launch)

        # bell_ids = self.config.get('bellIDs')
        # if bell_ids is not None and bell_ids[0] is not None:
        #     self.app.bellUI.set_bell_ids(bell_ids)


    def save(self):
        self.config.save()
        
    def get(self, name: str):
        return self.config.get(name)

    def set_hide_citizen(self, hide_citizen: bool):
        self.config.set('hideCitizen', hide_citizen)
        self.save()
        self.app.get_skyward_view().hide_skyward_table_columns(hide_citizen)

        # self.app.hideCitizen = hide_citizen
        
    def get_hide_citizen(self):
        self.config.get('hideCitizen')

    def set_refresh_on_launch(self, ref_on_launch: bool):
        self.config.set('refreshOnLaunch', ref_on_launch)
        self.save()

        self.app.ref_on_launch = ref_on_launch

    def set_bell_schedule_ids(self, bell_ids):
        self.config.set('bellIDs', bell_ids)
        self.save()
