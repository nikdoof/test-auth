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

from django                 import template
from django.template.loader import render_to_string

from django.conf            import settings

register = template.Library();


@register.filter
def trunc( string, maxlen = 50 ):
	""" converts "a very very extaordinary long text" to "a very very extra... """
	if len(string) < maxlen:
		return string;
	return string[:(maxlen - 3)] + "…";


@register.filter
def chanview( obj, user = None ):
	""" renders an mmChannel / mmPlayer object with the correct template """
	if obj.is_server:
		return render_to_string( 'mumble/server.html',  { 'Server':  obj, 'MumbleAccount': user, 'MEDIA_URL': settings.MEDIA_URL } );
	elif obj.is_channel:
		return render_to_string( 'mumble/channel.html', { 'Channel': obj, 'MumbleAccount': user, 'MEDIA_URL': settings.MEDIA_URL } );
	elif obj.is_player:
		return render_to_string( 'mumble/player.html',  { 'Player':  obj, 'MumbleAccount': user, 'MEDIA_URL': settings.MEDIA_URL } );


@register.filter
def chanurl( obj, user ):
	""" create a connection URL and takes the user's login into account """
	return obj.getURL( user );

@register.filter
def mmversion_lt( obj, version ):
	""" return True if the given Server's version is less than the given version. """
	return tuple(obj.version[:3]) < tuple([int(v) for v in version.split('.')])

@register.filter
def mmversion_eq( obj, version ):
	""" return True if the given Server's version equals the given version. """
	return tuple(obj.version[:3]) == tuple([int(v) for v in version.split('.')])

@register.filter
def mmversion_gt( obj, version ):
	""" return True if the given Server's version is greater than the given version. """
	return tuple(obj.version[:3]) > tuple([int(v) for v in version.split('.')])
