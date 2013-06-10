/*
 *
 * OpenSAND is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
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
 * @file Constant.h
 * @brief Determine Minimal C/N depending of the current Constant 
 * @author Santiago PENA LUQUE <santiago.penaluque@cnes.fr>
 */

#ifndef CONSTANT_MINIMAL_CONDITION_PLUGIN_H
#define CONSTANT_MINIMAL_CONDITION_PLUGIN_H 


#include "PhysicalLayerPlugin.h"
#include "OpenSandCore.h"

/**
 * @class Constant 
 */
class Constant: public MinimalConditionPlugin
{

	public:

		/**
		 * @brief Build the defaultMinimalCondition
		 */
		Constant();

		/**
		 * @brief Destroy the defaultMinimalCondition
		 */
		~Constant();

		/**
		 * @brief initialize the minimal condition
		 *
		 * @return true on success, false otherwise
		 */
		bool init();

		/**
		 * @brief Updates Thresold when a msg arrives to Channel
		 *
		 * @return true on success, false otherwise
		 */
		bool updateThreshold(T_DVB_HDR *UNUSED(hdr));
};

CREATE(Constant, minimal_plugin, "Constant");

#endif

