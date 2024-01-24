from pyqtconfig import ConfigManager


class Config:
    def __init__(self, app):
        self.config = ConfigManager(filename="ReSkyward/user/settings_config.json")
        self.config.set_defaults({
            'hideCitizen': False,
            'bell_ids': [None, None, None],
        })
        self.app = app
        self.load()

    def load(self):
        self.app.hideCitizen = self.config.get('hideCitizen')
        self.app.hideCitizenCheck.setChecked(self.app.hideCitizen)

        bell_ids = self.config.get('bell_ids')
        if bell_ids[0] is not None:
            self.app.bellUI.set_bell_ids(bell_ids)

    def save(self):
        self.config.save()

    def set_hide_citizen(self, hide_citizen: bool):
        self.config.set('hideCitizen', hide_citizen)
        self.save()

        self.app.hideCitizen = hide_citizen

    def set_bell_schedule_ids(self, bell_ids):
        self.config.set('bell_ids', bell_ids)
        self.save()

