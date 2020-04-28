from . import BaseInjector

class Hardware(BaseInjector):

    def __init__(self, job_name, host_group, command, inject_at):
        BaseInjector.__init__(self, job_name, host_group, command, inject_at)