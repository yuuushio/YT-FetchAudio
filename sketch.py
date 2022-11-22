import os
import yaml

class Config:
    """
    Class to read config file.
    """

    # This will make it so that the user doesn't have to input the
    # output directory each time the app is run; the app will fetch 
    # it from the config file instead.

    def __init__(self):
        self._data = ""
        self._read_config_file()

    @property
    def directory(self):
        return self._data

    @directory.setter
    def directory(self, v):
        self._data = v

    def _read_config_file(self):
        with open("config.yml", "r") as f:
            yml_data = yaml.safe_load(f)

        print(yml_data["colors"])
        # `expanduser` used to expand paths containing tilde
        if os.path.exists(os.path.expanduser(yml_data["directory"])):
            self.directory = os.path.expanduser(yml_data["directory"])
        else:
            self.directory = ""


cfg = Config()
cfg._read_config_file()

