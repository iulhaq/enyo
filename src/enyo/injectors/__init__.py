import os
from threading import Timer
import logging

from enyo.config import Config
from enyo.utils.ansible_api import Task, AnsibleRunner
from enyo.utils.custom_logger import CustomLogger

config = Config()
LOG_FILE = os.path.join(config.get_value('log_dir'), 'injectors.log')
logger = CustomLogger(LOG_FILE, name=__name__)

class BaseInjector(object):

    def __init__(self, job_name, host, command, inject_at):
        self.job_name = job_name
        self.host = host
        self.command = command
        self.inject_at = inject_at
        self.injection_thread = Timer(self.inject_at, self.__execute__)

    def inject(self):
        logger.info("Running injection after %s seconds", str(self.inject_at))
        self.injection_thread.start()

    def wait_to_finish(self):
        logger.info("Waiting for injection thread to join")
        self.injection_thread.join()
        logger.info("Finished injection thread")

    def __execute__(self):
        logger.info("Injecting : %s", str(self.command))
        injection_task = Task("shell", self.command).get_dict()
        runner = AnsibleRunner(self.job_name, logger)
        runner.run(self.host, [injection_task])
        logger.info("Finished injection")
