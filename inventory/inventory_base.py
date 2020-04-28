
"""
Base module and class for managing dynamic inventories
We can either use this module and create dynamic
inventories which are well documented or create
inventory plugins as introduced in Ansible 2.4. But,
the inventory plugins are very new and their working is
not very well documented.
"""

# System imports
import json


class InventoryBase(object):

    def __init__(self, config):
        """
        Initialize the dynamic inventory - look at
        Ansible dynamic inventory specifications
        for more details. But at a minimum the _meta
        and hostvars are initialized

        :param config: config data
        :type config: dict
        """

        self.inventory = dict(_meta=dict(hostvars=dict()))
        self.config = config

    def group_exists(self, group_name):
        """
        Check if a group exists in the inventory object
        :param group_name: The group name to check for existence
        :type group_name: str
        :returns: True if the group name exists, False if it doesn't
        :rtype: boolean
        """

        return group_name in self.inventory

    def host_exists(self, host_name):
        """
        Check if a host exists in the inventory hostvars.
        The host_name is the ansible
        alias and not the FQDN or the IP address.
        :param host_name: The host name to check for existence.
        :type host_name: str
        :returns: True if the host_name exists in False if it doesn't
        :rtype: boolean
        """

        return host_name in self.inventory['_meta']['hostvars']

    def add_group(self, group_name):
        """
        Add a group to the inventory. The group will be added
        with empty hosts, vars and children nodes.
        The group will not be added if the group already exists.
        :param group_name: The group name to add to the inventory
        :type group_name: str
        :returns: None
        """

        # Use a set instead of a list
        # This will provide efficiency O(1) for the hash set
        # vs O(n) for list when managing large inventories
        if self.group_exists(group_name) is False:
            self.inventory[group_name] = dict(hosts=set(),
                                              vars=dict(),
                                              children=set())

    def add_host(self, host_name):
        """
        Add a host to _meta.hostvars only if the host
        doesn't already exist. The host alias to add is
        always the ansible host alias or name not the FQDN
        or IP address.
        :param host_name: The host to add to the inventory
        :type host_name: str
        :returns: None
        """

        if self.host_exists(host_name) is False:
            self.inventory['_meta']['hostvars'][host_name] = dict()

    def add_host_to_group(self, group_name, host_name):
        """
        Add a host to a group, i.e. insert the host into
        the group.hosts array/set.
        :param group_name: Group name where the host is to be added
        :param host_name: The host name to be added into the group
        :type group_name: str
        :type host_name: str
        :returns: None
        :raises ValueError: If the group_name or the host_name \
                do not exist
        """

        if (self.group_exists(group_name) is True and
                self.host_exists(host_name) is True):
            self.inventory[group_name]['hosts'].add(host_name)
        else:
            raise ValueError('Group %s and Host %s should be present' %
                             (group_name, host_name))

    def add_var_to_host(self, host_name, var, val=''):
        """
        Add a variable to the list/set of host variables
        in the _meta.hostvars structure
        This can be used to modify the variable value as well
        :param host_name: The host name to add the variable to
        :param var: The variable name
        :param val: The variable value
        :type host_name: str
        :type var: str
        :type val: str optional
        :returns: None
        :raises ValueError: If the host_name is not in the inventory
        """

        if self.host_exists(host_name) is False:
            raise ValueError('%s is not in the _meta structure' % host_name)
        else:
            self.inventory['_meta']['hostvars'][host_name][var] = val

    def add_var_to_group(self, group_name, var, val=''):
        """
        Add a variable to a group in the inventory. The
        call will modify the variable
        value if the variable already exists
        :param group_name: The group name to add the variable to
        :param var: The variable name
        :param val: The value of the variable
        :type group_name: str
        :type var: str
        :type val: str optional
        :returns: None
        :raises ValueError: If the group_name does not exist
        """

        if self.group_exists(group_name) is False:
            raise ValueError('%s is not present' % group_name)
        else:
            self.inventory[group_name]['vars'][var] = val

    def add_child_to_group(self, group_name, child_name):
        """
        Add a child to a group - this is used to build
        a hierarchy of groups and useful in representing
        a data center type graph/tree
        :param group_name: The group name to add the child to
        :param child_name: The child group to add to group_name
        :type group_name: str
        :type child_name: str
        :returns: None
        :raises ValueError: If either group_name or child_name \
                are not groups already
        """

        if (self.group_exists(group_name) is True and
                self.group_exists(child_name) is True):
            self.inventory[group_name]['children'].add(child_name)
        else:
            raise ValueError('Groups %s and child %s should be present' %
                             (group_name, child_name))

    def serialize_to_json(self):
        """
        Serialize the inventory to a JSON string
        :returns: The JSON string which represents a dynamic ansible inventory
        :rtype: str
        :raises TypeError: If the object or parts of the \
                inventory object are not serializable to JSON
        """

        # The only non json serializable element is the set
        # for which the default is provided by overriding
        # the encoder class.
        class InventoryEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, set):
                    return list(obj)
                else:
                    return super(InventoryEncoder, self).default(obj)

        return json.dumps(self.inventory,
                          cls=InventoryEncoder,
                          indent=4,
                          sort_keys=True,
                          separators=(',', ': '))

    def create_inventory(self):
        """
        Method to override in subclass implementations
        to create an inventory object with the functions
        provided.
        """

        pass
