#! /usr/bin/env python

import json
import sys
import os
import importlib

DEFAULT_INVENTORY = 'fileinv'
INVENTORY_CLASS = 'AnsibleInventory'

ENYO_INVENTORY_CONFIG = '/home/ihti/thesis/code/enyo/config/inventory_config.json'

def main(argv):
    """
    The main inventory executable script. The argv
    for all practical purposes is sys.argv

    :param argv: An argument list
    :type argv: list
    :returns: The dynamic inventory json
    :rtype: str
    :raises ValueError: if the argv is incorrect \
            or if the JSON cannot be parsed
    :raises TypeError: if the inventory plugin is invalid
    :raises IOError: if there an issue with config files
    """

    # The argv is in reality just the sys.argv. However, when
    # testing modifying sys.argv could get a bit dicey because
    # of runtime modification of system variables. Hence, use
    # argv as a parameter to main. The tests can then pass in
    # sys.argv like list.

    # Do we have the correct arguments?
    # 1 argument that is named --list - according to Ansible dynamic inventory
    # guidelines. Do not support the --host argument. The inventory plugins are
    # supposed to populate the _meta.hostvars structure so that --host calls
    # are not needed.
    if argv is None or len(argv) != 2 or argv[1] != '--list':
        raise ValueError('Incorrect argv passed')

    # Get the environment variable and check if its present
    config_file = ENYO_INVENTORY_CONFIG
    if config_file is None:
        raise ValueError('ENYO_INVENTORY_CONFIG is None')

    # Check if the file is readable
    if os.access(config_file, os.R_OK) is False:
        raise IOError('%s is not readable' % config_file)

    # Check if the path is a file
    if os.path.isfile(config_file) is False:
        raise IOError('%s is not a file' % config_file)

    # Read the config into a dictionary
    config = None
    with open(config_file, 'r') as fid:
        config = json.load(fid)

    # Default plugin is the fileinv
    inventory_plugin = DEFAULT_INVENTORY
    if 'inventory_plugin' in config:
        inventory_plugin = config['inventory_plugin']
    config.pop('inventory_plugin', None)

    # Get the class and create the object
    inventory_mod = importlib.import_module(inventory_plugin)
    inventory_cls = getattr(inventory_mod, INVENTORY_CLASS)
    inventory_obj = inventory_cls(config)

    # Create the inventory and serialize
    inventory_obj.create_inventory()
    inventory_json = inventory_obj.serialize_to_json()

    # Phew - finally we return this
    return inventory_json


# Main entry point for the script execution
if __name__ == '__main__':
    print(main(sys.argv))
