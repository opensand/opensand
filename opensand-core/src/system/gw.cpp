/*
 *
 * OpenSAND is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
 * Copyright © 2013 TAS
 * Copyright © 2013 CNES
 *
 *
 * This file is part of the OpenSAND testbed.
 *
 *
 * OpenSAND is free software : you can redistribute it and/or modify it under the
 * terms of the GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option) any later
 * version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program. If not, see http://www.gnu.org/licenses/.
 *
 */

/**
 * @file gw.cpp
 * @brief Gateway (GW) process
 * @author Didier Barvaux <didier.barvaux@toulouse.viveris.com>
 * @author Julien BERNARD <jbernard@toulouse.viveris.com>
 *
 * Gateway uses the following stack of blocks installed over 2 NICs
 * (nic1 on user network side and nic2 on satellite network side):
 *
 * <pre>
 *
 *                     eth nic 1
 *                         |
 *                   Lan Adaptation  ---------
 *                         |                  |
 *                   Encap/Desencap      IpMacQoSInteraction
 *                         |                  |
 *                      Dvb Ncc  -------------
 *                 [Dama Controller]
 *                         |
 *                  Sat Carrier Eth
 *                         |
 *                     eth nic 2
 *
 * </pre>
 *
 */


#include "BlockLanAdaptation.h"
#include "BlockDvbNcc.h"
#include "BlockSatCarrier.h"
#include "BlockEncap.h"
#include "BlockPhysicalLayer.h"
#include "Plugin.h"

#include <opensand_conf/ConfigurationFile.h>
#include <opensand_conf/uti_debug.h>

#include <opensand_output/Output.h>
#include <opensand_rt/Rt.h>

#include <stdlib.h>
#include <string.h>
#include <signal.h>


/**
 * Argument treatment
 */
bool init_process(int argc, char **argv, string &ip_addr,
                  string &emu_iface, string &lan_iface)
{
	int opt;
	bool output_enabled = true;
	event_level_t output_event_level = LEVEL_INFO;

	/* setting environment agent parameters */
	while((opt = getopt(argc, argv, "-hqda:n:l:")) != EOF)
	{
		switch(opt)
		{
		case 'q':
			// disable output
			output_enabled = false;
			break;
		case 'd':
			// enable output debug
			output_event_level = LEVEL_DEBUG;
		case 'a':
			// get local IP address
			ip_addr = optarg;
			break;
		case 'n':
			// get local interface name
			emu_iface = optarg;
			break;
		case 'l':
			// get lan interface name
			lan_iface = optarg;
			break;
		case 'h':
		case '?':
			fprintf(stderr, "usage: %s [-h] [[-q] [-d] -a ip_address "
				"-n emu_iface -l lan_iface\n",
			        argv[0]);
			fprintf(stderr, "\t-h                   print this message\n");
			fprintf(stderr, "\t-q                   disable output\n");
			fprintf(stderr, "\t-d                   enable output debug events\n");
			fprintf(stderr, "\t-a <ip_address>      set the IP address for emulation\n");
			fprintf(stderr, "\t-n <emu_iface>       set the emulation interface name\n");
			fprintf(stderr, "\t-l <lan_iface>       set the ST lan interface name\n");

			UTI_ERROR("usage printed on stderr\n");
			return false;
		}
	}

	UTI_PRINT(LOG_INFO, "starting output\n");

	// output initialisation
	Output::init(output_enabled, output_event_level);

	if(ip_addr.size() == 0)
	{
		UTI_ERROR("missing mandatory IP address option");
		return false;
	}

	if(emu_iface.size() == 0)
	{
		UTI_ERROR("missing mandatory emulation interface name option");
		return false;
	}
	
	if(lan_iface.size() == 0)
	{
		UTI_ERROR("missing mandatory lan interface name option");
		return false;
	}
	return true;
}


