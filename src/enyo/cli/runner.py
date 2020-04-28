
import os, sys
import argparse
from threading import Thread, Event
import logging
import time
import yaml

from enyo.workloaders.rally import Rally
from enyo.workloaders.shaker import Shaker
from rally.api import API
from rally.cli.commands.deployment import DeploymentCommands
from enyo.injectors.software import Software
from enyo.injectors.hardware import Hardware
from enyo.injectors.network import Network
from enyo.monitors import BaseMonitor
from enyo.reporters.recovery import RecoveryReporter
from enyo.utils.custom_logger import CustomLogger
from enyo.config import Config

config = Config()
LOG_FILE = os.path.join(config.get_value('log_dir'), 'main.log')
logger = CustomLogger(LOG_FILE, console=True, name=__name__)
logger.setLevel(3)

class ScenarioRunner(object):

    def __init__(self, scenario_file):
        self.loader = None
        self.injection = None
        self.stop_monitors_flag = Event()
        self.scenario = self.read_scenario(scenario_file)
        self.injectors = []
        self.monitors = []


    def start_loaders(self):
        '''
            Start the work load
        '''
        logger.info('Starting workload')
        loader_config = self.scenario['loader']

        if(loader_config==None):
            logger.info("No work loader specified")
            return
        if loader_config['type']=="rally":
            self.loader = Rally(loader_config['scenario_file'], loader_config['deployment_name'])
        elif loader_config['type']=="shaker":
            self.loader = Shaker(loader_config['host_ip'], loader_config['scenario_file'],
                                 loader_config['report_file'], loader_config['log_file'])
        self.loader.start()


    def start_injectors(self):
        '''
            Loop through all injectors and create objects and start
            in seperate threads based on their timers
        '''
        logger.info('Setting up injectors')
        if(self.scenario['injectors']==None):
            logger.info("No injectors specified")
            return

        for injector in self.scenario['injectors']:
            if injector['type'] == 'software':
                self.injectors.append(Software(injector['name'], injector['host'],
                                               injector['command'], injector['time']))
            if injector['type'] == 'hardware':
                self.injectors.append(Hardware(injector['name'], injector['host'],
                                               injector['command'], injector['time']))
            if injector['type'] == 'network':
                self.injectors.append(Network(injector['name'], injector['host'],
                                              injector['command'], injector['time']))

        logger.debug(self.loader.deployment_status())
        logger.info('Waiting for the workload task to initialize ...')

        timeout = 0
        failure = False
        while(self.loader.task_init_timeout>timeout):
            if(self.loader.task_status()=="running"):
                break
            elif(self.loader.task_status()=="failed"):
                failure = True
                break
            logger.info('Work loader task status: %s', self.loader.task_status())
            time.sleep(1)
            timeout += 1

        if(timeout>self.loader.task_init_timeout or failure):
            logger.info('Failed to initialize work load task. Aborting injectors.')
            return

        logger.info('Work load task started. Ready to inject')

        list(map(lambda i: i.inject(), self.injectors))


    def start_monitors(self):
        '''
            Loop through all monitors and create objects and start
            in seperate threads based on their timers
        '''
        logger.info('Starting monitors')
        if(self.scenario['monitors']==None):
            logger.info("No monitors specified")
            return

        for monitor in self.scenario['monitors']:
            self.monitors.append(BaseMonitor(monitor['name'], monitor['host'], monitor['command'],
                                             monitor['interval'], monitor['output'],
                                             self.stop_monitors_flag))

        list(map(lambda m: m.start(), self.monitors))


    def stop_monitors(self):
        logger.info('Stopping monitors')
        self.stop_monitors_flag.set()


    def wait_workers(self):
        logger.info("Waiting for workers to finish")
        map(lambda i: i.wait_to_finish(), self.injectors)
        self.loader.wait_to_finish()
        self.stop_monitors()


    def generate_reports(self):
        logger.info("Generating report")
        # generate report from workload
        self.loader.generate_report(self.scenario['loader']['report_file'])

        # generate report from monitors
        for monitor in self.scenario['monitors']:
            report = RecoveryReporter(monitor['output'])
            report.generate_report()

    def read_scenario(self, file):
        with open(file, 'r') as stream:
            try:
                scenario = yaml.safe_load(stream)
            except yaml.YAMLError as ex:
                logger.error(ex)

        return scenario

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enyo")
    parser.add_argument('-s', '--scenario', required=True, help="Scenario file to be passed")
    args = parser.parse_args()
    if os.path.exists(args.scenario):
        logger.info('Starting the scenario')
        scenario = ScenarioRunner(args.scenario)
        scenario.start_loaders()
        scenario.start_injectors()
        scenario.start_monitors()
        scenario.wait_workers()
        scenario.generate_reports()
        logger.info('Finished!')
    else:
        print("Scenario file not found")

