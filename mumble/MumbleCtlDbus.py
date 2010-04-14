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

from PIL	import Image
from struct	import pack, unpack
from zlib	import compress, decompress

from mctl	import MumbleCtlBase
from utils	import ObjectInfo

import dbus
from dbus.exceptions import DBusException


def MumbleCtlDbus( connstring ):
	""" Choose the correct DBus handler (1.1.8 or legacy) to use. """
	
	meta = dbus.Interface( dbus.SystemBus().get_object( connstring, '/' ), 'net.sourceforge.mumble.Meta' );
	
	try:
		meta.getVersion();
	except DBusException:
		return MumbleCtlDbus_Legacy( connstring, meta );
	else:
		return MumbleCtlDbus_118( connstring, meta );


class MumbleCtlDbus_118(MumbleCtlBase):
	method = "DBus";
	
	def __init__( self, connstring, meta ):
		self.dbus_base = connstring;
		self.meta = meta;
	
	def _getDbusMeta( self ):
		return self.meta;
	
	def _getDbusServerObject( self, srvid):
		if srvid not in self.getBootedServers():
			raise SystemError, 'No murmur process with the given server ID (%d) is running and attached to system dbus under %s.' % ( srvid, self.meta );
		
		return dbus.Interface( dbus.SystemBus().get_object( self.dbus_base, '/%d' % srvid ), 'net.sourceforge.mumble.Murmur' );
	
	def getVersion( self ):
		return MumbleCtlDbus_118.convertDbusTypeToNative( self.meta.getVersion() );
	
	def getAllConf(self, srvid):
		conf = self.meta.getAllConf(dbus.Int32(srvid))
		
		info = {};
		for key in conf:
			if key == "playername":
				info['username'] = conf[key];
			else:
				info[str(key)] = conf[key];
		return info;
	
	def getConf(self, srvid, key):
		if key == "username":
			key = "playername";
		
		return self.meta.getConf(dbus.Int32( srvid ), key)
	
	def setConf(self, srvid, key, value):
		if key == "username":
			key = "playername";
		
		self.meta.setConf(dbus.Int32( srvid ), key, value)
	
	def getDefaultConf(self):
		conf = self.meta.getDefaultConf()
		
		info = {};
		for key in conf:
			if key == "playername":
				info['username'] = conf[key];
			else:
				info[str(key)] = conf[key];
		return info;
	
	def start( self, srvid ):
		self.meta.start( srvid );
	
	def stop( self, srvid ):
		self.meta.stop( srvid );
	
	def isBooted( self, srvid ):
		return bool( self.meta.isBooted( srvid ) );
	
	def deleteServer( self, srvid ):
		srvid = dbus.Int32( srvid )
		if self.meta.isBooted( srvid ):
			self.meta.stop( srvid )
		
		self.meta.deleteServer( srvid )
	
	def newServer(self):
		return self.meta.newServer()
	
	def registerPlayer(self, srvid, name, email, password):
		mumbleid = int( self._getDbusServerObject(srvid).registerPlayer(name) );
		self.setRegistration( srvid, mumbleid, name, email, password );
		return mumbleid;
	
	def unregisterPlayer(self, srvid, mumbleid):
		self._getDbusServerObject(srvid).unregisterPlayer(dbus.Int32( mumbleid ))
	
	def getChannels(self, srvid):
		chans = self._getDbusServerObject(srvid).getChannels()
		
		ret = {};
		
		for channel in chans:
			print channel;
			ret[ channel[0] ] = ObjectInfo(
				id     = int(channel[0]),
				name   = unicode(channel[1]),
				parent = int(channel[2]),
				links  = [ int(lnk) for lnk in channel[3] ],
				);
		
		return ret;
	
	def getPlayers(self, srvid):
		players = self._getDbusServerObject(srvid).getPlayers();
		
		ret = {};
		
		for playerObj in players:
			ret[ int(playerObj[0]) ] = ObjectInfo(
				session      =  int( playerObj[0] ),
				mute         = bool( playerObj[1] ),
				deaf         = bool( playerObj[2] ),
				suppress     = bool( playerObj[3] ),
				selfMute     = bool( playerObj[4] ),
				selfDeaf     = bool( playerObj[5] ),
				channel      =  int( playerObj[6] ),
				userid       =  int( playerObj[7] ),
				name         = unicode( playerObj[8] ),
				onlinesecs   =  int( playerObj[9] ),
				bytespersec  =  int( playerObj[10] )
				);
		
		return ret;
	
	def getRegisteredPlayers(self, srvid, filter = ''):
		users = self._getDbusServerObject(srvid).getRegisteredPlayers( filter );
		ret = {};
		
		for user in users:
			ret[int(user[0])] = ObjectInfo(
				userid =     int( user[0] ),
				name   = unicode( user[1] ),
				email  = unicode( user[2] ),
				pw     = unicode( user[3] )
				);
		
		return ret
	
	def getACL(self, srvid, channelid):
		raw_acls, raw_groups, raw_inherit = self._getDbusServerObject(srvid).getACL(channelid)
		
		acls =  [ ObjectInfo(
				applyHere = bool(rule[0]),
				applySubs = bool(rule[1]),
				inherited = bool(rule[2]),
				userid    =  int(rule[3]),
				group     = unicode(rule[4]),
				allow     =  int(rule[5]),
				deny      =  int(rule[6]),
				)
			for rule in raw_acls
			];
		
		groups = [ ObjectInfo(
				name        = unicode(group[0]),
				inherited   = bool(group[1]),
				inherit     = bool(group[2]),
				inheritable = bool(group[3]),
				add         = [ int(usrid) for usrid in group[4] ],
				remove      = [ int(usrid) for usrid in group[5] ],
				members     = [ int(usrid) for usrid in group[6] ],
				)
			for group in raw_groups
			];
		
		return acls, groups, bool(raw_inherit);
	
	def setACL(self, srvid, channelid, acls, groups, inherit):
		# Pack acl ObjectInfo into a tuple and send that over dbus
		dbus_acls = [
			( rule.applyHere, rule.applySubs, rule.inherited, rule.userid, rule.group, rule.allow, rule.deny )
			for rule in acls
			];
		
		dbus_groups = [
			( group.name, group.inherited, group.inherit, group.inheritable, group.add, group.remove, group.members )
			for group in groups
			];
		
		return self._getDbusServerObject(srvid).setACL( channelid, dbus_acls, dbus_groups, inherit );
	
	def getBootedServers(self):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self.meta.getBootedServers())
	
	def getAllServers(self):
		return MumbleCtlDbus_118.convertDbusTypeToNative(self.meta.getAllServers())
	
	def setSuperUserPassword(self, srvid, value):
		self.meta.setSuperUserPassword(dbus.Int32(srvid), value)
	
	def getRegistration(self, srvid, mumbleid):
		user = self._getDbusServerObject(srvid).getRegistration(dbus.Int32(mumbleid))
		return ObjectInfo(
			userid = mumbleid,
			name   = unicode(user[1]),
			email  = unicode(user[2]),
			pw     = '',
			);
	
	def setRegistration(self, srvid, mumbleid, name, email, password):
		return MumbleCtlDbus_118.convertDbusTypeToNative(
			self._getDbusServerObject(srvid).setRegistration(dbus.Int32(mumbleid), name, email, password)
			)
	
	def getTexture(self, srvid, mumbleid):
		texture = self._getDbusServerObject(srvid).getTexture(dbus.Int32(mumbleid));
		
		if len(texture) == 0:
			raise ValueError( "No Texture has been set." );
		# this returns a list of bytes.
		# first 4 bytes: Length of uncompressed string, rest: compressed data
		orig_len = ( texture[0] << 24 ) | ( texture[1] << 16 ) | ( texture[2] << 8 ) | ( texture[3] );
		# convert rest to string and run decompress
		bytestr = "";
		for byte in texture[4:]:
			bytestr += pack( "B", int(byte) );
		decompressed = decompress( bytestr );
		# iterate over 4 byte chunks of the string
		imgdata = "";
		for idx in range( 0, orig_len, 4 ):
			# read 4 bytes = BGRA and convert to RGBA
			bgra = unpack( "4B", decompressed[idx:idx+4] );
			imgdata += pack( "4B",  bgra[2], bgra[1], bgra[0], bgra[3] );
		
		# return an 600x60 RGBA image object created from the data
		return Image.fromstring( "RGBA", ( 600, 60 ), imgdata);
	
	def setTexture(self, srvid, mumbleid, infile):
		# open image, convert to RGBA, and resize to 600x60
		img = infile.convert( "RGBA" ).transform( ( 600, 60 ), Image.EXTENT, ( 0, 0, 600, 60 ) );
		# iterate over the list and pack everything into a string
		bgrastring = "";
		for ent in list( img.getdata() ):
			# ent is in RGBA format, but Murmur wants BGRA (ARGB inverse), so stuff needs
			# to be reordered when passed to pack()
			bgrastring += pack( "4B",  ent[2], ent[1], ent[0], ent[3] );
		# compress using zlib
		compressed = compress( bgrastring );
		# pack the original length in 4 byte big endian, and concat the compressed
		# data to it to emulate qCompress().
		texture = pack( ">L", len(bgrastring) ) + compressed;
		# finally call murmur and set the texture
		self._getDbusServerObject(srvid).setTexture(dbus.Int32( mumbleid ), texture)
	
	def verifyPassword( self, srvid, username, password ):
		player = self.getRegisteredPlayers( srvid, username );
		if not player:
			return -2;
		
		ok = MumbleCtlDbus_118.convertDbusTypeToNative(
			self._getDbusServerObject(srvid).verifyPassword( dbus.Int32( player[0].userid ), password )
			);
		
		if ok:
			return player[0].userid;
		else:
			return -1;
	
	@staticmethod
	def convertDbusTypeToNative(data):
		#i know dbus.* type is extends python native type.
		#but dbus.* type is not native type.  it's not good transparent for using Ice/Dbus.
		ret = None
		
		if isinstance(data, tuple) or type(data) is data.__class__ is dbus.Array or data.__class__ is dbus.Struct:
			ret = []
			for x in data:
				ret.append(MumbleCtlDbus_118.convertDbusTypeToNative(x))
		elif data.__class__ is dbus.Dictionary:
			ret = {}
			for x in data.items():
				ret[MumbleCtlDbus_118.convertDbusTypeToNative(x[0])] = MumbleCtlDbus_118.convertDbusTypeToNative(x[1])
		else:
			if data.__class__ is dbus.Boolean:
				ret = bool(data)
			elif data.__class__  is dbus.String:
				ret = unicode(data)
			elif data.__class__  is dbus.Int32 or data.__class__ is dbus.UInt32:
				ret = int(data)
			elif data.__class__ is dbus.Byte:
				ret = int(data)
		return ret


class MumbleCtlDbus_Legacy( MumbleCtlDbus_118 ):
	def getVersion( self ):
		return ( 1, 1, 4, u"1.1.4" );
	
	def setRegistration(self, srvid, mumbleid, name, email, password):
		return MumbleCtlDbus_118.convertDbusTypeToNative(
			self._getDbusServerObject(srvid).updateRegistration( ( dbus.Int32(mumbleid), name, email, password ) )
			)