int main(int argc, char **argv)
{
	const char *progname = argv[0];
 	struct sched_param param;
	bool with_phy_layer = false;
	string ip_addr;
	string emu_iface;
	string lan_iface;
	struct sc_specific specific;

	Block *block_lan_adaptation;
	Block *block_encap;
	Block *block_dvb;
	Block *block_phy_layer;
	Block *up_sat_carrier;
	Block *block_sat_carrier;

	vector<string> conf_files;

	int is_failure = 1;

	Event *status = NULL;
	Event *failure = NULL;

	// retrieve arguments on command line
	if(init_process(argc, argv, ip_addr, emu_iface, lan_iface) == false)
	{
		UTI_ERROR("%s: failed to init the process\n", progname);
		goto quit;
	}

	failure = Output::registerEvent("failure", LEVEL_ERROR);
	status = Output::registerEvent("status", LEVEL_INFO);

	// increase the realtime responsiveness of the process
	param.sched_priority = sched_get_priority_max(SCHED_FIFO);
	sched_setscheduler(0, SCHED_FIFO, &param);

	conf_files.push_back(CONF_TOPOLOGY);
	conf_files.push_back(CONF_GLOBAL_FILE);
	conf_files.push_back(CONF_DEFAULT_FILE);
	// Load configuration files content
	if(!globalConfig.loadConfig(conf_files))
	{
		UTI_ERROR("%s: cannot load configuration files, quit\n",
		          progname);
		goto unload_config;
	}

	// read all packages debug levels
	UTI_readDebugLevels();

	// Retrieve the value of the ‘enable’ parameter for the physical layer
	if(!globalConfig.getValue(PHYSICAL_LAYER_SECTION, ENABLE,
	                          with_phy_layer))
	{
		UTI_ERROR("%s: cannot  check if physical layer is enabled\n",
		          progname);
		goto unload_config;
	}
	UTI_PRINT(LOG_INFO, "%s: physical layer is %s\n",
	          progname, with_phy_layer ? "enabled" : "disabled");


	// load the plugins
	if(!Plugin::loadPlugins(with_phy_layer))
	{
		UTI_ERROR("%s: cannot load the plugins\n", progname);
		goto unload_config;
	}

	// instantiate all blocs
	block_lan_adaptation = Rt::createBlock<BlockLanAdaptationGw,
	                                       BlockLanAdaptationGw::Upward,
	                                       BlockLanAdaptationGw::Downward,
	                                       string>("LanAdaptation", NULL, lan_iface);
	if(!block_lan_adaptation)
	{
		UTI_ERROR("%s: cannot create the LanAdaptation block\n", progname);
		goto release_plugins;
	}

	block_encap = Rt::createBlock<BlockEncapGw,
	                              BlockEncapGw::Upward,
	                              BlockEncapGw::Downward>("Encap", block_lan_adaptation);
	if(!block_encap)
	{
		UTI_ERROR("%s: cannot create the Encap block\n", progname);
		goto release_plugins;
	}

	block_dvb = Rt::createBlock<BlockDvbNcc,
	                            BlockDvbNcc::Upward,
	                            BlockDvbNcc::Downward>("DvbNcc", block_encap);
	if(!block_dvb)
	{
		UTI_ERROR("%s: cannot create the DvbNcc block\n", progname);
		goto release_plugins;
	}

	up_sat_carrier = block_dvb;
	if(with_phy_layer)
	{
		block_phy_layer = Rt::createBlock<BlockPhysicalLayerGw,
		                                  BlockPhysicalLayerGw::PhyUpward,
		                                  BlockPhysicalLayerGw::PhyDownward>("PhysicalLayer",
		                                                                      block_dvb);
		if(block_phy_layer == NULL)
		{
			UTI_ERROR("%s: cannot create the PhysicalLayer block\n", progname);
			goto release_plugins;
		}
		up_sat_carrier = block_phy_layer;
	}

	specific.ip_addr = ip_addr;
	specific.emu_iface = emu_iface; // TODO emu_iface in struct
	block_sat_carrier = Rt::createBlock<BlockSatCarrierGw,
	                                    BlockSatCarrierGw::Upward,
	                                    BlockSatCarrierGw::Downward,
	                                    struct sc_specific>("SatCarrier",
	                                                        up_sat_carrier,
	                                                        specific);
	if(!block_sat_carrier)
	{
		UTI_ERROR("%s: cannot create the SatCarrier block\n", progname);
		goto release_plugins;
	}

	// make the GW alive
	if(!Rt::init())
	{
		goto release_plugins;
    }
/*	if(!Output::finishInit())
	{
		UTI_PRINT(LOG_INFO,
		          "%s: failed to init the output => disable it\n",
		         progname);
	}

	Output::sendEvent(status, "Blocks initialized");*/
	if(!Rt::run())
	{
		Output::sendEvent(failure, "cannot run process loop\n");
    }	

	Output::sendEvent(status, "Simulation stopped");

	// everything went fine, so report success
	is_failure = 0;

	// cleanup before GW stops
release_plugins:
	Plugin::releasePlugins();
unload_config:
	if(is_failure)
	{
		Output::finishInit();
		Output::sendEvent(failure, "Failure while launching component\n");
	}
	globalConfig.unloadConfig();
quit:
	UTI_PRINT(LOG_INFO, "%s: GW process stopped with exit code %d\n",
	          progname, is_failure);
	closelog();
	return is_failure;
}
