/*
 *
 *
 * Platine is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
 * Copyright © 2011 TAS
 *
 *
 * This file is part of the Platine testbed.
 *
 *
 * Platine is free software : you can redistribute it and/or modify it under the
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
 * @file bloc_encap_sat.h
 * @brief Generic Encapsulation Bloc for SE
 * @author Didier Barvaux <didier.barvaux@b2i-toulouse.com>
 * @author Julien Bernard <julien.bernard@toulouse.viveris.com>
 */

#ifndef BLOC_ENCAP_SAT_H
#define BLOC_ENCAP_SAT_H

// margouilla includes
#include "platine_margouilla/mgl_bloc.h"

// message includes
#include "msg_dvb_rcs.h"
#include "platine_margouilla/msg_ip.h"

#include "EncapCtx.h"
#include "AtmCtx.h"
#include "MpegUleCtx.h"
#include "GseCtx.h"
#include "NetPacket.h"
#include "NetBurst.h"

#include "platine_conf/conf.h"


/**
 * @class BlocEncapSat
 * @brief Generic Encapsulation Bloc for SE
 */
class BlocEncapSat: public mgl_bloc
{
 private:

	/// encapsulation context for ATM cells
	EncapCtx *encapCtx;

	/// Output encapsulation scheme
	string output_encap_proto;

	/// Expiration timers for encapsulation contexts
	std::map < mgl_timer, int > timers;

	/// Whether the bloc has been initialized or not
	bool initOk;

 public:

	/**
	 * Build a satellite encapsulation bloc
	 *
	 * @param blocmgr   The bloc manager
	 * @param fatherid  The father of the bloc
	 * @param name      The name of the bloc
	 */
	BlocEncapSat(mgl_blocmgr *blocmgr, mgl_id fatherid, const char *name);

	/**
	 * Destroy the encapsulation bloc
	 */
	~BlocEncapSat();

	/**
	 * Handle the events
	 *
	 * @param event  The event to handle
	 * @return       Whether the event was successfully handled or not
	 */
	mgl_status onEvent(mgl_event *event);

	/**
	 * Set the upper-layer bloc
	 *
	 * @param bloc_id  The id of the upper-layer bloc
	 * @return         Whether the upper-layer bloc was successfully set or not
	 */
	mgl_status setUpperLayer(mgl_id bloc_id);

 private:

	/**
	 * Initialize the satellite encapsulation block
	 *
	 * @return  Whether the init was successful or not
	 */
	mgl_status onInit();

	/**
	 * Handle the timer event
	 *
	 * @param timer  The Margouilla timer to handle
	 * @return       Whether the timer event was successfully handled or not
	 */
	mgl_status onTimer(mgl_timer timer);

	/**
	 * Handle a burst of encapsulation packets received from the lower-layer
	 * block
	 *
	 * @param burst  The burst received from the lower-layer block
	 * @return       Whether the burst was successful handled or not
	 */
	mgl_status onRcvBurstFromDown(NetBurst *burst);

	/**
	 * Forward a burst of MPEG or GSE packets to the lower-layer block
	 *
	 * @param burst  The MPEG or GSE burst to forward
	 * @return       Whether the burst was successful forwarded or not
	 */
	mgl_status ForwardPackets(NetBurst *burst);

	/**
	 * Encapsulate a burst of ATM cells or MPEG packets and forward the resulting
	 * burst of MPEG or GSE packets to the lower-layer block
	 *
	 * @param burst  The ATM or GSE burst to encapsulate and forward
	 * @return       Whether the burst was successful encapsulated and forwarded
	 *               or not
	 */
	mgl_status EncapsulatePackets(NetBurst *burst);
};

#endif
