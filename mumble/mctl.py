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

class MumbleCtlBase (object):
	""" This class defines the base interface that the Mumble model expects. """
	
	cache = {};
	
	def getAllConf(self, srvid):
		raise NotImplementedError( "mctl::getAllConf" );
	
	def getVersion( self ):
		raise NotImplementedError( "mctl::getVersion" );
	
	def getConf(self, srvid, key):
		raise NotImplementedError( "mctl::getConf" );
	
	def setConf(self, srvid, key, value):
		raise NotImplementedError( "mctl::setConf" );
	
	def getDefaultConf(self):
		raise NotImplementedError( "mctl::getDefaultConf" );
	
	def newServer(self):
		raise NotImplementedError( "mctl::newServer" );
	
	def setSuperUserPassword(self, srvid, value):
		raise NotImplementedError( "mctl::setSuperUserPassword" );
	
	def start(self, srvid):
		raise NotImplementedError( "mctl::start" );
	
	def stop(self, srvid):
		raise NotImplementedError( "mctl::stop" );
	
	def isBooted(self, srvid):
		raise NotImplementedError( "mctl::isBooted" );
	
	def deleteServer(self, srvid):
		raise NotImplementedError( "mctl::deleteServer" );
	
	def getPlayers(self, srvid):
		raise NotImplementedError( "mctl::getPlayers" );
	
	def getRegisteredPlayers(self, srvid, filter):
		raise NotImplementedError( "mctl::getRegisteredPlayers" );
	
	def getChannels(self, srvid):
		raise NotImplementedError( "mctl::getChannels" );
	
	def registerPlayer(self, srvid, name, email, password):
		raise NotImplementedError( "mctl::registerPlayer" );
	
	def getRegistration(self, srvid, mumbleid):
		raise NotImplementedError( "mctl::getRegistration" );
	
	def setRegistration(self, srvid, mumbleid, name, email, password):
		raise NotImplementedError( "mctl::setRegistration" );
	
	def unregisterPlayer(self, srvid, mumbleid):
		raise NotImplementedError( "mctl::unregisterPlayer" );
	
	def getBootedServers(self):
		raise NotImplementedError( "mctl::getBootedServers" );
	
	def getAllServers(self):
		raise NotImplementedError( "mctl::getAllServers" );
	
	def getACL(self, srvid, channelid):
		raise NotImplementedError( "mctl::getACL" );
	
	def setACL(self, srvid, channelid, acl, groups, inherit):
		raise NotImplementedError( "mctl::setACL" );
	
	def getTexture(self, srvid, mumbleid):
		raise NotImplementedError( "mctl::getTexture" );
	
	def setTexture(self, srvid, mumbleid, infile):
		raise NotImplementedError( "mctl::setTexture" );
	
	def verifyPassword( self, srvid, username, password ):
		raise NotImplementedError( "mctl::verifyPassword" );
	
	@staticmethod
	def newInstance( connstring, slicefile ):
		""" Create a new CTL object for the given connstring. """
		
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
			ctl = MumbleCtlIce( connstring, slicefile )
		
		MumbleCtlBase.cache[connstring] = ctl;
		return ctl;
	
	@staticmethod
	def clearCache():
		MumbleCtlBase.cache = {};



