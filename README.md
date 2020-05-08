# Enyo

Framework for testing High Availability of Openstack Cloud



## Getting Started
 
- Install [Rally](https://github.com/openstack/rally) and [Shaker](https://opendev.org/performa/shaker) and make sure they can run
- `git clone https://github.com/iulhaq/enyo.git`
- `pip install -r src/requirements3.txt`
- Update `config/deployment_map.json` according to your OpenStack setup
- Source admin OpenStack RC file `source admin-openstack.rc` 
- Set config file in environment variable `export ENYO_CONFIG_FILE=~/enyo/config/config.json`
- Run test scenario 
  ```
  cd src
  python -m enyo.cli.runner -s ~/enyo/tests/scenarios/scenario_nova.yaml
  ```
