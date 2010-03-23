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

from django.core.management.base	import BaseCommand
from django.contrib.auth.models 	import User
from django.contrib.sites.models	import Site
from django.conf			import settings

from mumble.models			import Mumble


class TestFailed( Exception ):
	pass;

class Command( BaseCommand ):
	help = "Run a few tests on Mumble-Django's setup."
	
	def handle(self, **options):
		try:
			import Ice
		except ImportError:
			pass
		else:
			self.check_slice();
		
		self.check_rootdir();
		self.check_dbase();
		self.check_sites();
		self.check_mumbles();
		self.check_admins();
		self.check_secret_key();
	
	def check_slice( self ):
		print "Checking slice file...",
		if settings.SLICE is None:
			raise TestFailed( "You don't have set the SLICE variable in settings.py." )
		
		if " " in settings.SLICE:
			raise TestFailed( "You have a space char in your Slice path. This will confuse Ice, please check." )
		
		if not settings.SLICE.endswith( ".ice" ):
			raise TestFailed( "The slice file name MUST end with '.ice'." )
		
		try:
			fd = open( settings.SLICE, "rb" )
			slice = fd.read()
			fd.close()
		except IOError, err:
			raise TestFailed( "Failed opening the slice file: %s" % err )
		
		import Ice
		Ice.loadSlice( settings.SLICE )
		
		print "[ OK ]"
	
	def check_rootdir( self ):
		print "Checking root directory access...",
		if not os.path.exists( settings.MUMBLE_DJANGO_ROOT ):
			raise TestFailed( "The mumble-django root directory does not exist." );
		
		elif settings.DATABASE_ENGINE != "sqlite3":
			print "not using sqlite [ OK ]"
		
		else:
			statinfo = os.stat( settings.MUMBLE_DJANGO_ROOT );
			
			if statinfo.st_uid == 0:
				raise TestFailed(
					"The mumble-django root directory belongs to user root. This is "
					"most certainly not what you want because it will prevent your "
					"web server from being able to write to the database. Please check." );
			
			elif not os.access( settings.MUMBLE_DJANGO_ROOT, os.W_OK ):
				raise TestFailed( "The mumble-django root directory is not writable." );
			
			else:
				print "[ OK ]";
	
	def check_dbase( self ):
		print "Checking database access...",
		if settings.DATABASE_ENGINE == "sqlite3":
			if not os.path.exists( settings.DATABASE_NAME ):
				raise TestFailed( "database does not exist. Have you run syncdb yet?" );
			
			else:
				statinfo = os.stat( settings.DATABASE_NAME );
				
				if statinfo.st_uid == 0:
					raise TestFailed(
						"the database file belongs to root. This is most certainly not what "
						"you want because it will prevent your web server from being able "
						"to write to it. Please check." );
				
				elif not os.access( settings.DATABASE_NAME, os.W_OK ):
					raise TestFailed( "database file is not writable." );
				
				else:
					print "[ OK ]";
		
		else:
			print "not using sqlite, so I can't check.";
	
	
	def check_sites( self ):
		print "Checking URL configuration...",
		
		try:
			site = Site.objects.get_current();
		
		except Site.DoesNotExist:
			try:
				sid = settings.SITE_ID
			except AttributeError:
				from django.core.exceptions import ImproperlyConfigured
				raise ImproperlyConfigured(
					"You're using the Django \"sites framework\" without having set the SITE_ID "
					"setting. Create a site in your database and rerun this command to fix this error.")
			else:
				print(  "none set.\n"
					"Please enter the domain where Mumble-Django is reachable." );
				dom = raw_input( "> " ).strip();
				site = Site( id=sid, name=dom, domain=dom );
				site.save();
		
		if site.domain == 'example.com':
			print(  "still the default.\n"
				"The domain is configured as example.com, which is the default but does not make sense. "
				"Please enter the domain where Mumble-Django is reachable." );
			
			site.domain = raw_input( "> " ).strip();
			site.save();
		
		print site.domain, "[ OK ]";
	
	
	def check_admins( self ):
		print "Checking if an Admin user exists...",
		
		for user in User.objects.all():
			if user.is_superuser:
				print "[ OK ]";
				return;
		
		raise TestFailed( ""
			"No admin user exists, so you won't be able to log in to the admin system. You "
			"should run `./manage.py createsuperuser` to create one." );
	
	
	def check_mumbles( self ):
		print "Checking Murmur instances...",
		
		mm = Mumble.objects.all();
		
		if mm.count() == 0:
			raise TestFailed(
				"no Mumble servers are configured, you might want to run "
				"`./manage.py syncdb` to run an auto detection." );
		
		else:
			for mumble in mm:
				try:
					mumble.ctl
				except Exception, err:
					raise TestFailed(
						"Connecting to Murmur `%s` (%s) failed: %s" % ( mumble.name, mumble.server, err )
						);
			print "[ OK ]";
	
	def check_secret_key( self ):
		print "Checking SECRET_KEY...",
		
		blacklist = ( 'u-mp185msk#z4%s(do2^5405)y5d!9adbn92)apu_p^qvqh10v', );
		
		if settings.SECRET_KEY in blacklist:
			raise TestFailed(
				"Your SECRET_KEY setting matches one of the keys that were put in the settings.py "
				"file shipped with Mumble-Django, which means your SECRET_KEY is all but secret. "
				"You should change the setting, or run gen_secret_key.sh to do it for you."
				);
		else:
			print "[ OK ]";






