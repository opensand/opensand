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
 * @file PhyChannel.h
 * @brief Physical Layer Channel
 * @author Santiago PENA LUQUE <santiago.penaluque@cnes.fr>
 */

#ifndef PHY_CHANNEL_H
#define PHY_CHANNEL_H

#include "PhysicalLayerPlugin.h"
#include "FmtDefinitionTable.h"
#include "OpenSandFrames.h"

#include <opensand_rt/Rt.h>

#include <string>


using std::string;

/**
 * @class PhyChannel
 * @brief Physical Layer Channel
 */
class PhyChannel
{
 protected:

	/// The channel status
	bool status;

	/// Nominal Conditions (best C/N in clear-sky conditions)
	unsigned int nominal_condition;

	/// AttenuationModels
	AttenuationModelPlugin *attenuation_model;

	/** Minimal Conditions (minimun C/N to have QEF communications)
	 *  of global link (i.e. considering the Modcod scheme)
	 */
	MinimalConditionPlugin *minimal_condition;

	/// Error Insertion object : defines who error will be introduced
	ErrorInsertionPlugin *error_insertion;

	/// Period of channel(s) attenuation update (ms)
	time_ms_t granularity;

	/// The type of satellite payload
	sat_type_t satellite_type;

	/// Timer id for attenuation update
	event_id_t att_timer;

	/**
	 * @brief Update the conditions of the communication model
	 *        (attenuation, propagation model, waveforms-modcod)
	 *
	 * @return true on success, false otherwise
	 */
	bool update();

	/**
	 * @brief get the total C/N of the link according to the uplink C/N
	 *        carried in the T_DVB_PHY structure and the downlink C/N
	 *        computed from nominal conditions and attenuation
	 *
	 * @param phy_frame  The uplink physical layer information for the current frame
	 *
	 * @return the total C/N
	 */
	double getTotalCN(T_DVB_PHY *phy_frame);

	/*
	 * @brief Inserts the C/N value of the Channel in a given T_DVB_PHY
	 *        structure
	 *
	 * @param phy_frame  The physical layer data of the current frame
	 */
	void addSegmentCN(T_DVB_PHY *phy_frame);

	/*
	 * @brief Update the Minimal Condition attribute when a msg is received
	 *
	 * @param hdr The DVB header
	 * @return true on success, false otherwise
	 */
	bool updateMinimalCondition(T_DVB_HDR *hdr);

	/**
	 * @brief Determine if a Packet shall be corrupted or not
	 *        depending on the attenuation_model conditions
	 *
	 * @param cn_total  The total C/N of the link
	 * @return true if it must be corrupted, false otherwise
	 */
	bool isToBeModifiedPacket(double cn_total);

	/**
	 * @brief Corrupt a package with error bits
	 *
	 * @param frame the packet to be modified
	 */
	void modifyPacket(T_DVB_META *frame, long length);


	/**
	 * Forward a DVB frame to a destination block
	 *
	 * @param dvb_meta  The DVB frame to send
	 * @param len       The length of the DVB frame to send
	 * @return Whether the DVB frame was successfully sent or not
	 */
	virtual bool forwardMetaFrame(T_DVB_META *dvb_meta,
	                              size_t len) = 0;

 public:

	/**
	 * @brief Build the Channel
	 */
	PhyChannel();

	/**
	 * @brief Destroy the Channel
	 */
	~PhyChannel();

};

#endif
