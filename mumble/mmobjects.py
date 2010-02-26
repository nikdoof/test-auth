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

import datetime
from time			import time
from os.path			import join

from django.utils.http		import urlquote
from django.conf		import settings

def cmp_names( left, rite ):
	""" Compare two objects by their name property. """
	return cmp( left.name, rite.name );


class mmChannel( object ):
	""" Represents a channel in Murmur. """
	
	def __init__( self, server, channel_obj, parent_chan = None ):
		self.server   = server;
		self.players  = list();
		self.subchans = list();
		self.linked   = list();
		
		self.channel_obj = channel_obj;
		self.chanid      = channel_obj.id;
		
		self.parent = parent_chan;
		if self.parent is not None:
			self.parent.subchans.append( self );
		
		self._acl = None;
	
	# Lookup unknown attributes in self.channel_obj to automatically include Murmur's fields
	def __getattr__( self, key ):
		if hasattr( self.channel_obj, key ):
			return getattr( self.channel_obj, key );
		else:
			raise AttributeError( "'%s' object has no attribute '%s'" % ( self.__class__.__name__, key ) );
	
	def parent_channels( self ):
		""" Return the names of this channel's parents in the channel tree. """
		if self.parent is None or self.parent.is_server or self.parent.chanid == 0:
			return [];
		return self.parent.parent_channels() + [self.parent.name];
	
	
	def getACL( self ):
		""" Retrieve the ACL for this channel. """
		if not self._acl:
			self._acl = mmACL( self, self.server.ctl.getACL( self.server.srvid, self.chanid ) );
		
		return self._acl;
	
	acl = property( getACL, doc=getACL.__doc__ );
	
	
	is_server  = False;
	is_channel = True;
	is_player  = False;
	
	
	playerCount = property(
		lambda self: len( self.players ) + sum( [ chan.playerCount for chan in self.subchans ] ),
		doc="The number of players in this channel."
		);
	
	id   = property(
		lambda self: "channel_%d"%self.chanid,
		doc="A string ready to be used in an id property of an HTML tag."
		);
	
	top_or_not_empty = property(
		lambda self: self.parent is None or self.parent.chanid == 0 or self.playerCount > 0,
		doc="True if this channel needs to be shown because it is root, a child of root, or has players."
		);
	
	show =  property( lambda self: settings.SHOW_EMPTY_SUBCHANS or self.top_or_not_empty );
	
	def __str__( self ):
		return '<Channel "%s" (%d)>' % ( self.name, self.chanid );
	
	def sort( self ):
		""" Sort my subchannels and players, and then iterate over them and sort them recursively. """
		self.subchans.sort( cmp_names );
		self.players.sort( cmp_names );
		for subc in self.subchans:
			subc.sort();
	
	def visit( self, callback, lvl = 0 ):
		""" Call callback on myself, then visit my subchans, then my players. """
		callback( self, lvl );
		for subc in self.subchans:
			subc.visit( callback, lvl + 1 );
		for plr in self.players:
			plr.visit( callback, lvl + 1 );
	
	
	def getURL( self, for_user = None ):
		""" Create an URL to connect to this channel. The URL is of the form
		    mumble://username@host:port/parentchans/self.name
		"""
		userstr = "";
		
		if for_user is not None:
			userstr = "%s@" % for_user.name;
		
		versionstr = "version=%d.%d.%d" % tuple(self.server.version[0:3]);
		
		# create list of all my parents and myself
		chanlist = self.parent_channels() + [self.name];
		# urlencode channel names
		chanlist = [ urlquote( chan ) for chan in chanlist ];
		# create a path by joining the channel names
		chanpath = join( *chanlist );
		
		if self.server.port != settings.MUMBLE_DEFAULT_PORT:
			return "mumble://%s%s:%d/%s?%s" % ( userstr, self.server.addr, self.server.port, chanpath, versionstr );
		
		return "mumble://%s%s/%s?%s" % ( userstr, self.server.addr, chanpath, versionstr );
	
	connecturl = property( getURL, doc="A convenience wrapper for getURL." );
	
	def setDefault( self ):
		""" Make this the server's default channel. """
		self.server.defchan = self.chanid;
		self.server.save();
	
	is_default = property(
		lambda self: self.server.defchan == self.chanid,
		doc="True if this channel is the server's default channel."
		);
	
	def asDict( self ):
		chandata = self.channel_obj.__dict__.copy();
		chandata['players']  = [ pl.asDict() for pl in self.players  ];
		chandata['subchans'] = [ sc.asDict() for sc in self.subchans ];
		return chandata;




