#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
#
# OpenSAND is an emulation testbed aiming to represent in a cost effective way a
# satellite telecommunication system for research and engineering activities.
#
#
# Copyright © 2012 TAS
#
#
# This file is part of the OpenSAND testbed.
#
#
# OpenSAND is free software : you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see http://www.gnu.org/licenses/.
#
#

# Author: Julien BERNARD / <jbernard@toulouse.viveris.com>

"""
opensand_model.py - OpenSAND manager model
"""

import ConfigParser
import os
import shutil

from opensand_manager_core.utils import GreedyConfigParser
from opensand_manager_core.model.environment_plane import SavedProbeLoader
from opensand_manager_core.model.event_manager import EventManager
from opensand_manager_core.model.host import HostModel
from opensand_manager_core.model.global_config import GlobalConfig
from opensand_manager_core.my_exceptions import ModelException, XmlException
from opensand_manager_core.loggers.manager_log import ManagerLog
from opensand_manager_core.opensand_xml_parser import XmlParser
from opensand_manager_gui.view.popup.infos import error_popup
from opensand_manager_core.module import load_modules

MAX_RECENT = 5
DEFAULT_SIMU_FILE = '/usr/share/opensand/simulation_files.ini'

TOPOLOGY_CONF = "topology.conf"
TOPOLOGY_XSD = "topology.xsd"

