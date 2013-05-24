/*
 *
 * OpenSAND is an emulation testbed aiming to represent in a cost effective way a
 * satellite telecommunication system for research and engineering activities.
 *
 *
 * Copyright © 2013 TAS
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
 * @file RtEvent.h
 * @author Cyrille GAILLARDET / <cgaillardet@toulouse.viveris.com>
 * @author Julien BERNARD / <jbernard@toulouse.viveris.com>
 * @brief  The generic event
 *
 */


#ifndef RT_EVENT_H
#define RT_EVENT_H


#include <sys/time.h>
#include <string>

#include "stdlib.h"

#include "Types.h"

using std::string;

/**
  * @class RtEvent
  * @brief virtual class that Events are based on
  *
  */
class RtEvent
{
  public:

	/**
	 * @brief RtEvent constructor
	 *
	 * @aram type       The type of event
	 * @param name      The name of the event
	 * @param fd        The file descriptor to monitor for the event
	 * @param priority  The priority of the event
	 */
	RtEvent(event_type_t type, const string &name, int32_t fd, uint8_t priority);
	virtual ~RtEvent();

	/**
	 * @brief Get the type of the event
	 *
	 * @return the type of the event
	 */
	event_type_t getType(void) const {return this->type;};

	/**
	 * @brief Get the time since event creation
	 *
	 * @return the time elapsed since event creation
	 */
	timeval getElapsedTime(void) const;

	/**
	 * @brief Get the event priority
	 *
	 * @return the event priority
	 */
	uint8_t getPriority(void) const {return this->priority;};

	/**
	 * @brief Get the event name
	 *
	 * @return the event name
	 *
	 */
	string getName(void) const {return this->name;};

	/**
	 * @brief Get the file descriptor on the event
	 *
	 * @return the event file descriptor
	 */
	int32_t getFd(void) const {return this->fd;};
	
	/**
	 * @brief This event was received, handle it
	 * 
	 * @return true on success, false otherwise
	 */
	virtual bool handle(void) = 0;

	/**
	 * @brief Update the creation time
	 *
	 */
	void setCreationTime(void);

	/// operator < used by sort on events priority
	bool operator<(const RtEvent *event) const
	{   
		return (this->priority < event->priority);
	}   

	/// operator == used to check if the event id corresponds
	bool operator==(const event_id_t id) const
	{
		return (this->fd == id);
	}

	/// operator != used to check if the event id corresponds
	bool operator!=(const event_id_t id) const
	{
		return (this->fd != id);
	}

  protected:

	/// type of event, for now Message, Signal, Timer or NetSocket
	event_type_t type;

	/// event name
	const string name;

	/// Event input file descriptor
	int32_t fd;

	/// Event priority
	uint8_t priority;

	/// date, used by default as event creation date
	timeval creation_time;
};

#endif