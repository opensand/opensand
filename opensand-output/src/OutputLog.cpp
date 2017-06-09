/*
 *
 * OpenSAND is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
 * Copyright © 2016 TAS
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
 * @file OutputLog.cpp
 * @brief The OutputLog class represent a log generated by the application.
 * @author Fabrice Hobaya <fhobaya@toulouse.viveris.com>
 */


#include "OutputLog.h"

#include <stdlib.h>
#include <string.h>

const char *OutputLog::levels[] =
{
	"[CRITICAL]",
	"[CRITICAL]",
	"[CRITICAL]",
	"   [ERROR]",
	" [WARNING]",
	"  [NOTICE]",
	"    [INFO]",
	"   [DEBUG]",
};

const int OutputLog::colors[] =
{
	41,
	41,
	41,
	31,
	33,
	34,
	34,
	32,
};



OutputLog::OutputLog(uint8_t id,
                     log_level_t display_level,
                     const string &name):
	id(id),
	name(name),
	display_level(display_level),
	spinlock()
	//mutex("log-" + name)
{
}

OutputLog::~OutputLog()
{
}

log_level_t OutputLog::getDisplayLevel(void) const
{
	OutputSLock lock(this->spinlock);
	//OutputLock lock(this->mutex);
	return this->display_level;
}

void OutputLog::setDisplayLevel(log_level_t level)
{
	OutputSLock lock(this->spinlock);
	//OutputLock lock(this->mutex);
	this->display_level = level;
}


