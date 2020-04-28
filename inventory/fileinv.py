import json

from inventory_base import InventoryBase


class AnsibleInventory(InventoryBase):

    def __init__(self, config):
        """
        Create the  File Inventory from various parameters
        for rally and a deployment map.
        :param config: The config file as a dictionary
        :type config: dict
        """

        super(AnsibleInventory, self).__init__(config)

    def _load_deployment_map(self):
        """
        Load a site deployment map. The site deployment is
        in the following configuration
        {
            "name": "host_alias",
            "groups": ["group1", "group2",...],
            "ip": "actual.ip.addr.here",
            "mac": "mac:for:the:ip:addr:here",
            "type": "vm" or "bare-metal" or "rack" or "switch" or "router"
            "bare-metal": "bare-metal-name-if-type-is-vm",
            "rack": "rack-name-if-type-is-metal"
            "ansible_ssh_variables": {
                Look at Ansible inventory documentation
                Provide these if you want to override defaults
                in the inv_config
            }
        }

        :returns: List of dict objects
        :rtype: list
        :raises ValueError: Thrown when parsing JSON
        :raises TypeError: Thrown when parsing JSON
        :raises IOError: Thrown for error reading file
        """

        deployment_map = None
        map_loc = self.config['openstack_deployment']['deployment_map']
        with open(map_loc, 'r') as fid:
            deployment_map = json.load(fid)

        return deployment_map

    def create_inventory(self):
        """
        Create the entire inventory from the config
        and the deployment map.
        """
        # Process other keys first
        for key, val in self.config.items():
            if key == 'openstack_deployment':
                continue
            else:
                # Add group only if there are variables under the group
                if val is not None:
                    self.add_group(key)
                    for vkey, vval in val.items():
                        self.add_var_to_group(key, vkey, vval)

        # Now process the openstack deployment
        # Load the deployment map
        deployment_map = self._load_deployment_map()

        # Add in the localhost
        self.add_group('local')
        self.add_host('localhost')
        self.add_var_to_host('localhost', 'ansible_host', '127.0.0.1')
        self.add_var_to_host('localhost', 'ansible_become', 'false')
        self.add_var_to_host('localhost', 'ansible_connection', 'local')
        self.add_host_to_group('local', 'localhost')

        # Add in the root group
        # Everything is a part of the root group - or the deployment
        dep_name = self.config['openstack_deployment']['name']
        self.add_group(dep_name)

        # Add in the ssh parameters as a part of the root group
        # !!! Important !!!
        # The ssh parameters have to be Ansible inventory compliant
        # TODO: Test this
        # TODO: Refactor when aggregate modifications are implemented
        # in InventoryBase
        dep_ssh = self.config['openstack_deployment']['deployment_ssh']
        for ansible_inv_ssh_var, ansible_inv_ssh_val in dep_ssh.items():
            self.add_var_to_group(dep_name,
                                  ansible_inv_ssh_var,
                                  ansible_inv_ssh_val)

        groups_and_hosts = self._add_hosts_to_inventory(deployment_map)
        group_expansion = self.config['openstack_deployment']['groups']
        self._create_group_hierarchy(dep_name,
                                     group_expansion,
                                     groups_and_hosts)

    def _create_group_hierarchy(self, dep_name,
                                group_expansion,
                                groups_and_hosts):
        """
        Private method
        DO NOT CALL EXTERNALLY

        Create a group hierarchy and add the hosts to the inventory.

        :param dep_name: The root group
        :param group_expansion: Aggregate group expansions
        :param groups_and_hosts: Groups and hosts from deployment map
        :type dep_name: str
        :type group_expansion: dict
        :type groups_and_hosts: dict
        :returns: None
        """

        # Add in all the children from the service expansion pieces
        # These are the groups that you want to logically club
        # together
        # FIXME: Yuck - an O(n^3) algorithm. Look for efficiency
        for group, hlist in groups_and_hosts.items():
            if group in group_expansion:
                # A whole bunch of processing

                group_list = group_expansion[group]

                # Add the parent group
                self.add_group(group)
                self.add_child_to_group(dep_name, group)

                # Add the group_list
                for l_group in group_list:
                    self.add_group(l_group)
                    self.add_child_to_group(group, l_group)

                    # Add all the hosts to l_group
                    for l_host in hlist:
                        self.add_host_to_group(l_group, l_host)
            else:
                # A standalong group with a bunch of hosts

                # Add in the group
                self.add_group(group)
                self.add_child_to_group(dep_name, group)

                # Then add the hosts
                for host in hlist:
                    self.add_host_to_group(group, host)

    def _add_hosts_to_inventory(self, deployment_map):
        """
        Private method
        DO NOT CALL EXTERNALLY

        Add hosts to the inventory from the deployment map

        :param deployment_map: The deployment map from the config
        :type deployment_map: list
        :returns: A dictionary of hosts and group from the deployment
        :rtype: dict
        """

        # TODO: Add code for auto creating groups for racks and bare metal
        # Process the deployment map
        groups_and_hosts = dict()
        for node in deployment_map:
            # First add to the hosts
            hostname = node['name']
            self.add_host(hostname)

            # Then keep a track of the groups and hosts
            for group in node['groups']:
                if group in groups_and_hosts:
                    groups_and_hosts[group].append(hostname)
                else:
                    groups_and_hosts[group] = list([hostname, ])

            # Then add in the ansible ssh variables
            # ip maps to ansible_host
            # mac doesn't map to anything - it's just a variable
            # The rest of the variables are in ansible_ssh_variables
            self.add_var_to_host(hostname, 'ansible_host', node['ip'])
            self.add_var_to_host(hostname, 'mac', node['mac'])
            if 'ansible_ssh_variables' in node:
                ansible_ssh_vars = node['ansible_ssh_variables']
                for ansible_ssh_var, ansible_ssh_val in ansible_ssh_vars.items():
                    self.add_var_to_host(hostname,
                                         ansible_ssh_var,
                                         ansible_ssh_val)

        return groups_and_hosts
