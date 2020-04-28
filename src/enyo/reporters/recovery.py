import os
import json
import fileinput
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from enyo.utils.custom_logger import CustomLogger
from enyo.config import Config
from enyo.utils import Utils

config = Config()
LOG_FILE = os.path.join(config.get_value('log_dir'), 'report.log')
logger = CustomLogger(LOG_FILE, name=__name__)
TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

class RecoveryReporter():

    def __init__(self, input_file):
        self.input_file = input_file
        self.output_file = input_file + '.out'
        self.output_graph = input_file + '.png'

    def _get_json(self, file):
        '''
            Convert file's data to json list

        file: file containing json appended data created by the monitors
        '''
        with open(file, 'r') as f :
            filedata = f.read()
        filedata = filedata.replace('}\n{', '},{')
        return json.loads('[' + filedata + ']')

    def _get_result_for_hosts(self, results):
        '''
            Split results for by hosts
        '''
        sorted_by_host = sorted(results, key=lambda x:x['host'])
        all_results = []
        result_from_host = []
        previous = None
        for result in sorted_by_host:
            if result['host'] != previous:
                if(len(result_from_host)!=0):
                    all_results.append(result_from_host)
                result_from_host = [result]
                previous = result['host']
            else:
                result_from_host.append(result)
        all_results.append(result_from_host)

        return all_results

    def _get_recovery_time(self, results):
        '''
            result: monitoring results of the same host and monitor
            recovery_times: returns list of all the recovery times during the
            monitoring
        '''
        results = sorted(results, key=lambda x:x['time'])
        recovery_times = []
        previous_rc = 0
        for result in results:
            if result['return_code'] > 0 and previous_rc == 0:
                failure_time = datetime.strptime(result['time'], TIME_FORMAT)
                previous_rc = 1
            elif result['return_code'] == 0 and previous_rc > 0:
                up_time = datetime.strptime(result['time'], TIME_FORMAT)
                previous_rc = 0
                recovery_time = (up_time-failure_time).total_seconds()
                recovery_times.append(recovery_time)

        # only getting the last one
        if (len(recovery_times)>0):
            return recovery_times[len(recovery_times)-1]
        else:
            return None


    def _write_to_file(self, recovery_times):
        with open(self.output_file, 'w') as f:
            json.dump(recovery_times, f)


    def plot_recovery_times_plot(self, data):
        if (len(data.keys())==0):
            logger.info("Empty data, nothing to plot")
            return

        nodes = [i.split('.')[0] for i in data.keys()]
        recovery_times = [data[t] for t in data.keys()]
        x_pos = np.arange(len(nodes))

        plt.bar(x_pos, recovery_times, align='center', alpha=0.5)

        plt.xticks(x_pos, nodes, rotation=45, ha="right")

        plt.xlabel('Nodes')
        plt.ylabel('Time to recover (seconds)')
        plt.tight_layout()

        plt.savefig(self.output_graph)
        plt.clf()


    def _create_graph(self):
        try:
            data = Utils.read_json_file(self.output_file)
            self.plot_recovery_times_plot(data)
        except Exception as exception:
            logger.error("Error occured during creation of graphical report: %s",
                         exception)


    def generate_time_vs_recovery_report(self):
        monitor_data = self._get_json(self.input_file)
        if(len(monitor_data)==0):
            logger.info("No monitoring data found. No report to generate.")
            return

        results_by_host = self._get_result_for_hosts(monitor_data)
        all_recovery_times = {}
        for single_host_results in results_by_host:
            recovery_time = self._get_recovery_time(single_host_results)
            if(recovery_time):
                all_recovery_times[single_host_results[1]['host']] = recovery_time

        logger.info("%s services recoverd", len(all_recovery_times))
        logger.info("Writing results to file")
        self._write_to_file(all_recovery_times)
        self._create_graph()

    def generate_report(self):
        logger.info("Generating report")
        self.generate_time_vs_recovery_report()

