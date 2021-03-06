/*
 *
 * OpenSAND is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
 * Copyright © 2017 CNES
 * Copyright © 2017 TAS
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

#include "PhyChannel.h"
#include "BBFrame.h"
#include "DvbRcsFrame.h"
#include "DelayFifoElement.h"
#include "OpenSandCore.h"

#include <opensand_output/Output.h>
#include <opensand_conf/conf.h>

#include <math.h>

PhyChannel::PhyChannel():
	status(true),
	clear_sky_condition(0),
	attenuation_model(NULL),
	minimal_condition(NULL),
	error_insertion(NULL),
	refresh_period_ms(0),
	is_sat(false),
	satdelay(NULL),
	fifo_timer(-1),
	delay_timer(-1),
	delay_fifo(),
	probe_attenuation(NULL),
	probe_clear_sky_condition(NULL),
	probe_minimal_condition(NULL),
	probe_total_cn(NULL),
	probe_drops(NULL),
	probe_delay(NULL)
{
	// Output logs
	this->log_channel = Output::registerLog(LEVEL_WARNING,
	                                        "PhysicalLayer.Channel");
}

PhyChannel::~PhyChannel()
{
}

bool PhyChannel::update()
{
	if(!this->status)
	{
		LOG(this->log_channel, LEVEL_DEBUG,
		    "channel is broken, do not update it");
		goto error;
	}

	LOG(this->log_channel, LEVEL_INFO,
	    "Channel updated\n");
	if(this->attenuation_model->updateAttenuationModel())
	{
		LOG(this->log_channel, LEVEL_INFO,
		    "New attenuation: %.2f dB\n",
		    this->attenuation_model->getAttenuation());
	}
	else
	{
		LOG(this->log_channel, LEVEL_ERROR,
		    "channel updating failed, disable it");
		this->status = false;
	}

	this->probe_attenuation->put(this->attenuation_model->getAttenuation());
	this->probe_clear_sky_condition->put(this->clear_sky_condition);

error:
	return this->status;
}

double PhyChannel::getTotalCN(DvbFrame *dvb_frame)
{
	double cn_down, cn_up, cn_total; 
	double num_down, num_up, num_total; 

	/* C/N calculation of downlink, as the substraction of the clear sky C/N
	 * with the Attenuation */
	cn_down = this->clear_sky_condition - this->attenuation_model->getAttenuation();

	/* C/N of uplink */ 
	cn_up = dvb_frame->getCn();

	// Calculation of the sub total C/N ratio
	num_down = pow(10, cn_down / 10);
	num_up = pow(10, cn_up / 10);

	num_total = 1 / ((1 / num_down) + (1 / num_up)); 
	cn_total = 10 * log10(num_total);

	// update CN in frame for DVB block transmission
	dvb_frame->setCn(cn_total);

	LOG(this->log_channel, LEVEL_DEBUG,
	    "Satellite: cn_downlink= %.2f dB cn_uplink= %.2f dB "
	    "cn_total= %.2f dB\n", cn_down, cn_up, cn_total);
	this->probe_total_cn->put(cn_total);

	return cn_total;
}


void PhyChannel::addSegmentCN(DvbFrame *dvb_frame)
{
	double val; 

	/* C/N calculation as the substraction of the clear_sky C/N with
	   the Attenuation for this segment(uplink) */

	val = this->clear_sky_condition - this->attenuation_model->getAttenuation();
	LOG(this->log_channel, LEVEL_INFO,
	    "Calculation of C/N: %.2f dB\n", val);

	dvb_frame->setCn(val);
}


bool PhyChannel::isToBeModifiedPacket(double cn_total)
{
	// we sum all values so we can put 0 here
	this->probe_drops->put(0);
	return error_insertion->isToBeModifiedPacket(cn_total,
	                                             this->minimal_condition->getMinimalCN());
}

