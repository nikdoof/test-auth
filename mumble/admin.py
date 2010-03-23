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

from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from mumble.forms  import MumbleServerForm, MumbleAdminForm, MumbleUserAdminForm
from mumble.models import MumbleServer, Mumble, MumbleUser

class MumbleServerAdmin(admin.ModelAdmin):
	list_display   = [ 'dbus', 'get_murmur_online' ]
	search_fields  = [ 'dbus' ]
	ordering       = [ 'dbus' ]
	
	form = MumbleServerForm
	
	def get_murmur_online( self, obj ):
		return obj.online
	
	get_murmur_online.short_description = _('Master is running')
	get_murmur_online.boolean = True


class MumbleAdmin(admin.ModelAdmin):
	""" Specification for the "Server administration" admin section. """
	
	list_display   = [ 'name', 'srvid', 'get_addr', 'get_port', 'get_murmur_online', 'get_booted',
			   'get_is_public', 'get_users_regged', 'get_users_online', 'get_channel_count' ];
	list_filter    = [ 'addr', 'server' ];
	search_fields  = [ 'name', 'addr', 'port' ];
	ordering       = [ 'name' ];
	form           = MumbleAdminForm;
	
	def get_murmur_online( self, obj ):
		return obj.server.online
	
	get_murmur_online.short_description = _('Master is running')
	get_murmur_online.boolean = True
	
	def get_addr( self, obj ):
		if not obj.addr:
			return "*"
		return obj.addr
	
	get_addr.short_description = _('Server Address')
	
	def get_port( self, obj ):
		if not obj.port:
			return "< %d >" % (settings.MUMBLE_DEFAULT_PORT + obj.srvid - 1)
		return obj.port
	
	get_port.short_description = _('Server Port')
	
	def get_booted( self, obj ):
		return obj.booted
	
	get_booted.short_description = _('Instance is running')
	get_booted.boolean = True
	
	def get_users_regged( self, obj ):
		""" Populates the "Registered users" column. """
		if obj.booted:
			return obj.users_regged;
		else:
			return '-';
	
	get_users_regged.short_description = _( 'Registered users' );
	
	
	def get_users_online( self, obj ):
		""" Populates the "Online users" column. """
		if obj.booted:
			return obj.users_online;
		else:
			return '-';
	
	get_users_online.short_description = _( 'Online users' );
	
	
	def get_channel_count( self, obj ):
		""" Populates the "Channel Count" column. """
		if obj.booted:
			return obj.channel_cnt;
		else:
			return '-';
	
	get_channel_count.short_description = _( 'Channel count' );
	
	
	def get_is_public( self, obj ):
		""" Populates the "Public" column. """
		if obj.booted:
			if obj.is_public:
				return _( 'Yes' );
			else:
				return _( 'No' );
		else:
			return '-';
	
	get_is_public.short_description = _( 'Public' );


class MumbleUserAdmin(admin.ModelAdmin):
	""" Specification for the "Registered users" admin section. """
	
	list_display   = [ 'owner', 'server', 'name', 'get_acl_admin' ];
	list_filter    = [ 'server' ];
	search_fields  = [ 'owner__username', 'name' ];
	ordering       = [ 'owner__username' ];
	
	form = MumbleUserAdminForm
	
	def get_acl_admin( self, obj ):
		if obj.server.booted:
			return obj.aclAdmin
		return None
	
	get_acl_admin.short_description = _('Admin on root channel')
	get_acl_admin.boolean = True


admin.site.register( MumbleServer, MumbleServerAdmin );
admin.site.register( Mumble,       MumbleAdmin );
admin.site.register( MumbleUser,   MumbleUserAdmin );
