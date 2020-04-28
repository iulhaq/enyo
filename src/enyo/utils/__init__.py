import json

class Utils():
    @staticmethod
    def read_json_file(file):
        with open(file) as json_file :
            data = json.load(json_file)
        return data