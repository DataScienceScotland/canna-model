import yaml
import json
import os

class ImportConfig:

    def __init__(self, config_name):
        file_path = "modellingvfm/configs"
        self.config_path = file_path + "/" + config_name + '.yaml'

    def get_yaml_config(self) -> object:

        with open(self.config_path, 'r') as f:
            config_to_return = yaml.safe_load(f)

        return config_to_return

    def get_json_config(self):
        with open(self.config_path, 'r') as f:
            config_to_return = json.load(f)

        return config_to_return
