# -*- coding: utf-8 -*-

"""
 *  Copyright © 2009-2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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

from django.conf		import settings
from django.test		import TestCase

from models			import Mumble
from utils			import ObjectInfo


class InstancesHandling( TestCase ):
	""" Tests creation, editing and removing of vserver instances. """
	
	def setUp( self ):
		# Make sure we always start with a FRESH murmur instance, checking for left-over instances
		# and deleting them before creating ours.
		try:
			self.murmur = Mumble.objects.get( addr="0.0.0.0", port=31337 );
		except Mumble.DoesNotExist:
			pass
		else:
			self.murmur.delete();
		finally:
			self.murmur = Mumble( name="#unit testing instance#", addr="0.0.0.0", port=31337 );
			self.murmur.save();
	
	def testDefaultConf( self ):
		conf = self.murmur.ctl.getAllConf( self.murmur.srvid );
		
		self.assert_( type(conf) == dict );
		self.assert_( "host"             in conf );
		self.assert_( "port"             in conf );
		self.assert_( "certificate"      in conf );
		self.assert_( "key"              in conf );
		self.assert_( "registerhostname" in conf );
		self.assert_( "registername"     in conf );
		self.assert_( "channelname"      in conf );
		self.assert_( "username"         in conf );
		self.assert_( "obfuscate"        in conf );
		self.assert_( "defaultchannel"   in conf );
	
	def testAddrPortUnique( self ):
		try:
			duplicate = Mumble(
				name="#another unit testing instance#",
				addr=self.murmur.addr, port=self.murmur.port,
				dbus=settings.DEFAULT_CONN
				);
			if duplicate.ctl.method == "ICE":
				import Murmur
				self.assertRaises( Murmur.ServerFailureException, duplicate.save );
			elif self.murmur.version[:2] == [ 1, 2 ]:
				from dbus import DBusException
				self.assertRaises( DBusException, duplicate.save );
			else:
				from sqlite3 import IntegrityError
				self.assertRaises( IntegrityError, duplicate.save );
		finally:
			# make sure the duplicate is removed
			duplicate.ctl.deleteServer( duplicate.srvid );
	
	def tearDown( self ):
		self.murmur.delete();


class DataReading( TestCase ):
	""" Tests reading data from murmur using the low-level CTL methods. """
	
	def setUp( self ):
		# BIG FAT WARNING: This sucks ass, because it assumes the tester has a
		# Murmur database like the one I have.
		# I definitely need to prepare Murmur somehow before running these tests.
		# Just don't yet know how.
		self.murmur = Mumble.objects.get(id=1);
	
	
	def testCtlGetChannels( self ):
		""" Test getChannels() """
		
		channels = self.murmur.ctl.getChannels( self.murmur.srvid );
		
		if self.murmur.ctl.method == "ICE":
			import Murmur
			self.assertEquals( type( channels[0] ), Murmur.Channel );
		else:
			self.assertEquals( type( channels[0] ), ObjectInfo );
		
		self.assert_( hasattr( channels[0], "id"     ) );
		self.assert_( hasattr( channels[0], "name"   ) );
		self.assert_( hasattr( channels[0], "parent" ) );
		self.assert_( hasattr( channels[0], "links"  ) );
	
	
	def testCtlGetPlayers( self ):
		""" Test getPlayers() """
		
		players = self.murmur.ctl.getPlayers( self.murmur.srvid );
		
		self.assert_( len(players) > 0 );
		
		self.assertEquals( type(players), dict );
		
		for plidx in players:
			player = players[plidx];
			
			if self.murmur.ctl.method == "ICE" and self.murmur.version[:2] == ( 1, 2 ):
				import Murmur
				self.assertEquals( type( player ), Murmur.User );
			else:
				self.assertEquals( type( player ), ObjectInfo );
			
			self.assert_( hasattr( player, "session" ) );
			self.assert_( hasattr( player, "mute" ) );
			self.assert_( hasattr( player, "deaf" ) );
			self.assert_( hasattr( player, "selfMute" ) );
			self.assert_( hasattr( player, "selfDeaf" ) );
			self.assert_( hasattr( player, "channel" ) );
			self.assert_( hasattr( player, "userid" ) );
			self.assert_( hasattr( player, "name" ) );
			self.assert_( hasattr( player, "onlinesecs" ) );
			self.assert_( hasattr( player, "bytespersec" ) );
	
	
	def testCtlGetRegisteredPlayers( self ):
		""" Test getRegistredPlayers() and getRegistration() """
		
		players = self.murmur.ctl.getRegisteredPlayers( self.murmur.srvid );
		
		self.assert_( len(players) > 0 );
		
		self.assertEquals( type(players), dict );
		
		for plidx in players:
			player = players[plidx];
			
			self.assertEquals( type( player ), ObjectInfo );
			
			self.assert_( hasattr( player, "userid" ) );
			self.assert_( hasattr( player, "name"   ) );
			self.assert_( hasattr( player, "email"  ) );
			self.assert_( hasattr( player, "pw"     ) );
			
			# compare with getRegistration result
			reg = self.murmur.ctl.getRegistration( self.murmur.srvid, player.userid );
			
			self.assertEquals( type( reg ), ObjectInfo );
			
			self.assert_( hasattr( reg, "userid" ) );
			self.assert_( hasattr( reg, "name"   ) );
			self.assert_( hasattr( reg, "email"  ) );
			self.assert_( hasattr( reg, "pw"     ) );
			
			self.assertEquals( player.userid, reg.userid );
			self.assertEquals( player.name,   reg.name   );
			self.assertEquals( player.email,  reg.email  );
			self.assertEquals( player.pw,     reg.pw     );
	
	
	def testCtlGetAcl( self ):
		""" Test getACL() for the root channel """
		
		acls, groups, inherit = self.murmur.ctl.getACL( self.murmur.srvid, 0 );
		
		for rule in acls:
			if self.murmur.ctl.method == "ICE" and self.murmur.version[:2] == ( 1, 2 ):
				import Murmur
				self.assertEquals( type( rule ), Murmur.ACL );
			else:
				self.assertEquals( type( rule ), ObjectInfo );
			
			self.assert_( hasattr( rule, "applyHere" ) );
			self.assert_( hasattr( rule, "applySubs" ) );
			self.assert_( hasattr( rule, "inherited" ) );
			self.assert_( hasattr( rule, "userid"    ) );
			self.assert_( hasattr( rule, "group"     ) );
			self.assert_( hasattr( rule, "allow"     ) );
			self.assert_( hasattr( rule, "deny"      ) );
		
		for grp in groups:
			if self.murmur.ctl.method == "ICE":
				import Murmur
				self.assertEquals( type( grp ), Murmur.Group );
			else:
				self.assertEquals( type( grp ), ObjectInfo );
			
			self.assert_( hasattr( grp,  "name"        ) );
			self.assert_( hasattr( grp,  "inherited"   ) );
			self.assert_( hasattr( grp,  "inherit"     ) );
			self.assert_( hasattr( grp,  "inheritable" ) );
			self.assert_( hasattr( grp,  "add"         ) );
			self.assert_( hasattr( grp,  "remove"      ) );
			self.assert_( hasattr( grp,  "members"     ) );



