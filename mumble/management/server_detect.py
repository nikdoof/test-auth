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

import os, getpass

from django.db		import DatabaseError
from django.conf	import settings

from mumble.models	import MumbleServer, Mumble
from mumble.mctl	import MumbleCtlBase


def find_in_dicts( keys, conf, default, valueIfNotFound=None ):
	if not isinstance( keys, tuple ):
		keys = ( keys, );

	for keyword in keys:
		if keyword in conf:
			return conf[keyword];

	for keyword in keys:
		keyword = keyword.lower();
		if keyword in default:
			return default[keyword];

	return valueIfNotFound;


def find_existing_instances( **kwargs ):
	if "verbosity" in kwargs:
		v = kwargs['verbosity'];
	else:
		v = 1;
	
	if v > 1:
		print "Starting Mumble servers and players detection now.";
	
	triedEnviron = False;
	online = False;
	while not online:
		if not triedEnviron and 'MURMUR_CONNSTR' in os.environ:
			dbusName = os.environ['MURMUR_CONNSTR'];
			triedEnviron = True;
			if v > 1:
				print "Trying environment setting", dbusName;
		else:
			print "--- Murmur connection info ---"
			print "  1) DBus -- net.sourceforge.mumble.murmur"
			print "  2) ICE  -- Meta:tcp -h 127.0.0.1 -p 6502"
			print "Enter 1 or 2 for the defaults above, nothing to skip Server detection,"
			print "and if the defaults do not fit your needs, enter the correct string."
			print "Whether to use DBus or Ice will be detected automatically from the"
			print "string's format."
			print
			
			dbusName = raw_input( "Service string: " ).strip();
		
		if not dbusName:
			if v:
				print 'Be sure to run "python manage.py syncdb" with Murmur running before'
				print "trying to use this app! Otherwise, existing Murmur servers won't be"
				print 'configurable!';
			return False;
		elif dbusName == "1":
			dbusName = "net.sourceforge.mumble.murmur";
		elif dbusName == "2":
			dbusName = "Meta:tcp -h 127.0.0.1 -p 6502";
		
		icesecret = getpass.getpass("Please enter the Ice secret (if any): ");
		
		try:
			ctl = MumbleCtlBase.newInstance( dbusName, settings.SLICE, icesecret );
		except Exception, instance:
			if v:
				print "Unable to connect using name %s. The error was:" % dbusName;
				print instance;
				print
		else:
			online = True;
			if v > 1:
				print "Successfully connected to Murmur via connection string %s, using %s." % ( dbusName, ctl.method );
	
	servIDs   = ctl.getAllServers();
	
	try:
		meta = MumbleServer.objects.get( dbus=dbusName );
	except MumbleServer.DoesNotExist:
		meta = MumbleServer( dbus=dbusName );
	finally:
		meta.secret = icesecret;
		meta.save();
	
	for id in servIDs:
		if v > 1:
			print "Checking Murmur instance with id %d." % id;
		# first check that the server has not yet been inserted into the DB
		try:
			instance = Mumble.objects.get( server=meta, srvid=id );
		except Mumble.DoesNotExist:
			values = {
				"server":  meta,
				"srvid":   id,
				}
			
			if v:
				print "Found new Murmur instance %d on bus '%s'... " % ( id, dbusName )
			
			# now create a model for the record set.
			instance = Mumble( **values );
		else:
			if v:
				print "Syncing Murmur instance %d: '%s'... " % ( instance.id, instance.name )
		
		try:
			instance.configureFromMurmur();
		except DatabaseError, err:
			try:
				# Find instances with the same address/port
				dup = Mumble.objects.get( addr=instance.addr, port=instance.port )
			except Mumble.DoesNotExist:
				# None exist - this must've been something else.
				print "Server ID / Name: %d / %s" % ( instance.srvid, instance.name )
				raise err
			else:
				print "ERROR: There is already another server instance registered"
				print "       on the same address and port."
				print "        -------------"
				print "        New Server ID:", instance.srvid,
				print "      New Server Name:", instance.name
				print "              Address:", instance.addr
				print "                 Port:", instance.port
				print "    Connection string:", instance.server.dbus
				print "        -------------"
				print "  Duplicate Server ID:", dup.srvid,
				print "Duplicate Server Name:", dup.name
				print "              Address:", dup.addr
				print "                 Port:", dup.port
				print "    Connection string:", dup.server.dbus
				return False
		except Exception, err:
			print "Server ID / Name: %d / %s" % ( instance.srvid, instance.name )
			raise err
		
		# Now search for players on this server that have not yet been registered
		if instance.booted:
			if v > 1:
				print "Looking for registered Players on Server id %d." % id;
			instance.readUsersFromMurmur( verbose=v );
		elif v:
			print "This server is not running, can't sync players.";
	
	if v > 1:
		print "Successfully finished Servers and Players detection.";
	return True;


