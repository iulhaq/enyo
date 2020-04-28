import os
from threading import Thread
import logging
import sys

from rally.cli.commands.task import TaskCommands
from rally.plugins import load as load_plugins
from rally.api import API
from rally.cli.commands.deployment import DeploymentCommands
from rally.plugins import load as load_plugins
from rally.exceptions import DBRecordNotFound

from enyo.config import Config
from . import BaseLoader
from enyo.utils.custom_logger import CustomLogger, DEFAULT_LOG_FORMAT
from enyo.reporters.rally import RallyReporter


config = Config()
LOG_FILE = os.path.join(config.get_value('log_dir'), 'loader-rally.log')
logger = CustomLogger(LOG_FILE, name=__name__)

RALLY_LOG_FILE = os.path.join(config.get_value('log_dir'), 'rally/task.log')


class Rally(BaseLoader):

    def __init__(self, task_file, deployment=None, task_args=None, task_args_file=None, config_file=None):
        self.rally_api = API()
        self._modify_logger()
        self.task = TaskCommands()
        self.task_init_timeout = 200
        self.deployment_name = deployment
        self.task_file = task_file

        self.task_thread = Thread(target=self.run)

        self.create_or_use_deployment()
        self.input_task = self.task._load_and_validate_task(self.rally_api, self.task_file,
                                                            raw_args=task_args,
                                                            args_file=task_args_file)
        self.task_instance = self.rally_api.task.create(deployment=self.deployment_name)
        self.task_id = self.task_instance["uuid"]

    def validate(self):
        print(self.task.validate(self.rally_api, self.task_file, self.deployment_name))

    def start(self):
        logger.info("Starting thread for rally task")
        self.task_thread.start()

    def run(self):
        self.rally_api.task.start(deployment=self.deployment_name, config=self.input_task,
                             task=self.task_id)

    def stop(self):
        self.task.abort(self.rally_api, task_id=self.task_id)

    def task_status(self):
        task = self.rally_api.task.get(self.task_id)
        return task["status"]

    def deployment_status(self):
        deployment = self.rally_api.deployment.get(self.deployment_name)
        return deployment["status"]

    def wait_to_finish(self):
        logger.info("Waiting for rally thread to join")
        self.task_thread.join()
        logger.info("Finished rally thread")

    def generate_report(self, output_file):
        logger.info("Generating report")
        output_html = output_file + ".html"
        output_json = output_file + ".json"
        self.task.report(self.rally_api, self.task_id, out=output_html, out_format="html")
        self.task.report(self.rally_api, self.task_id, out=output_json, out_format="json")

        report = RallyReporter(output_json)
        report.generate_report()
        logger.info("Report generated")

    def create_or_use_deployment(self):
        load_plugins()

        try:
            self.rally_api.deployment.get(self.deployment_name)
        except DBRecordNotFound:
            return DeploymentCommands().create(self.rally_api, self.deployment_name, fromenv=True)

    def destroy_deployment(self):
        self.rally_api.deployment.destroy(self.deployment_name)

    def _modify_logger(self):
        '''
            Modify rally library logger to our requirments
        '''
        rally_logger = logging.getLogger("rally")
        console_handler = logging.StreamHandler(sys.stdout)
        rally_logger.removeHandler(console_handler)
        file_handler = logging.FileHandler(RALLY_LOG_FILE)
        formatter  = logging.Formatter(DEFAULT_LOG_FORMAT)
        file_handler.setFormatter(formatter)
        rally_logger.addHandler(file_handler)
        rally_logger.propagate = False
