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
 * @file UlePacket.h
 * @brief Ule packet
 * @author Didier Barvaux <didier.barvaux@b2i-toulouse.com>
 */

#ifndef ULE_PACKET_H
#define ULE_PACKET_H

#include <NetPacket.h>

/// The length of the ULE header (in bytes)
#define ULE_HEADER_LEN 4
/// The length of the ULE Destination Address field (in bytes)
#define ULE_ADDR_LEN   6
/// The length of the ULE CRC (in bytes)
#define ULE_CRC_LEN    4


/**
 * @class UlePacket
 * @brief ULE packet
 */
class UlePacket: public NetPacket
{
 protected:

	/**
	 * Calculate the CRC for ULE data
	 *
	 * @param pos     the index of first byte to use
	 * @param len     the number of bytes to use
	 * @param enabled is the CRC computing enabled
	 * @return     the calculated CRC
	 */
	uint32_t calcCrc(bool enabled);

 public:

	/**
	 * Build an ULE packet
	 *
	 * @param data    raw data from which an ULE packet can be created
	 * @param length  length of raw data
	 */
	UlePacket(unsigned char *data, unsigned int length);

	/**
	 * Build an ULE packet
	 *
	 * @param data  raw data from which an ULE packet can be created
	 */
	UlePacket(Data data);

	/**
	 * Build an empty ULE packet
	 */
	UlePacket();

	/**
	 * Build an ULE packet
	 *
	 * @param type        the protocol type of the payload data
	 * @param address     the optional address to add in ULE header (specify NULL
	 *                    to not use ULE destination address field)
	 * @param crc_enabled is the CRC computing enabled
	 * @param payload  data of ULE payload
	 */
	UlePacket(uint16_t type, Data *address, Data payload, bool crc_enabled);

	/**
	 * Destroy the ULE packet
	 */
	~UlePacket();

	/**
	 * Check if the ULE packet is valid
	 *
	 * @param crc_enabled is the CRC computing enabled
	 * @return true if the packet is valied, false otherwise
	 */
	bool isValid(bool crc_enabled);

	// implementation of virtual functions
	uint16_t getTotalLength();
	uint16_t getPayloadLength();
	Data getPayload();
	uint8_t getQos();
	uint8_t getSrcTalId();
	uint8_t getDstTalId();

	/**
	 * Set the ULE packet source terminal ID
	 * since it cannot be stored in a header field
	 *
	 * @param tal_id The terminal ID
	 */
	void setSrcTalId(uint8_t tal_id);

	/**
	 * Set the ULE packet destination terminal ID
	 * since it cannot be stored in a header field
	 *
	 * @param tal_id The terminal ID
	 */
	void setDstTalId(uint8_t tal_id);

	/**
	 * Set the ULE packet QoS value because it cannot be stored
	 * in a header field
	 *
	 * @param QoS The QoS value
	 */
	void setQos(uint8_t qos);

	/**
	 * @brief Whether the Destination Address field of the ULE header is present
	 *        or not
	 *
	 * @return  true if the Destination Address field is present, false otherwise
	 */
	bool isDstAddrPresent();

	/**
	 * Get the Type field of the ULE header
	 *
	 * @return  the Type field of the ULE header
	 */
	uint16_t getPayloadType();

	/**
	 * Get the Destination Address field of the ULE header
	 *
	 * @return  the Destination Address field of the ULE header
	 */
	Data destAddr();

	/**
	 * Get the CRC field at the end of the ULE packet
	 *
	 * @return  the CRC field at the end of the ULE packet
	 */
	uint32_t crc();
};

#endif
