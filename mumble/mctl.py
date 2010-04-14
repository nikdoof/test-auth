# -*- coding: utf-8 -*-

"""
 *  Copyright © 2009, withgod                   <withgod@sourceforge.net>
 *         2009-2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 *
 *  Mumble-Django is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

import re

class MumbleCtlBase(object):
	""" This class defines the base interface that the Mumble model expects. """
	
	cache = {};
	
	@staticmethod
	def newInstance( connstring, slicefile=None, icesecret=None ):
		""" Create a new CTL object for the given connstring.
		
		    Optional parameters are the path to the slice file and the
		    Ice secret necessary to authenticate to Murmur.
		
		    The path can be omitted only if using DBus or running Murmur
		    1.2.3 or later, which exports a getSlice method to retrieve
		    the Slice from.
		"""
		
		# check cache
		if connstring in MumbleCtlBase.cache:
			return MumbleCtlBase.cache[connstring];
		
		# connstring defines whether to connect via ICE or DBus.
		# Dbus service names: some.words.divided.by.periods
		# ICE specs are WAY more complex, so if DBus doesn't match, use ICE.
		rd = re.compile( r'^(\w+\.)*\w+$' );
		
		if rd.match( connstring ):
			from MumbleCtlDbus import MumbleCtlDbus
			ctl = MumbleCtlDbus( connstring )
		else:
			from MumbleCtlIce import MumbleCtlIce
			ctl = MumbleCtlIce( connstring, slicefile, icesecret )
		
		MumbleCtlBase.cache[connstring] = ctl;
		return ctl;
	
	@staticmethod
	def clearCache():
		MumbleCtlBase.cache = {};
