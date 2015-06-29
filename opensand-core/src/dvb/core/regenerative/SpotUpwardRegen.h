/*
 *
 * OpenSAND is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
 * Copyright © 2015 TAS
 * Copyright © 2015 CNES
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
 * @file SpotUpwardRegen.h
 * @brief Upward spot related functions for DVB NCC block
 * @author Bénédicte Motto <bmotto@toulouse.viveris.com>
 * @author Julien Bernard <julien.bernard@toulouse.viveris.com>
 *
 */

#ifndef SPOT_UPWARD_REGEN_H
#define SPOT_UPWARD_REGEN_H

#include "SpotUpward.h"
#include "PhysicStd.h"  
#include "NetBurst.h"
#include "DamaCtrlRcs.h"
#include "NccPepInterface.h"
#include "Scheduling.h"
#include "SlottedAlohaNcc.h"

#define SIMU_BUFF_LEN 255

class SpotUpwardRegen: public SpotUpward
{
	public:
		SpotUpwardRegen(spot_id_t spot_id,
		                tal_id_t mac_id);
		~SpotUpwardRegen();
		bool onInit();


		/**
		 * @brief Handle a DVB frame
		 *
		 * @param frame  The frame
		 * @param burst  OUT: the burst of packets
		 * @return true on success, false otherwise
		 */
		bool handleFrame(DvbFrame *frame, NetBurst **burst);

		/**
		 * @brief Schedule Slotted Aloha carriers
		 *
		 *	@param dvb_frame   a SoF
		 *  @param ack_frames  OUT: The generated ACK frames
		 *  @param sa_burst    OUT: The Slotted Aloha bursts received
		 *  @return true on success, false otherwise
		 */
		bool scheduleSaloha(DvbFrame *dvb_frame,
		                    list<DvbFrame *>* &ack_frames,
		                    NetBurst **sa_burst);

		/**
		 *  @brief Handle a Slotted Aloha Data Frame
		 *
		 *  @param frame  The Slotted Aloha data frame
		 *  @return true on success, false otherwise
		 */
		bool handleSlottedAlohaFrame(DvbFrame *frame);

		// statistics update
		void updateStats(void);


	protected:
		
		/**
		 * @brief Initialize the transmission mode
		 *
		 * @return  true on success, false otherwise
		 */
		bool initMode(void);

		/**
		 * Read configuration for the Slotted Aloha algorithm
		 *
		 * @return  true on success, false otherwise
		 */
		bool initSlottedAloha(void);

		/**
		 * @brief Initialize the statistics
		 *
		 * @return  true on success, false otherwise
		 */
		bool initOutput(void);

	};

#endif