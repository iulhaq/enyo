import os
import json

CONFIG_FILE = os.environ['ENYO_CONFIG_FILE']

class Config():

    def __init__(self):
        with open(CONFIG_FILE, 'r') as f :
            self._cfg = json.loads(f.read())

    def get_value(self, property):
        if property not in self._cfg:
            return None
        return self._cfg[property]