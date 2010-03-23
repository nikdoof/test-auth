# -*- coding: utf-8 -*-

"""
 *  Copyright © 2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
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
from os.path		import join

from django.db		import connection, transaction
from django.db.models	import signals
from django.conf	import settings

from mumble		import models
from mumble.management.server_detect import find_existing_instances


def update_schema( **kwargs ):
	if "verbosity" in kwargs:
		v = kwargs['verbosity'];
	else:
		v = 1;
	
	if v:
		print "Migrating Database schema for Mumble-Django 2.0 now."
	
	scriptdir = join( settings.CONVERSIONSQL_ROOT, {
			'postgresql_psycopg2': 'pgsql',
			'postgresql': 'pgsql',
			'mysql':      'mysql',
			'sqlite3':    'sqlite',
			}[settings.DATABASE_ENGINE] )
	
	if v > 1:
		print "Reading migration scripts for %s from '%s'" % ( settings.DATABASE_ENGINE, scriptdir )
	
	scripts = [ filename for filename in os.listdir( scriptdir ) if filename.endswith( ".sql" ) ]
	scripts.sort()
	
	for filename in scripts:
		cursor = connection.cursor()
		
		scriptpath = os.path.join( scriptdir, filename )
		scriptfile = open( scriptpath, "r" )
		try:
			if v > 1:
				print "Running migration script '%s'..." % scriptpath
			stmt = scriptfile.read()
			cursor.execute( stmt )
		
		except IOError, err:
			print "Error reading file '%s':" % filename
			print err
		
		except cursor.db.connection.Error, err:
			print "Error executing file '%s':" % filename
			print err
		
		finally:
			scriptfile.close()
			cursor.close()
	
	if v:
		print "Database migration finished successfully."
	
	find_existing_instances( **kwargs )
