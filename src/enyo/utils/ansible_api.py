#!/usr/bin/env python
import os
import json
import shutil
import logging

from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C

from enyo.config import Config
from enyo.utils.custom_logger import CustomLogger

ENYO_BIN_DIR = "/home/ihti/thesis/code/enyo/inventory/"
config = Config()

class ResultsCollector(CallbackBase):
  def __init__(self, job_name, logger, *args, **kwargs):
    super(ResultsCollector, self).__init__(*args, **kwargs)
    self.hosts = []
    self.logger = logger
    self.job_name = job_name

  def v2_runner_on_unreachable(self, result, ignore_errors=False):
    result_json = {
                    'job_name': self.job_name,
                    'time': result._result['end'],
                    'host': result._host.get_name(),
                    'output': 'Host unreachable',
                    'error' : result._result['stderr'],
                    'success': False
                  }
    self.hosts.append(result_json)
    self.logger.info(json.dumps(result_json, indent=4))

  def v2_runner_on_ok(self, result):
    result_json = {
                    'job_name': self.job_name,
                    'time':result._result['end'],
                    'host':result._host.get_name(),
                    'command': result._result['cmd'],
                    'return_code': result._result['rc'],
                    'output': result._result['stdout'],
                    'success':True
                  }
    self.hosts.append(result_json)
    self.logger.info(json.dumps(result_json, indent=4))

  def v2_runner_on_failed(self, result, ignore_errors=False):
    result_json = {
                    'job_name': self.job_name,
                    'time':result._result['end'],
                    'host':result._host.get_name(),
                    'command': result._result['cmd'],
                    'return_code': result._result['rc'],
                    'output': result._result['stdout'],
                    'error' : result._result['stderr'],
                    'success':False
                  }
    self.hosts.append(result_json)
    self.logger.info(json.dumps(result_json, indent=4))

  def get(self):
    return self.hosts

class AnsibleRunner():

    def __init__(self, job_name, logger , inventory=config.get_value('inventory_file')):
        # since the API is constructed for CLI it expects certain options to always be set in the context object
        context.CLIARGS = ImmutableDict(connection='smart', module_path=['/to/mymodules'], forks=10, become=None,
                                        become_method=None, become_user=None, check=False, diff=False,
                                        extra_vars=dict(), verbosity=3)

        # initialize needed objects
        self.loader = DataLoader() # Takes care of finding and reading yaml, json and ini files
        self.passwords = dict(vault_pass='secret')

        # Instantiate our ResultCallback for handling results as they come in. Ansible expects this to be one of its main display outlets
        # Move it to run?
        self.results_callback = ResultsCollector(job_name, logger)

        # create inventory, use path to host config file as source or hosts in a comma separated string
        self.inventory = InventoryManager(loader=self.loader, sources=inventory)

        # variable manager takes care of merging all the different sources to give you a unified view of variables available in each context
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

    def run(self, hosts, tasks):
        # create data structure that represents our play, including tasks, this is basically what our YAML loader does internally.
        play_source =  dict(
                name = "Test Playbook",
                hosts = hosts,
                gather_facts = 'no',
                tasks = tasks
            )

        # Create play object, playbook objects use .load instead of init or new methods,
        # this will also automatically create the task objects from the info provided in play_source
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        # Run it - instantiate task queue manager, which takes care of forking and setting up all objects to iterate over host list and tasks
        tqm = None
        try:
            tqm = TaskQueueManager(
                    inventory=self.inventory,
                    variable_manager=self.variable_manager,
                    loader=self.loader,
                    passwords=self.passwords,
                    stdout_callback=self.results_callback,  # Use our custom callback instead of the ``default`` callback plugin, which prints to stdout
                )
            result = tqm.run(play) # most interesting data for a play is actually sent to the callback's methods
        finally:
            # we always need to cleanup child procs and the structures we use to communicate with them
            if tqm is not None:
                tqm.cleanup()

            # Remove ansible tmpdir
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

class Task():
    def __init__(self, module_name, module_args, **kwargs):
        self.module_name = module_name
        self.module_args = module_args
        self.kwargs = kwargs

    def get_dict(self):
        action = dict(action=dict(module=self.module_name, args=self.module_args))
        action.update(self.kwargs)
        return action