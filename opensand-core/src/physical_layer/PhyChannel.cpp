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
 * @file PhyChannel.cpp
 * @brief PhyChannel
 * @author Santiago PENA LUQUE <santiago.penaluque@cnes.fr>
 */

// FIXME we need to include uti_debug.h before...
#define DBG_PREFIX
#define DBG_PACKAGE PKG_PHY_LAYER
#include <opensand_conf/uti_debug.h>

#include  "PhyChannel.h"

#include <math.h>

PhyChannel::PhyChannel():
	status(true),
	attenuation_model(NULL),
	nominal_condition(NULL),
	minimal_condition(NULL),
	error_insertion(NULL),
	granularity(0)
{
}

PhyChannel::~PhyChannel()
{
}

bool PhyChannel::update()
{
	const char *FUNCNAME = "[Channel::update]";

	if(!this->status)
	{
		UTI_DEBUG_L3("channel is broken, do not update it");
		goto error;
	}

	UTI_DEBUG("%s Channel updated\n", FUNCNAME);
	if(this->attenuation_model->updateAttenuationModel())
	{
		UTI_DEBUG("%s New attenuation: %f \n",
		          FUNCNAME, this->attenuation_model->getAttenuation());
		UTI_DEBUG("%s Current Nominal CN: %f \n", FUNCNAME,
		          this->nominal_condition->getNominalCN());
	}
	else
	{
		UTI_ERROR("channel updating failed, disable it");
		this->status = false;
	}

error:
	return this->status;
}

void PhyChannel::addSegmentCN(T_DVB_PHY *phy_frame)
{

	const char *FUNCNAME = "[Channel::addSegmentCN]";
	double val; 

	/* C/N calculation as the substraction of the Nominal C/N with
	   the Attenuation for this segment(uplink) */

	val = (this->nominal_condition->getNominalCN())
	      - (this->attenuation_model->getAttenuation());
	UTI_DEBUG("%s Calculation of C/N: %f \n", FUNCNAME, val);

	phy_frame->cn_previous = val;
}


void PhyChannel::modifySegmentCN(T_DVB_PHY *phy_frame)
{
	const char *FUNCNAME = "[Channel::modifySegmentCN]";
	double cn_segment, cn_previous, cn_total; 
	double num_segment, num_previous, num_total; 

	/* C/N calculation of the current segment, as the substraction
	 * of the Nominal C/N with
	 * the Attenuation */
	cn_segment = (this->nominal_condition->getNominalCN())
	              - (this->attenuation_model->getAttenuation());

	/* C/N of previous segment */ 
	cn_previous = phy_frame->cn_previous; 

	// Calculation of the sub total C/N ratio

	num_segment = pow(10,cn_segment/10);
	num_previous = pow(10,cn_previous/10);

	num_total = 1 / ((1/num_segment) + (1/num_previous)); 
	cn_total = 10 * log10(num_total);

	UTI_DEBUG_L3("%s Satellite: cn_segment= %f cn_previous= %f"
	          " cn_total= %f \n", FUNCNAME,
	          cn_segment, cn_previous, cn_total);

	// Change the subtotal C/N of the message 
	phy_frame->cn_previous = cn_total;
}

bool PhyChannel::isToBeModifiedPacket(double cn_uplink)
{
	return error_insertion->isToBeModifiedPacket(cn_uplink,
	                                             this->nominal_condition->getNominalCN(),
	                                             this->attenuation_model->getAttenuation(),
	                                             this->minimal_condition->getMinimalCN());
}

void PhyChannel::modifyPacket(T_DVB_META *frame, long length)
{
	error_insertion->modifyPacket(frame, length);
}

bool PhyChannel::updateMinimalCondition(T_DVB_HDR *hdr)
{
	UTI_DEBUG_L3("Trace update minimal condition\n");

	if(!this->status)
	{
		UTI_DEBUG("channel is broken, do not update minimal condition");
		goto error;
	}

	if(!this->minimal_condition->updateThreshold(hdr))
	{
		UTI_ERROR("Threshold update failed, the channel will be disabled\n");
		this->status = false;
		goto error;     
	}

error:
	return this->status;
}

