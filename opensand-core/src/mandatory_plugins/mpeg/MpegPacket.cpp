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
 * @file MpegPacket.cpp
 * @brief MPEG-2 TS packet
 * @author Didier Barvaux <didier.barvaux@toulouse.viveris.com>
 */

#include "MpegPacket.h"

#define DBG_PACKAGE PKG_DEFAULT
#include "opensand_conf/uti_debug.h"


MpegPacket::MpegPacket(unsigned char *data, unsigned int length):
                       NetPacket(data, length)
{
	this->name = "MPEG2-TS";
	this->type = NET_PROTO_MPEG;
	this->data.reserve(TS_PACKETSIZE);
	this->header_length = TS_HEADERSIZE;
}

MpegPacket::MpegPacket(Data data): NetPacket(data)
{
	this->name = "MPEG2-TS";
	this->type = NET_PROTO_MPEG;
	this->data.reserve(TS_PACKETSIZE);
	this->header_length = TS_HEADERSIZE;
}

MpegPacket::MpegPacket(): NetPacket()
{
	this->name = "MPEG2-TS";
	this->type = NET_PROTO_MPEG;
	this->data.reserve(TS_PACKETSIZE);
	this->header_length = TS_HEADERSIZE;
}

MpegPacket::~MpegPacket()
{
}

uint8_t MpegPacket::getQos()
{
	return (this->getPid() & 0x07);
}

uint8_t MpegPacket::getSrcTalId()
{
	return (this->getPid() >> 3) & 0x1F;
}

uint8_t MpegPacket::getDstTalId()
{
	return (this->getPid() >> 8) & 0x1F;
}

bool MpegPacket::isValid()
{
	const char FUNCNAME[] = "[MpegPacket::isValid]";

	/* check length */
	if(this->getTotalLength() != TS_PACKETSIZE)
	{
		UTI_ERROR("%s bad length (%d bytes)\n",
		          FUNCNAME, this->getTotalLength());
		goto bad;
	}

	/* check Synchonization byte */
	if(this->sync() != 0x47)
	{
		UTI_ERROR("%s bad sync byte (0x%02x)\n",
		          FUNCNAME, this->sync());
		goto bad;
	}

	/* check the Transport Error Indicator (TEI) bit */
	if(this->tei())
	{
		UTI_ERROR("%s TEI is on\n", FUNCNAME);
		goto bad;
	}

	/* check Transport Scrambling Control (TSC) bits */
	if(this->tsc() != 0)
	{
		UTI_ERROR("%s TSC is on\n", FUNCNAME);
		goto bad;
	}

	/* check Payload Pointer validity (if present) */
	if(this->pusi() && this->pp() >= (TS_DATASIZE - 1))
	{
		UTI_ERROR("%s bad payload pointer (PUSI set and PP = 0x%02x)\n",
		          FUNCNAME, this->pp());
		goto bad;
	}

	return true;

bad:
	return false;
}

uint16_t MpegPacket::getTotalLength()
{
	return this->data.length();
}

uint16_t MpegPacket::getPayloadLength()
{
	return (this->getTotalLength() - TS_HEADERSIZE);
}

Data MpegPacket::getPayload()
{
	return Data(this->data, TS_HEADERSIZE,
	            this->getPayloadLength());
}

uint8_t MpegPacket::sync()
{
	return this->data.at(0) & 0xff;
}

bool MpegPacket::tei()
{
	return (this->data.at(1) & 0x80) != 0;
}

bool MpegPacket::pusi()
{
	return (this->data.at(1) & 0x40) != 0;
}

bool MpegPacket::tp()
{
	return (this->data.at(1) & 0x20) != 0;
}

uint16_t MpegPacket::getPid()
{
	return (uint16_t) (((this->data.at(1) & 0x1f) << 8) +
	                   ((this->data.at(2) & 0xff) << 0));
}

uint8_t MpegPacket::tsc()
{
	return (this->data.at(3) & 0xC0);
}

uint8_t MpegPacket::cc()
{
	return (this->data.at(3) & 0x0f);
}

uint8_t MpegPacket::pp()
{
	return (this->data.at(4) & 0xff);
}

// static
uint16_t MpegPacket::getPidFromPacket(NetPacket *packet)
{
	uint8_t qos = packet->getQos();
	uint8_t src_tal_id = packet->getSrcTalId();
	uint8_t dst_tal_id = packet->getDstTalId();

	uint16_t pid = 0;

	return pid | ((dst_tal_id & 0x1F) << 8)
	           | ((src_tal_id & 0x1F) << 3)
	           | (qos & 0x07);
}