void PhyChannel::modifyPacket(DvbFrame *dvb_frame)
{
	Data payload;

	// keep the complete header because we carry useful data
	if(dvb_frame->getMessageType() == MSG_TYPE_BBFRAME)
	{
		// TODO BBFrame *bbframe = dynamic_cast<BBFrame *>(dvb_frame);
		BBFrame *bbframe = dvb_frame->operator BBFrame *();

		payload = bbframe->getPayload();
	}
	else
	{
		// TODO DvbRcsFrame *dvb_rcs_frame = dynamic_cast<DvbRcsFrame *>(dvb_frame);
		DvbRcsFrame *dvb_rcs_frame = dvb_frame->operator DvbRcsFrame *();

		payload = dvb_rcs_frame->getPayload();
	}

	if(error_insertion->modifyPacket(payload))
	{
		dvb_frame->setCorrupted(true);
		this->probe_drops->put(1);
	}
}

bool PhyChannel::updateMinimalCondition(DvbFrame *dvb_frame)
{
	uint8_t modcod_id = 0;
	LOG(this->log_channel, LEVEL_DEBUG,
	    "Trace update minimal condition\n");

	if(!this->status)
	{
		LOG(this->log_channel, LEVEL_INFO,
		    "channel is broken, do not update minimal condition");
		goto error;
	}

	// keep the complete header because we carry useful data
	if(dvb_frame->getMessageType() == MSG_TYPE_BBFRAME)
	{
		// TODO BBFrame *bbframe = dynamic_cast<BBFrame *>(dvb_frame);
		BBFrame *bbframe = (BBFrame *)dvb_frame;

		modcod_id = bbframe->getModcodId();
	}
	else
	{
		// TODO DvbRcsFrame *dvb_rcs_frame = dynamic_cast<DvbRcsFrame *>(dvb_frame);
		DvbRcsFrame *dvb_rcs_frame = (DvbRcsFrame *)dvb_frame;

		modcod_id = dvb_rcs_frame->getModcodId();
	}
	LOG(this->log_channel, LEVEL_INFO,
	    "Receive frame with MODCOD %u\n", modcod_id);

	if(!this->minimal_condition->updateThreshold(modcod_id, dvb_frame->getMessageType()))
	{
		LOG(this->log_channel, LEVEL_ERROR,
		    "Threshold update failed, the channel will "
		    "be disabled\n");
		this->status = false;
		goto error;     
	}

	// TODO this would be better to get minimal condition per source terminal
	//      if we are on regenerative satellite or GW
	//      On terminals,  here we receive all BBFrame on the spot,
	//      some may not contain packets for us but we will still count them in stats
	//      We would have to parse frames in order to remove them from
	//      statistics, this is not efficient 
	//      With physcal layer ACM loop, these frame would be mark as corrupted
	this->probe_minimal_condition->put(this->minimal_condition->getMinimalCN());

	LOG(this->log_channel, LEVEL_INFO,
	    "Update minimal condition: %.2f dB\n",
	    this->minimal_condition->getMinimalCN());
error:
	return this->status;
}

bool PhyChannel::pushInFifo(NetContainer *data, time_ms_t delay)
{
	DelayFifoElement *elem;
	time_ms_t current_time = getCurrentTime();

	// create a new FIFO element to store the packet
	elem = new DelayFifoElement(data, current_time, current_time + delay);
	if(!elem)
	{
		LOG(this->log_channel, LEVEL_ERROR,
		    "cannot allocate FIFO element, drop data\n");
		goto error;
	}
	// append the data in the fifo
	if(!this->delay_fifo.push(elem))
	{
		LOG(this->log_channel, LEVEL_ERROR,
		    "FIFO is full: drop data\n");
		goto release_elem;
	}
	LOG(this->log_channel, LEVEL_NOTICE,
	    "%s data stored in FIFO (tick_in = %ld, tick_out = %ld)\n",
	    data->getName().c_str(), elem->getTickIn(), elem->getTickOut());
	return true;
release_elem:
	delete elem;
error:
	delete data;
	return false;
}
