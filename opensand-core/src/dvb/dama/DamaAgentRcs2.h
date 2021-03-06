/*
 *
 * OpenSAND is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
 * Copyright © 2018 TAS
 *
 *
 * This file is part of the OpenSAND testbed.
 *
 *
 * OpenSAND is free software : you can redistribute it and/or modify it under
 * the terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY, without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
 * for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program. If not, see http://www.gnu.org/licenses/.
 *
 */

/**
 * @file DamaAgentRcs.h
 * @brief Implementation of the DAMA agent for DVB-RCS2 emission standard.
 * @author Aurelien DELRIEU <adelrieu@toulouse.viveris.com>
 */

#ifndef _DAMA_AGENT_RCS2_H_
#define _DAMA_AGENT_RCS2_H_

#include "DamaAgentRcsCommon.h"
#include "FmtDefinitionTable.h"
#include "ReturnSchedulingRcs2.h"

#include <opensand_output/OutputLog.h>

class DamaAgentRcs2 : public DamaAgentRcsCommon
{
 public:
	DamaAgentRcs2(FmtDefinitionTable *ret_modcod_def);
	virtual ~DamaAgentRcs2();

	virtual bool processOnFrameTick();

 protected:

	/**
	 * @brief Generate an unit converter
	 *
	 * @return                  the generated unit converter
	 */
	virtual UnitConverter *generateUnitConverter() const;
	
	/**
	 * @brief Generate a return link scheduling specialized to DVB-RCS, DVB-RCS2
	 *        or other
	 * @return                  the generated scheduling
	 */
	ReturnSchedulingRcsCommon *generateReturnScheduling() const;

	/**
	 * @brief Compute RBDC request
	 *
	 * @return                  the RBDC Request in kbits/s
	 */
	virtual rate_kbps_t computeRbdcRequest() = 0;

	/**
	 * @brief Compute VBDC request
	 *
	 * @return                  the VBDC Request in number of packets
	 *                          ready to be set in SAC field
	 */
	virtual vol_pkt_t computeVbdcRequest() = 0;
};

#endif

