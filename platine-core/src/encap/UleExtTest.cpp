/*
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
 * @file UleExtTest.cpp
 * @brief Mandatory Test SNDU ULE extension
 * @author Didier Barvaux <didier.barvaux@toulouse.viveris.com>
 */

#include "UleExtTest.h"

#define DBG_PACKAGE PKG_DEFAULT
#include "platine_conf/uti_debug.h"


UleExtTest::UleExtTest(): UleExt()
{
	this->is_mandatory = true;
	this->_type = 0x00;
}

UleExtTest::~UleExtTest()
{
}

ule_ext_status UleExtTest::build(uint16_t ptype, Data payload)
{
	// payload does not change
	this->_payload = payload;

	// type is Test SNDU extension
	//  - 5-bit zero prefix
	//  - 3-bit H-LEN field (= 0 because extension is mandatory)
	//  - 8-bit H-Type field (= 0x00 type of Test SNDU extension)
	this->_payloadType = this->type();

	return ULE_EXT_OK;
}

ule_ext_status UleExtTest::decode(uint8_t hlen, Data payload)
{
	const char FUNCNAME[] = "[UleExtTest::decode]";

	// extension is mandatory, hlen must be 0
	if(hlen != 0)
	{
		UTI_ERROR("%s mandatory extension, but hlen (0x%x) != 0\n",
		          FUNCNAME, hlen);
		goto error;
	}

	// always discard the SNDU according to section 5.1 in RFC 4326
	return ULE_EXT_DISCARD;

error:
	return ULE_EXT_ERROR;
}
