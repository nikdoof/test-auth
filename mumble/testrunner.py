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

import os

from django.test.simple 	import run_tests as django_run_tests
from django.conf		import settings

from murmurenvutils		import get_available_versions, run_callback, wait_for_user


def run_tests( test_labels, verbosity=1, interactive=True, extra_tests=[] ):
	""" Run the Django built in testing framework, but before testing the mumble
	    app, allow Murmur to be set up correctly.
	"""
	
	if not test_labels:
		test_labels = [ appname.split('.')[-1] for appname in settings.INSTALLED_APPS ];
	
	# No need to sync any murmur servers for the other apps
	os.environ['MURMUR_CONNSTR'] = '';
	
	# The easy way: mumble is not being tested.
	if "mumble" not in test_labels:
		return django_run_tests( test_labels, verbosity, interactive, extra_tests );
	
	# First run everything apart from mumble. mumble will be tested separately, so Murmur
	# can be set up properly first.
	failed_tests = 0;
	
	if len(test_labels) > 1:
		# only run others if mumble is not the only app to be tested
		test_labels = list(test_labels);
		test_labels.remove( "mumble" );
		failed_tests += django_run_tests( test_labels, verbosity, interactive, extra_tests );
	
	failed_tests += run_mumble_tests( verbosity, interactive );
	
	return failed_tests;


def run_mumble_tests( verbosity=1, interactive=True ):
	
	connstrings = {
		'DBus': 'net.sourceforge.mumble.murmur',
		'Ice':  'Meta:tcp -h 127.0.0.1 -p 6502',
		};
	
	def django_run_tests_wrapper( process, version ):
		wr_failed_tests = 0;
		
		for method in connstrings:
			# Check if this server is ready to be used with the current method
			if getattr( process.capabilities, ("has_%s" % method.lower()), False ):
				print "Testing mumble %s via %s" % ( version, method );
				
				os.environ['MURMUR_CONNSTR'] = connstrings[method];
				settings.DEFAULT_CONN        = connstrings[method];
				settings.SLICE_VERSION       = [ int(dgt) for dgt in version.split('.') ];
				
				print "MURMUR_CONNSTR:", os.environ['MURMUR_CONNSTR'];
				print "DEFAULT_CONN:  ", settings.DEFAULT_CONN;
				print "SLICE_VERSION: ", settings.SLICE_VERSION;
				
				if not process.capabilities.has_users:
					print "Waiting for user to connect (60 seconds)."
					wait_for_user( process, timeout=60 );
				
				wr_failed_tests += django_run_tests( ('mumble',), verbosity, interactive, [] );
			else:
				print "Mumble %s does not support Method %s" % ( version, method );
		
		return wr_failed_tests;
	
	failed_tests = 0;
	
	from mctl import MumbleCtlBase
	
	for version in get_available_versions():
		MumbleCtlBase.clearCache();
		
		run = raw_input( "Run tests for %s? [Y/n] " % version );
		if run in ('Y', 'y', ''):
			failed_tests += run_callback( version, django_run_tests_wrapper, version );
	
	return failed_tests;
