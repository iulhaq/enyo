
import os
from threading import Timer, Thread

from enyo.config import Config
from enyo.utils.ansible_api import Task, AnsibleRunner
from enyo.utils.custom_logger import CustomLogger

config = Config()
LOG_FILE = os.path.join(config.get_value('log_dir'), 'monitors.log')
logger = CustomLogger(LOG_FILE, name=__name__)

class BaseMonitor(Thread):

    def __init__(self, job_name, host, command, interval, output, stop_event):
        Thread.__init__(self)
        self.job_name = job_name
        self.host = host
        self.command = command
        self.interval = interval
        self.stopped = stop_event
        self.monitoring_log = CustomLogger(output,
                                           log_format='%(message)s',
                                           name=job_name)

    def run(self):
        logger.info("Running %s monitor every %s seconds", self.name, str(self.interval))
        while not self.stopped.wait(self.interval):
            self.__execute__()

    def __execute__(self):
        logger.debug("Running %s for monitoring on host %s", self.command, self.host)
        injection_task = Task("shell", self.command).get_dict()
        runner = AnsibleRunner(self.job_name, self.monitoring_log)
        runner.run(self.host, [injection_task])