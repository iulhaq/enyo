import subprocess
import time

from . import BaseLoader

#TODO Add logger
class Shaker(BaseLoader):

    def __init__(self, server_endpoint, scenario_file, report_file, log_file):
        self.server_endpoint = server_endpoint
        self.scenario_file = scenario_file
        self.report_file = report_file
        self.task_init_timeout = 900
        self._deployment_status = False
        self.shaker_task = None
        self.log_file = log_file
        self.logger = open(log_file, 'a')


    def start(self):
        self._deployment_status = True
        shaker_cmd = ['shaker', '--server-endpoint', self.server_endpoint,
                      '--scenario', self.scenario_file, '--report', self.report_file]
        self.shaker_task = subprocess.Popen(shaker_cmd, stdout=self.logger, stderr=self.logger)


    def wait_to_finish(self):
        self.shaker_task.wait()


    def generate_report(self, output_file):
        pass


    def stop(self):
        self.shaker_task.terminate()


    def deployment_status(self):
        return self._deployment_status


    def _follow_file(self, filename):
        filename.seek(0,2)
        while True:
            line = filename.readline()
            yield line

    def task_status(self):
        '''
            Currently there is no shaker API which can return status of the task
            so checking the log file for specific string to know if the task
            initialization is completed and actual workload is ready to run
        '''
        task_init_finished = "Finished processing operation: <shaker.engine.quorum.JoinOperation"
        logfile = open(self.log_file,"r")
        loglines = self._follow_file(logfile)
        for line in loglines:
            if not line:
                time.sleep(0.1)
                continue
            elif(task_init_finished in line):
                return "running"
            elif("ERROR" in line):
                return "failed"


    def status(self):
        return self.shaker_task.poll()

