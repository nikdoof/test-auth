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

import os, subprocess, signal
from select		import select
from os.path		import join, exists
from shutil		import copyfile

from django.conf	import settings

from utils		import ObjectInfo

def get_available_versions():
	""" Return murmur versions installed inside the LAB_DIR. """
	dirs = os.listdir( settings.TEST_MURMUR_LAB_DIR );
	dirs.sort();
	return dirs;


def run_callback( version, callback, *args, **kwargs ):
	""" Initialize the database and run murmur, then call the callback.
	    After the callback has returned, kill murmur.
	
	    The callback will be passed the Popen object that wraps murmur,
	    and any arguments that were passed to run_callback.
	
	    If the callback raises an exception, murmur will still be properly
	    shutdown and the exception will be reraised.
	
	    The callback can either return an arbitrary value, or a tuple.
	    If it returns a tuple, it must be of the form:
	
	        ( <any> intended_return_value, <bool> call_update_dbase )
	
	    That means: If the second value evaluates to True, update_dbase
	    will be called; the first value will be returned by run_callback.
	
	    If the callback returns anything other than a tuple, that value
	    will be returned directly.
	
	    So, If run_callback should return a tuple, you will need to return
	    the tuple form mentioned above in the callback, and put your tuple
	    into the first parameter.
	"""
	
	murmur_root = join( settings.TEST_MURMUR_LAB_DIR, version );
	if not exists( murmur_root ):
		raise EnvironmentError( "This version could not be found: '%s' does not exist!" % murmur_root );
	
	init_dbase( version );
	
	process = run_murmur( version );
	
	try:
		result = callback( process, *args, **kwargs );
		if type(result) == tuple:
			if result[1]:
				update_dbase( version );
			return result[0];
		else:
			return result;
	finally:
		kill_murmur( process );


def init_dbase( version ):
	""" Initialize Murmur's database by copying the one from FILES_DIR. """
	dbasefile = join( settings.TEST_MURMUR_FILES_DIR, "murmur-%s.db3" % version );
	if not exists( dbasefile ):
		raise EnvironmentError( "This version could not be found: '%s' does not exist!" % dbasefile );
	murmurfile = join( settings.TEST_MURMUR_LAB_DIR, version, "murmur.sqlite" );
	copyfile( dbasefile, murmurfile );


def update_dbase( version ):
	""" Copy Murmur's database to FILES_DIR (the inverse of init_dbase). """
	murmurfile = join( settings.TEST_MURMUR_LAB_DIR, version, "murmur.sqlite" );
	if not exists( murmurfile ):
		raise EnvironmentError( "Murmur's database could not be found: '%s' does not exist!" % murmurfile );
	dbasefile = join( settings.TEST_MURMUR_FILES_DIR, "murmur-%s.db3" % version );
	copyfile( murmurfile, dbasefile );


def run_murmur( version ):
	""" Run the given Murmur version as a subprocess.
	
	    Either returns a Popen object or raises an EnvironmentError.
	"""
	
	murmur_root = join( settings.TEST_MURMUR_LAB_DIR, version );
	if not exists( murmur_root ):
		raise EnvironmentError( "This version could not be found: '%s' does not exist!" % murmur_root );
	
	binary_candidates = ( 'murmur.64', 'murmur.x86', 'murmurd' );
	
	for binname in binary_candidates:
		if exists( join( murmur_root, binname ) ):
			process = subprocess.Popen(
				( join( murmur_root, binname ), '-fg' ),
				stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
				cwd=murmur_root
				);
			
			# Check capabilities by waiting for certain lines to show up.
			capa = ObjectInfo( has_dbus=False, has_ice=False, has_instance=False, has_users=False );
			
			def canRead( self, timeout=1 ):
				rdy_read, rdy_write, rdy_other = select( [self.stdout], [], [], timeout );
				return self.stdout in rdy_read;
			
			setattr(subprocess.Popen, 'canRead', canRead)
			
			while process.canRead(0.5):
				line = process.stdout.readline();
				#print "read line:", line
				if   line == 'DBus registration succeeded\n':
					capa.has_dbus = True;
				elif line == 'MurmurIce: Endpoint "tcp -h 127.0.0.1 -p 6502" running\n':
					capa.has_ice = True;
				elif line == '1 => Server listening on 0.0.0.0:64738\n':
					capa.has_instance = True;
				elif "> Authenticated\n" in line:
					capa.has_users = True;
			
			process.capabilities = capa;
			
			return process;
	
	raise EnvironmentError( "Murmur binary not found. (Tried %s)" % unicode(binary_candidates) );


def wait_for_user( process, timeout=1 ):
	""" Wait for a user to connect. This call will consume any output from murmur
	    until a line indicating a user's attempt to connect has been found.
	
	    The timeout parameter specifies how long (in seconds) to wait for input.
	    It defaults to 1 second. If you set this to 0 it will return at the end
	    of input (and thereby tell you if a player has already connected). If
	    you set this to None, the call will block until a player has connected.
	
	    Returns True if a user has connected before the timeout has been hit,
	    False otherwise.
	"""
	while process.canRead( timeout ):
		line = process.stdout.readline();
		if "> Authenticated\n" in line:
			process.capabilities.has_users = True;
			return True;
	return False;


def kill_murmur( process ):
	""" Send a sigterm to the given process. """
	return os.kill( process.pid, signal.SIGTERM );


class MumbleCommandWrapper_noargs( object ):
	""" Mixin used to run a standard Django command inside MurmurEnvUtils.
	
	    To modify a standard Django command for MEU, you will need to create
	    a new command and derive its Command class from the wrapper, and the
	    Command class of the original command:
	
	    from django.core.management.commands.shell  import Command as ShellCommand
	    from mumble.murmurenvutils                  import MumbleCommandWrapper
	
	    class Command( MumbleCommandWrapper, ShellCommand ):
	        pass
	
	    That will run the original command, after the user has had the chance to
	    select the version of Murmur to run.
	"""
	
	def _choose_version( self ):
		print "Choose version:";
		
		vv = get_available_versions();
		for idx in range(len(vv)):
			print "  #%d %s" % ( idx, vv[idx] );
		
		chosen = int( raw_input("#> ") );
		
		return vv[chosen];
	
	def handle_noargs( self, **options ):
		self.origOpts = options;
		
		run_callback( self._choose_version(), self.runOrig );
	
	def runOrig( self, proc ):
		super( MumbleCommandWrapper_noargs, self ).handle_noargs( **self.origOpts );


class MumbleCommandWrapper( object ):
	""" Mixin used to run a standard Django command inside MurmurEnvUtils.
	
	    To modify a standard Django command for MEU, you will need to create
	    a new command and derive its Command class from the wrapper, and the
	    Command class of the original command:
	
	    from django.core.management.commands.shell  import Command as ShellCommand
	    from mumble.murmurenvutils                  import MumbleCommandWrapper
	
	    class Command( MumbleCommandWrapper, ShellCommand ):
	        pass
	
	    That will run the original command, after the user has had the chance to
	    select the version of Murmur to run.
	"""
	
	def _choose_version( self ):
		print "Choose version:";
		
		vv = get_available_versions();
		for idx in range(len(vv)):
			print "  #%d %s" % ( idx, vv[idx] );
		
		chosen = int( raw_input("#> ") );
		
		return vv[chosen];
	
	def handle( self, *args, **options ):
		self.origArgs = args;
		self.origOpts = options;
		
		run_callback( self._choose_version(), self.runOrig );
	
	def runOrig( self, proc ):
		super( MumbleCommandWrapper, self ).handle( *self.origArgs, **self.origOpts );


