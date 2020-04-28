from . import BaseInjector

class Software(BaseInjector):

    def __init__(self, job_name, host_group, command, inject_at):
        # self.command = 'pkill -SIGKILL -f ' + service_name
        BaseInjector.__init__(self, job_name, host_group, command, inject_at)