class Model:
    """ Model for OpenSAND """
    def __init__(self, manager_log, scenario = ''):
        # initialized in load
        self._inifile = None
        self._log = manager_log

        # start event managers
        self._event_manager = EventManager("manager")
        self._event_manager_response = EventManager("response")

        # a list of modules that where not detected by some hosts
        self._missing_modules = {}
        self._scenario_path = scenario
        self._is_default = False
        self._modified = False
        self._run_id = "default"

        # Running in dev mode ?
        self._is_dev_mode = False

        self._hosts = []
        self._ws = []
        self._collector_known = False
        self._collector_functional = False

        # the global config
        self._config = None
        self._deploy_simu = None
        self._topology = None

        # load the global modules
        self._modules = load_modules('global')
        if not 'encap' in self._modules or len(self._modules['encap']) == 0:
            raise ModelException("You need encapsulation modules to use your "
                                 "platform")

        try:
            self.load()
        except ModelException:
            raise

    def load(self):
        """ load the model scenario """
        # load the scenario
        self._is_default = False
        if not 'HOME' in os.environ:
            raise ModelException("cannot get HOME environment variable")

        # no scenario to load use the default path
        if self._scenario_path == "":
            self._scenario_path = os.path.join(os.environ['HOME'],
                                               ".opensand/default")
            self.clean_default()
            self._is_default = True
        else:
            recents = []
            filename = os.path.join(os.environ['HOME'], ".opensand/recent")
            if os.path.exists(filename):
                with open(filename, 'r') as recent_file:
                    for line in recent_file:
                        recents.append(line.strip())

            # remove current path as it will be append at the end
            if os.path.realpath(self._scenario_path) in recents:
                recents.remove(os.path.realpath(self._scenario_path))

            # remove older folders
            while len(recents) > MAX_RECENT - 1:
                recents.pop(len(recents) - 1)

            recents.insert(0, os.path.realpath(self._scenario_path))

            with open(filename, 'w') as recent_file:
                for recent in recents:
                    recent_file.write(recent + '\n')

        # create the scenario path if necessary
        if not os.path.exists(self._scenario_path):
            try:
                os.makedirs(self._scenario_path, 0755)
            except OSError, (errno, strerror):
                raise ModelException("cannot create directory '%s': %s" %
                                     (self._scenario_path, strerror))

        # load the topology configuration
        self.load_topology()

        # actualize the tools scenario path
        for host in self._hosts:
            host.reload_all(self._scenario_path)

        # load modules configuration
        self.reload_modules()

        # load the simulation deployment file
        self.load_simulation()

        # read configuration file
        try:
            self._config = GlobalConfig(self._scenario_path)
        except ModelException:
            raise

    def load_topology(self):
        """ load or reload the topology configuration """
        topo_conf = os.path.join(self._scenario_path, TOPOLOGY_CONF)
        topo_xsd = os.path.join('/usr/share/opensand', TOPOLOGY_XSD)
        try:
            if self._topology is not None:
                # copy the previous topology in the new file
                self._topology.write(topo_conf)
            else:
                # get the default topology file
                default_topo = os.path.join('/usr/share/opensand',
                                            TOPOLOGY_CONF)
                shutil.copy(default_topo, topo_conf)

            self._topology = XmlParser(topo_conf, topo_xsd)
        except IOError, (errno, strerror):
            raise ModelException("cannot load topology configuration: %s " %
                                 strerror)
            
    def reload_modules(self):
        """ load or reload the modules configuration """
        for host_type in self._modules:
            for host_name in self._modules[host_type]:
                module = self._modules[host_type][host_name]
                module.update(self._scenario_path, 'global')

    def load_simulation(self):
        """ load the simulation deployment file """
        simu_path = os.path.join(self._scenario_path, 'simulation_files.ini')

        try:
            # if the simulation deployment file is not loaded, load it from
            # current scenario or from default path
            if self._deploy_simu is None:
                if not os.path.exists(simu_path):
                    shutil.copy(DEFAULT_SIMU_FILE, simu_path)

                self._deploy_simu = GreedyConfigParser()
                if len(self._deploy_simu.read(simu_path)) == 0:
                    raise ModelException("Cannot load simulation deployment "
                                         "file '%s'" % simu_path)
            else:
                # write the current simulation deployment file
                with open(simu_path, 'w') as simu_file:
                    self._deploy_simu.write(simu_file)
        except IOError, msg:
            raise ModelException("failed to copy the simulation deployment "
                                 "file: '%s'" % msg)
        except ConfigParser.Error, msg:
            raise ModelException("failed to write the simulation deployment "
                                 "file '%s': %s" % (simu_path, msg))

    def add_topology(self, name, instance, net_config):
        """ Add a new host in the topology configuration file """
        try:
            if name == 'sat':
                att_path = '/configuration/sat_carrier/carriers/carrier' \
                           '[@up="true" and @ip_multicast="false"]'
                self._topology.set_values(net_config['emu_ipv4'].split('/')[0],
                                          att_path, 'ip_address')
            elif name == 'gw':
                att_path = '/configuration/sat_carrier/carriers/carrier' \
                           '[@up="false" and @ip_multicast="false"]'
                self._topology.set_values(net_config['emu_ipv4'].split('/')[0],
                                          att_path, 'ip_address')

            if name != "sat":
                addr = net_config['lan_ipv4'].split('/')
                ip = addr[0]
                net = ip[0:ip.rfind('.') + 1] + "0"
                mask = addr[1]
                line = {'addr': net,
                        'mask': mask,
                        'tal_id': instance,
                       }
                xpath = '/configuration/ip_dedicated_v4/terminals'
                self._topology.create_line(line, 'terminal_v4', xpath)
                addr = net_config['lan_ipv6'].split('/')
                ip = addr[0]
                net = ip[0:ip.rfind(':') + 1] + "0"
                mask = addr[1]
                line = {'addr': net,
                        'mask': mask,
                        'tal_id': instance,
                       }
                xpath = '/configuration/ip_dedicated_v6/terminals'
                self._topology.create_line(line, 'terminal_v6', xpath)

            self._topology.write()
        except XmlException, msg:
            self._log.error("failed to add topology for %s: %s" % (name,
                                                                   str(msg)))
        except KeyError, msg:
            self._log.error("cannot find network keys %s for topology updating "
                            "on %s" % (msg, name))
        except Exception, msg:
            self._log.error("unknown exception when trying to add topology for "
                            "%s: %s" % (name, str(msg)))

    def remove_topology(self, instance):
        """ remove a host from topology configuration file """
        try:
            xpath = "/configuration/ip_dedicated_v4/terminals/terminal_v4" \
                    "[@tal_id='%s']" % instance
            self._topology.del_element(xpath)
            xpath = "/configuration/ip_dedicated_v6/terminals/terminal_v6" \
                    "[@tal_id='%s']" % instance
            self._topology.del_element(xpath)
            self._topology.write()
        except XmlException, msg:
            self._log.error("failed to remove host with id %s in topology: %s" %
                            (instance, str(msg)))
        except Exception, msg:
            self._log.error("unknown exception when trying to remove topology "
                            "for host with instance %s: %s" % (instance,
                                                               str(msg)))

    def close(self):
        """ release the model """
        self._log.debug("Model: close")
        self._event_manager.set('quit')
        self._event_manager_response.set('quit')
        self._log.debug("Model: closed")

    def get_hosts_list(self):
        """ return the hosts list """
        return self._hosts

    def get_host(self, name):
        """ return the host according to its name """
        for host in self.get_all():
            if name == host.get_name():
                return host
        if name == 'global':
            return self._config
        return None

    def get_workstations_list(self):
        """ return the workstations list """
        return self._ws

    def get_all(self):
        """ return the hosts and workstation list """
        return self._hosts + self._ws

    def del_host(self, name):
        """ remove an host """
        idx = 0
        for host in self._hosts:
            if name == host.get_name():
                self._log.debug("remove host: '" + name + "'")
                if not name == 'sat':
                    self.remove_topology(self._hosts[idx].get_instance())
                del self._hosts[idx]
            idx += 1

        idx = 0
        for host in self._ws:
            if name == host.get_name():
                self._log.debug("remove host: '" + name + "'")
                del self._ws[idx]
            idx += 1

        for module in self._missing_modules:
            if name in self._missing_modules[module]:
                self._missing_modules[module].remove(name)

    def add_host(self, name, instance, network_config,
                 state_port, command_port, tools, host_modules):
        """ add an host in the host list """
        # remove instance for ST and WS
        if name.startswith('st'):
            component = 'st'
        elif name.startswith('ws'):
            component = 'ws'
        else:
            component = name

        # check if we have all the correct information
        checked = True
        if (component == 'st' or component == 'ws') and instance == '':
            self._log.warning(name + ": "
                              "service received with no instance information")
            checked = False
        if not str(state_port).isdigit() or not str(command_port).isdigit():
            self._log.warning(name + ": "
                              "service received with no state or command port")
            checked = False

        ip_addr = network_config['discovered']
        # find if the component already exists
        for host in self._hosts:
            if host.get_name() == name:
                self._log.warning("%s : duplicated service received at "
                                  "address %s" % (name, ip_addr))
                raise ModelException
        for host in self._ws:
            if host.get_name() == name:
                self._log.warning("%s : duplicated service received at "
                                  "address %s" % (name, ip_addr))
                raise ModelException


        self._log.debug("add host '%s'" % name)
        # report a warning if a module is not supported by the host
        for module_type in self._modules:
            for module in [mod for mod in self._modules[module_type]
                               if mod.upper() not in host_modules]:
                if component != 'ws':
                    self._log.warning("%s: plugin %s may be missing" %
                                      (name.upper(), module))
                    if not module in self._missing_modules:
                        self._missing_modules[module] = [name]
                    else:
                        self._missing_modules[module].append(name)
        # the component does not exist so create it
        host = HostModel(name, instance, network_config, state_port,
                         command_port, tools, host_modules, self._scenario_path,
                         self._log)
        if component == 'sat':
            self._hosts.insert(0, host)
        elif component == 'gw':
            self._hosts.insert(1, host)
        elif component != 'ws':
            self._hosts.append(host)
        else:
            self._ws.append(host)

        if component != "ws":
            self.add_topology(name, instance, network_config)

        if not checked:
            raise ModelException
        else:
            return host

    def is_running(self):
        """ check if at least one host or controller is running """
        ret = False
        for host in self._hosts:
            if host.get_state() is not None:
                ret = ret or host.get_state()

        if ret:
            self._modified = True
        return ret

    def set_dev_mode(self, dev_mode=False):
        """ Set the dev mode to `dev_mode` """
        self._log.debug("Switch to dev mode %s" % dev_mode)
        self._is_dev_mode = dev_mode

    def get_dev_mode(self):
        """get the dev mode """
        return self._is_dev_mode

    def set_scenario(self, val):
        """ set the scenario id """
        self._modified = True
        self._scenario_path = val
        self._deploy_simu = None
        self.load()

    def get_scenario(self):
        """ get the scenario id """
        return self._scenario_path

    def set_run(self, val):
        """ set the scenario id """
        self._modified = True
        self._run_id = val
        if self._run_id == "":
            self._run_id = "default"


    def get_run(self):
        """ get the scenario id """
        return self._run_id

    def get_event_manager(self):
        """ get the event manager """
        return self._event_manager

    def get_event_manager_response(self):
        """ get the event manager response """
        return self._event_manager_response

    def get_simulation_file_parser(self):
        """ get the simulation file GreedyConfigParser object """
        return self._deploy_simu

    def main_hosts_found(self):
        """ check if OpenSAND main hosts were found in the platform """
        # check that we have at least sat, gw and one st
        sat = False
        gw = False
        st = False

        for host in self._hosts:
            if host.get_component() == 'sat' and host.get_state() != None:
                sat = True
            if host.get_component() == 'gw' and host.get_state() != None:
                gw = True
            if host.get_component() == 'st' and host.get_state() != None:
                st = True

        return sat and gw and st
    
    def is_collector_known(self):
        """ indicates if the environment plane collector service has been
            found. """
        return self._collector_known
    
    def is_collector_functional(self):
        """ indicates if the environment plane collector has responded to
            the manager registration. """
        return self._collector_functional
    
    def set_collector_known(self, collector_known):
        """ called by the service listener when the collector service is found
            or lost. """
        
        self._collector_known = collector_known
        if not collector_known:
            self._collector_functional = False
    
    def set_collector_functional(self, collector_functional):
        """ called by the probes controller when the collector responds to
            manager registration. """
        
        self._collector_functional = collector_functional

    def clean_default(self):
        """ clean the $HOME/.opensand directory from default files """
        if os.path.exists(self._scenario_path):
            try:
                shutil.rmtree(self._scenario_path)
            except (OSError, os.error), msg:
                self._log.warning("Cannot clean default scenario: %s" %
                                  str(msg))

    def is_default_modif(self):
        """ check if we work on the default path and if we modified it """
        return self._is_default and self._modified

    def is_default(self):
        """ check if we work on default path """
        return self._is_default

    def get_conf(self):
        """ get the global configuration """
        return self._config
    
    def get_modules(self):
        """ get the module list """
        return self._modules

    def get_encap_modules(self):
        """ get the encapsulation modules """
        return self._modules['encap']

    def get_missing(self):
        """ get the missing module list """
        return self._missing_modules

    def get_files(self):
        """ get the files to deploy for simulation """
        files = {}
        for host in self._hosts:
            init = []
            modules = host.get_modules()
            name = host.get_name().lower()
            compo = host.get_component().lower()
            # if the host is not referenced in the deployment file try the
            # component
            config = host.get_advanced_conf().get_configuration()
            files[name] = []
            if not self._deploy_simu.has_section(name):
                if self._deploy_simu.has_section(compo):
                    # copy the component section in the host section
                    self._deploy_simu.add_section(name)
                    for item in self._deploy_simu.items(compo):
                        self._deploy_simu.set(name, item[0], item[1])
                else:
                    continue
            for xpath in self._deploy_simu.options(name):
                src = self._deploy_simu.get(compo, xpath)
                dst = config.get(xpath)
                if dst is None:
                    # try to find dst in the modules
                    for module_type in modules:
                        if dst is not None:
                            break
                        for module_name in modules[module_type]:
                            module = modules[module_type][module_name]
                            module_config = module.get_config_parser()
                            if module_config is not None:
                                dst = module_config.get(xpath)
                            if dst is not None:
                                init.append(module_config.get("%s/.." % xpath))
                                break
                    if dst is None:
                        continue
                else:
                    init.append(config.get("%s/.." % xpath))
                files[name].append((xpath, src, dst))

            # detect files that are not in the simulation deployment file in
            # host configuration and modules configuration
            config = host.get_advanced_conf().get_configuration()
            new_files = config.get_files()
            new = {}
            # get the elements containing files in configuration
            for path in new_files:
                new[config.get("%s/.." % path)] = path
            for module_type in modules:
                for module_name in modules[module_type]:
                    module = modules[module_type][module_name]
                    module_config = module.get_config_parser()
                    if module_config is not None:
                        # get the elements containing files in module
                        # configuration
                        new_module_files = module_config.get_files()
                        for path in new_module_files:
                            new[module_config.get("%s/.." % path)] = path
                        new_files.update(new_module_files)
            # get the elements containing files that are delacred in the
            # deployment file
            # keep only the new elements
            remaining = set(new.keys()) - set(init)

            for new_file in remaining:
                xpath = new[new_file]
                dst = new_files[xpath]
                files[name].append((xpath, '', dst))

        # 'global' section
        init = []
        glob = self._config.get_configuration()
        files['global'] = []
        if self._deploy_simu.has_section('global'):
            for xpath in self._deploy_simu.options('global'):
                src = self._deploy_simu.get('global', xpath)
                dst = glob.get(xpath)
                if dst is None:
                    # try to find dst in the modules
                    for module_type in self._modules:
                        if dst is not None:
                            break
                        for module_name in modules[module_type]:
                            module = self._modules[module_type][module_name]
                            module_config = module.get_config_parser()
                            if module_config is not None:
                                dst = module_config.get(xpath)
                            if dst is not None:
                                init.append(module_config.get("%s/.." % xpath))
                                break
                    if dst is None:
                        continue
                else:
                    init.append(glob.get("%s/.." % xpath))
                files['global'].append((xpath, src, dst))

        # detect files that are not in the simulation deployment file in
        # global configuration and global modules configuration
        new_files = glob.get_files()
        new = {}
        # get the elements containing files in configuration
        for path in new_files:
            new[glob.get("%s/.." % path)] = path
        for module_type in self._modules:
            for module_name in self._modules[module_type]:
                module = self._modules[module_type][module_name]
                module_config = module.get_config_parser()
                if module_config is not None:
                    # get the elements containing files in module
                    # configuration
                    new_module_files = module_config.get_files()
                    for path in new_module_files:
                        new[module_config.get("%s/.." % path)] = path
                    new_files.update(new_module_files)
        # get the elements containing files that are delacred in the
        # deployment file
        # keep only the new elements
        remaining = set(new.keys()) - set(init)

        for new_file in remaining:
            xpath = new[new_file]
            dst = new_files[xpath]
            files['global'].append((xpath, '', dst))

        return files

    def modify_deploy_simu(self, host, xpath, val):
        """ modify a source in the files to deploy for simulation """
        if not self._deploy_simu.has_section(host):
            error_popup("Cannot find host %s in the simulation deployment file"
                        % host)
            return
        if not xpath in self._deploy_simu.options(host):
            error_popup("Cannot find key %s in the simulation deployment file"
                        % xpath)
            return
        self._deploy_simu.set(host, xpath, val)

    def save_deploy_simu(self):
        """ write the modified file list """
        simu_path = os.path.join(self._scenario_path, 'simulation_files.ini')
        try:
            with open(simu_path, 'w') as simu_file:
                self._deploy_simu.write(simu_file)
        except IOError, msg:
            error_popup("failed to copy the simulation deployment file: '%s'" %
                        msg)

    def get_saved_probes(self, run_id=None):
        """ get a SavedProbeLoader object with the saved probes objects """
        
        if run_id is None:
            run_id = self.get_run()
        
        run_path = os.path.join(self.get_scenario(), run_id)
        
        try:
            return SavedProbeLoader(run_path)
        except ValueError:
            return None

