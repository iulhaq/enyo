import os
import json
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from enyo.utils.custom_logger import CustomLogger
from enyo.config import Config
from enyo.utils import Utils

config = Config()
LOG_FILE = os.path.join(config.get_value('log_dir'), 'rally-reporter.log')
logger = CustomLogger(LOG_FILE, name=__name__)

class RallyReporter():

    def __init__(self, input_file):
        self.input_file = input_file
        self.output_graph = input_file + '.pdf'


    def plot(self, data):
        if (len(data.keys())==0):
            logger.info("Empty data, nothing to plot")
            return

        try:
            # getting the specific data from the data generated by rally
            results = data['tasks'][0]['subtasks'][0]['workloads'][0]['data']
        except Exception as exception:
            logger.error("Error occured while reading rally report: %s",
                         exception)
            return

        min_timestamp = results[0]['timestamp']
        timestamp = [r['timestamp']-min_timestamp for r in results]
        boot_and_delete =  [r['duration'] for r in results]

        error_timestamp = [r['timestamp']-min_timestamp for r in results if len(r['error'])!=0]
        error_boot_and_delete =  [r['duration'] for r in results if len(r['error'])!=0]

        plt.plot(timestamp, boot_and_delete, 'o-', color='deepskyblue')
        plt.scatter(error_timestamp, error_boot_and_delete, color='orangered', zorder=10)

        plt.xlabel('Time (seconds)')
        plt.ylabel('Provisioning Duration (seconds)')
        plt.tight_layout()

        plt.savefig(self.output_graph)
        plt.clf()


    def _create_graph(self):
        try:
            data = Utils.read_json_file(self.input_file)
            self.plot(data)
        except Exception as exception:
            logger.error("Error occured during creation of graphical report: %s",
                         exception)


    def generate_report(self):
        self._create_graph()
