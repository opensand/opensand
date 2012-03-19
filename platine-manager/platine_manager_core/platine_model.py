#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#
# Platine is an emulation testbed aiming to represent in a cost effective way a
# satellite telecommunication system for research and engineering activities.
#
#
# Copyright © 2011 TAS
#
#
# This file is part of the Platine testbed.
#
#
# Platine is free software : you can redistribute it and/or modify it under the
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
platine_model.py - Platine manager model
"""

import ConfigParser
import os
import shutil

from platine_manager_core.model.environment_plane import EnvironmentPlaneModel
from platine_manager_core.model.event_manager import EventManager
from platine_manager_core.model.host import HostModel
from platine_manager_core.my_exceptions import ModelException
from platine_manager_core.loggers.manager_log import ManagerLog

DEFAULT_INI_PATH = '/etc/platine/manager.ini'
MAX_RECENT = 5

#TODO store the configuration in a separated class ?
class Model:
    """ Model for Platine """

    def __init__(self, manager_log, scenario = ''):
        # initialized in load
        self._inifile = None
        self._log = manager_log

        self._env_plane = EnvironmentPlaneModel(self._log)
        # start event managers
        self._event_manager = EventManager("manager")
        self._event_manager_response = EventManager("response")

        self._scenario_path = scenario
        self._is_default = False
        self._modified = False
        self._run_id = "default"

        # Running in dev mode ?
        self._is_dev_mode = False

        self._hosts = []
        self._ws = []

        self._config = ConfigParser.SafeConfigParser()

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
                                               ".platine/default")
            self.clean_default()
            self._is_default = True
        else:
            recents = []
            filename = os.path.join(os.environ['HOME'], ".platine/recent")
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

        # actualize the tools scenario path
        for host in self._hosts:
            host.reload_tools(self._scenario_path)

        self._inifile = os.path.join(self._scenario_path, 'manager.ini')
        # copy configuration file if necessary
        if not os.path.exists(self._inifile):
            try:
                shutil.copy(DEFAULT_INI_PATH, self._inifile)
            except IOError, (errno, strerror):
                raise ModelException("cannot copy file '%s' in '%s': %s" %
                                     (DEFAULT_INI_PATH, self._inifile,
                                      strerror))

        # read configuration file
        # TODO replace that by a XML validation tool when configuration
        #      will be in XML format
        if len(self._config.read(self._inifile)) == 0:
            self._log.error("failed to load Platine Manager configuration " \
                            "from '%s'" % self._inifile)
            raise ModelException("failed to load Platine Manager " \
                                 "configuration from '%s'" % self._inifile)

        # check that all the needed elements are in the configuration file
        if not self._config.has_section('global'):
            self._log.error("cannot get global section in the configuration " \
                            "file")
            raise ModelException("cannot get global section in the " \
                                 "configuration file")

        if not self._config.has_option('global', 'payload_type'):
            self._log.error("cannot get payload_type option in the " \
                            "configuration file")
            raise ModelException("cannot get payload_type option in the " \
                                 "configuration file")

        if not self._config.has_option('global', 'emission_std'):
            self._log.error("cannot get emission_std option in the " \
                            "configuration file")
            raise ModelException("cannot get emission_std option in the " \
                                 "configuration file")

        if not self._config.has_option('global', 'out_encapsulation'):
            self._log.error("cannot get out_encapsulation option in the " \
                            "configuration file")
            raise ModelException("cannot get out_encapsulation option in the " \
                                 "configuration file")

        if not self._config.has_option('global', 'in_encapsulation'):
            self._log.error("cannot get in_encapsulation option in the " \
                            "configuration file")
            raise ModelException("cannot get in_encapsulation option in the " \
                                 "configuration file")

        if not self._config.has_option('global', 'terminal_type'):
            self._log.error("cannot get terminal_type option in the " \
                            "configuration file")
            raise ModelException("cannot get terminal_type option in the " \
                                 "configuration file")

        if not self._config.has_option('global', 'frame_duration'):
            self._log.error("cannot get frame_duration option in the " \
                            "configuration file")
            raise ModelException("cannot get frame_duration option in the " \
                                 "configuration file")

    def close(self):
        """ release the model """
        self._log.debug("Model: close")
        self._event_manager.set('quit')
        self._event_manager_response.set('quit')
        self._log.debug("Model: closed")

    def get_hosts_list(self):
        """ return the hosts list """
        return self._hosts

    def get_workstations_list(self):
        """ return the workstations list """
        return self._ws

    def del_host(self, name):
        """ remove an host """
        idx = 0
        for host in self._hosts:
            if name == host.get_name():
                self._log.debug("remove host: '" + name + "'")
                del self._hosts[idx]
            idx += 1

        idx = 0
        for host in self._ws:
            if name == host.get_name():
                self._log.debug("remove host: '" + name + "'")
                del self._ws[idx]
            idx += 1

    def add_host(self, name, instance, ip_addr, state_port,
                 command_port, tools):
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


        # the component does not exist so create it
        self._log.debug("add host '%s'" % name)
        host = HostModel(name, instance, ip_addr, state_port, command_port,
                         tools, self._scenario_path, self._log)
        if component == 'sat':
            self._hosts.insert(0, host)
        elif component == 'gw':
            self._hosts.insert(1, host)
        elif component != 'ws':
            self._hosts.append(host)
        else:
            self._ws.append(host)

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

        if self._env_plane.is_running() is not None:
            ret = ret or self._env_plane.is_running()

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

    def get_env_plane(self):
        """ get the environment plane model """
        return self._env_plane

    def set_scenario(self, val):
        """ set the scenario id """
        self._modified = True
        self._scenario_path = val
        self.load()

    def get_scenario(self):
        """ get the scenario id """
        return self._scenario_path

    def set_run(self, val):
        """ set the scenario id """
        self._modified = True
        self._run_id = val

    def get_run(self):
        """ get the scenario id """
        return self._run_id

    def set_payload_type(self, val):
        """ set the payload_type value """
        try:
            self._config.set('global', 'payload_type', val)
        except ConfigParser.Error, error:
            self._log.error("error when writing configuration " + error)

    def get_payload_type(self):
        """ get the payload_type value """
        val = None
        try:
            val = self._config.get('global', 'payload_type')
        except ConfigParser.Error, error:
            self._log.error("error when reading configuration " + error)
        finally:
            return val

    def set_emission_std(self, val):
        """ set the emission_std value """
        try:
            self._config.set('global', 'emission_std', val)
        except ConfigParser.Error, error:
            self._log.error("error when writing configuration " + error)

    def get_emission_std(self):
        """ get the emission_std value """
        val = None
        try:
            val = self._config.get('global', 'emission_std')
        except ConfigParser.Error, error:
            self._log.error("error when reading configuration " + error)
        finally:
            return val

    def set_out_encapsulation(self, val):
        """ set the out_encapsulation value """
        try:
            self._config.set('global', 'out_encapsulation', val)
        except ConfigParser.Error, error:
            self._log.error("error when writing configuration " + error)

    def get_out_encapsulation(self):
        """ get the out_encapsulation value """
        val = None
        try:
            val = self._config.get('global', 'out_encapsulation')
        except ConfigParser.Error, error:
            self._log.error("error when reading configuration " + error)
        finally:
            return val

    def set_in_encapsulation(self, val):
        """ set the in_encapsulation value """
        try:
            self._config.set('global', 'in_encapsulation', val)
        except ConfigParser.Error, error:
            self._log.error("error when writing configuration " + error)

    def get_in_encapsulation(self):
        """ get the in_encapsulation value """
        val = None
        try:
            val = self._config.get('global', 'in_encapsulation')
        except ConfigParser.Error, error:
            self._log.error("error when reading configuration " + error)
        finally:
            return val

    def set_terminal_type(self, val):
        """ set the terminal_type value """
        try:
            self._config.set('global', 'terminal_type', val)
        except ConfigParser.Error, error:
            self._log.error("error when writing configuration " +  error)

    def get_terminal_type(self):
        """ get the terminal_type value """
        val = None
        try:
            val = self._config.get('global', 'terminal_type')
        except ConfigParser.Error, error:
            self._log.error("error when reading configuration " + error)
        finally:
            return val

    def set_frame_duration(self, val):
        """ set the frame_duration value """
        try:
            self._config.set('global', 'frame_duration', val)
        except ConfigParser.Error, error:
            self._log.error("error when writing configuration" + error)

    def get_frame_duration(self):
        """ get the frame_duration value """
        val = None
        try:
            val = self._config.getint('global', 'frame_duration')
        except ConfigParser.Error, error:
            self._log.error("error when reading configuration " + error)
        finally:
            return val

    def get_event_manager(self):
        """ get the event manager """
        return self._event_manager

    def get_event_manager_response(self):
        """ get the event manager response """
        return self._event_manager_response

    def save_configuration(self):
        """ save the model in configuration file """
        self._modified = True
        # write configuration to file
        try:
            file_conf = open(self._inifile, 'w')
        except IOError, (errno, strerror):
            error = "failed to open file to save the new configuration\n" + \
                    "File: %s\nReason: %s" % (self._inifile, strerror)
            raise ModelException(error)
        else:
            # write configuration to file
            try:
                # write config file
                self._config.write(file_conf)
            except IOError, (errno, strerror):
                error = "failed to write the new configuration to file\n" + \
                        "File: %s\nReason: %s" % (self._inifile, strerror)
                raise ModelException(error)
            else:
                self._log.debug('new configuration saved to disk')
            finally:
                file_conf.close()

    def main_hosts_found(self):
        """ check if Platine main hosts were found in the platform """
        # check that we have at least env_plane, sat, gw and one st
        sat = False
        gw = False
        st = False
        env_plane = False
        for host in self._hosts:
            if host.get_component() == 'sat' and host.get_state() != None:
                sat = True
            if host.get_component() == 'gw' and host.get_state() != None:
                gw = True
            if host.get_component() == 'st' and host.get_state() != None:
                st = True

        if self._env_plane.get_states() != None:
            env_plane = True

        return env_plane and sat and gw and st

    def clean_default(self):
        """ clean the $HOME/.platine directory from default files """
        if os.path.exists(self._scenario_path):
            try:
                shutil.rmtree(self._scenario_path)
            except (OSError, os.error), msg:
                self._log.warning("Cannot clean default scenario: %s" %
                                  str(msg))

    def is_default_modif(self):
        """ check if we work on the default path and if we modified it """
        return self._is_default and self._modified


##### TEST #####
if __name__ == "__main__":
    import sys

    LOGGER = ManagerLog('debug', True, True, True)
    MODEL = Model(LOGGER)
    try:
        LOGGER.debug("payload type: " + MODEL.get_payload_type())
        LOGGER.debug("emission standard: " + MODEL.get_emission_std())
        LOGGER.debug("uplink encapsulation protocol: " +
                     MODEL.get_out_encapsulation())
        LOGGER.debug("downlink encapsulation protocol: " +
                     MODEL.get_in_encapsulation())
        LOGGER.debug("terminal type: " + MODEL.get_terminal_type())
        LOGGER.debug("frame duration: " + str(MODEL.get_frame_duration()))

        MODEL.add_host('st1', '1', '127.0.0.1', 1111, 2222, {})
        MODEL.add_host('st3', '3', '127.0.0.1', 1111, 2222, {})
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