##### TEST #####
if __name__ == "__main__":
    import sys

    LOGGER = ManagerLog('debug', True, True, True)
    MODEL = Model(LOGGER)
    try:
        CONFIG = MODEL.get_conf()
        LOGGER.debug("payload type: " + CONFIG.get_payload_type())
        LOGGER.debug("emission standard: " + CONFIG.get_emission_std())
        LOGGER.debug("uplink encapsulation protocol: " +
                     CONFIG.get_up_return_encap())
        LOGGER.debug("downlink encapsulation protocol: " +
                     CONFIG.get_down_forward_encap())
        LOGGER.debug("frame duration: " + str(CONFIG.get_frame_duration()))

        MODEL.add_host('st1', '1', '127.0.0.1', 1111, 2222, {}, {})
        MODEL.add_host('st3', '3', '127.0.0.1', 1111, 2222, {}, {})
        NAMES = ''
        for HOST in MODEL.get_hosts_list():
            NAMES = NAMES + HOST.get_name() + ", "
        LOGGER.debug("hosts: " + NAMES[:len(NAMES)-2])

        MODEL.del_host('st1')
        NAMES = ''
        for HOST in MODEL.get_hosts_list():
            NAMES = NAMES + HOST.get_name() + ", "
        LOGGER.debug("hosts: " + NAMES[:len(NAMES)-2])
    except ModelException:
        LOGGER.error("model error")
        sys.exit(1)
    except ConfigParser.Error:
        LOGGER.error("error when reading configuration")
        sys.exit(1)
    finally:
        MODEL.close()

    sys.exit(0)