class mmPlayer( object ):
	""" Represents a Player in Murmur. """
	
	def __init__( self, server, player_obj, player_chan ):
		self.player_obj    = player_obj;
		
		self.onlinesince  = datetime.datetime.fromtimestamp( float( time() - player_obj.onlinesecs ) );
		self.channel      = player_chan;
		self.channel.players.append( self );
		
		if self.isAuthed:
			from mumble.models import MumbleUser
			try:
				self.mumbleuser = MumbleUser.objects.get( mumbleid=self.userid, server=server );
			except MumbleUser.DoesNotExist:
				self.mumbleuser = None;
		else:
			self.mumbleuser = None;
	
	# Lookup unknown attributes in self.player_obj to automatically include Murmur's fields
	def __getattr__( self, key ):
		if hasattr( self.player_obj, key ):
			return getattr( self.player_obj, key );
		else:
			raise AttributeError( "'%s' object has no attribute '%s'" % ( self.__class__.__name__, key ) );
	
	def __str__( self ):
		return '<Player "%s" (%d, %d)>' % ( self.name, self.session, self.userid );
	
	hasComment = property(
		lambda self: hasattr( self.player_obj, "comment" ) and bool(self.player_obj.comment),
		doc="True if this player has a comment set."
		);
	
	isAuthed = property(
		lambda self: self.userid != -1,
		doc="True if this player is authenticated (+A)."
		);
	
	isAdmin = property(
		lambda self: self.mumbleuser and self.mumbleuser.getAdmin(),
		doc="True if this player is in the Admin group in the ACL."
		);
	
	is_server  = False;
	is_channel = False;
	is_player  = True;
	
	# kept for compatibility to mmChannel (useful for traversal funcs)
	playerCount = property( lambda self: -1, doc="Exists only for compatibility to mmChannel." );
	
	id = property(
		lambda self: "player_%d"%self.session,
		doc="A string ready to be used in an id property of an HTML tag."
		);
	
	def visit( self, callback, lvl = 0 ):
		""" Call callback on myself. """
		callback( self, lvl );
	
	def asDict( self ):
		pldata = self.player_obj.__dict__.copy();
		
		if self.mumbleuser:
			if self.mumbleuser.hasTexture():
				pldata['texture'] = self.mumbleuser.textureUrl;
		
		return pldata;



class mmACL( object ):
	""" Represents an ACL for a certain channel. """
	
	def __init__( self, channel, acl_obj ):
		self.channel = channel;
		self.acls, self.groups, self.inherit = acl_obj;
		
		self.groups_dict = {};
		
		for group in self.groups:
			self.groups_dict[ group.name ] = group;
	
	def group_has_member( self, name, userid ):
		""" Checks if the given userid is a member of the given group in this channel. """
		if name not in self.groups_dict:
			raise ReferenceError( "No such group '%s'" % name );
		
		return userid in self.groups_dict[name].add or userid in self.groups_dict[name].members;
	
	def group_add_member( self, name, userid ):
		""" Make sure this userid is a member of the group in this channel (and subs). """
		if name not in self.groups_dict:
			raise ReferenceError( "No such group '%s'" % name );
		
		group = self.groups_dict[name];
		
		# if neither inherited nor to be added, add
		if userid not in group.members and userid not in group.add:
			group.add.append( userid );
		
		# if to be removed, unremove
		if userid in group.remove:
			group.remove.remove( userid );
	
	def group_remove_member( self, name, userid ):
		""" Make sure this userid is NOT a member of the group in this channel (and subs). """
		if name not in self.groups_dict:
			raise ReferenceError( "No such group '%s'" % name );
		
		group = self.groups_dict[name];
		
		# if added here, unadd
		if userid in group.add:
			group.add.remove( userid );
		# if member and not in remove, add to remove
		elif userid in group.members and userid not in group.remove:
			group.remove.append( userid );
	
	def save( self ):
		""" Send this ACL to Murmur. """
		return self.channel.server.ctl.setACL(
			self.channel.server.srvid,
			self.channel.chanid,
			self.acls, self.groups, self.inherit
			);



