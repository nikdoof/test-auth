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

import simplejson
from StringIO				import StringIO
from PIL				import Image

from django.shortcuts			import render_to_response, get_object_or_404, get_list_or_404
from django.template			import RequestContext
from django.http			import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators	import login_required
from django.contrib.auth.models 	import User
from django.conf			import settings
from django.core.urlresolvers		import reverse

from django.contrib.auth		import views as auth_views

from models				import Mumble, MumbleUser
from forms				import MumbleForm, MumbleUserForm, MumbleUserPasswordForm
from forms				import MumbleUserLinkForm, MumbleTextureForm, MumbleKickForm


def redir( request ):
	""" Redirect to the servers list. """
	if request.META['HTTP_USER_AGENT'].startswith( 'BlackBerry' ) or \
	   "Opera Mobi" in request.META['HTTP_USER_AGENT'] or \
	   "Opera Mini" in request.META['HTTP_USER_AGENT'] or \
	   "Windows CE" in request.META['HTTP_USER_AGENT'] or \
	   "MIDP" in request.META['HTTP_USER_AGENT'] or \
	   "Palm" in request.META['HTTP_USER_AGENT'] or \
	   "NetFront" in request.META['HTTP_USER_AGENT'] or \
	   "Nokia" in request.META['HTTP_USER_AGENT'] or \
	   "Symbian" in request.META['HTTP_USER_AGENT'] or \
	   "UP.Browser" in request.META['HTTP_USER_AGENT'] or \
	   "UP.Link" in request.META['HTTP_USER_AGENT'] or \
	   "WinWAP" in request.META['HTTP_USER_AGENT'] or \
	   "Android" in request.META['HTTP_USER_AGENT'] or \
	   "DoCoMo" in request.META['HTTP_USER_AGENT'] or \
	   "KDDI-" in request.META['HTTP_USER_AGENT'] or \
	   "Softbank" in request.META['HTTP_USER_AGENT'] or \
	   "J-Phone" in request.META['HTTP_USER_AGENT'] or \
	   "IEMobile" in request.META['HTTP_USER_AGENT'] or \
	   "iPod" in request.META['HTTP_USER_AGENT'] or \
	   "iPhone" in request.META['HTTP_USER_AGENT']:
		return HttpResponseRedirect( reverse( mobile_mumbles ) );
	else:
		return HttpResponseRedirect( reverse( mumbles ) );


def mobile_mumbles( request ):
	return mumbles( request, mobile=True );


def mumbles( request, mobile=False ):
	""" Display a list of all configured Mumble servers, or redirect if only one configured. """
	mms = Mumble.objects.all().order_by( "name" );
	
	if len(mms) == 1:
		return HttpResponseRedirect( reverse(
			{ False: show, True: mobile_show }[mobile],
			kwargs={ 'server': mms[0].id, }
			) );
	
	return render_to_response(
		'mumble/%s.html' % { False: 'list', True: 'mobile_list' }[mobile],
		{ 'MumbleObjects': mms,
		  'MumbleActive':  True,
		},
		context_instance = RequestContext(request)
		);


def show( request, server ):
	""" Display the channel list for the given Server ID.
	
	    This includes not only the channel list itself, but indeed the user registration,
	    server admin and user texture form as well. The template then uses JavaScript
	    to display these forms integrated into the Channel viewer.
	"""
	srv = get_object_or_404( Mumble, id=server );
	if not srv.booted:
		return render_to_response(
			'mumble/offline.html',
			{ 'DBaseObject':  srv,
			  'MumbleActive': True,
			}, context_instance = RequestContext(request) );
	
	isAdmin = srv.isUserAdmin( request.user );
	
	# The tab to start on.
	displayTab = 0;
	
	if isAdmin:
		if request.method == 'POST' and "mode" in request.POST and request.POST['mode'] == 'admin':
			adminform = MumbleForm( request.POST, instance=srv );
			if adminform.is_valid():
				adminform.save();
				return HttpResponseRedirect( reverse( show, kwargs={ 'server': int(server), } ) );
			else:
				displayTab = 2;
		else:
			adminform = MumbleForm( instance=srv );
	else:
		adminform = None;
	
	registered = False;
	user = None;
	
	if request.user.is_authenticated():
		# Unregistered users may or may not need a password to register.
		if settings.PROTECTED_MODE and srv.passwd:
			unregged_user_form = MumbleUserPasswordForm;
		# Unregistered users may or may not want to link an existing account
		elif settings.ALLOW_ACCOUNT_LINKING:
			unregged_user_form = MumbleUserLinkForm;
		else:
			unregged_user_form = MumbleUserForm;
		
		
		if request.method == 'POST' and 'mode' in request.POST and request.POST['mode'] == 'reg':
			try:
				user    = MumbleUser.objects.get( server=srv, owner=request.user );
			except MumbleUser.DoesNotExist:
				regform = unregged_user_form( request.POST );
				regform.server = srv;
				if regform.is_valid():
					model = regform.save( commit=False );
					model.owner  = request.user;
					model.server = srv;
					# If we're linking accounts, the change is local only.
					model.save( dontConfigureMurmur=( "linkacc" in regform.data ) );
					return HttpResponseRedirect( reverse( show, kwargs={ 'server': int(server), } ) );
				else:
					displayTab = 1;
			else:
				regform = MumbleUserForm( request.POST, instance=user );
				regform.server = srv;
				if regform.is_valid():
					regform.save();
					return HttpResponseRedirect( reverse( show, kwargs={ 'server': int(server), } ) );
				else:
					displayTab = 1;
		else:
			try:
				user  = MumbleUser.objects.get( server=srv, owner=request.user );
			except MumbleUser.DoesNotExist:
				regform = unregged_user_form();
			else:
				regform = MumbleUserForm( instance=user );
				registered = True;
		
		if request.method == 'POST' and 'mode' in request.POST and request.POST['mode'] == 'texture' and registered:
			textureform = MumbleTextureForm( request.POST, request.FILES );
			if textureform.is_valid():
				user.setTexture( Image.open( request.FILES['texturefile'] ) );
				return HttpResponseRedirect( reverse( show, kwargs={ 'server': int(server), } ) );
		else:
			textureform = MumbleTextureForm();
	
	else:
		regform = None;
		textureform = None;
	
	if isAdmin:
		if request.method == 'POST' and 'mode' in request.POST and request.POST['mode'] == 'kick':
			kickform = MumbleKickForm( request.POST );
			if kickform.is_valid():
				if kickform.cleaned_data["ban"]:
					srv.banUser( kickform.cleaned_data['session'], kickform.cleaned_data['reason'] );
				srv.kickUser( kickform.cleaned_data['session'], kickform.cleaned_data['reason'] );
	
	# ChannelTable is a somewhat misleading name, as it actually contains channels and players.
	channelTable = [];
	for cid in srv.channels:
		if cid != 0 and srv.channels[cid].show:
			channelTable.append( srv.channels[cid] );
	for pid in srv.players:
		channelTable.append( srv.players[pid] );
	
	show_url = reverse( show, kwargs={ 'server': srv.id } );
	login_url = reverse( auth_views.login );
	
	return render_to_response(
		'mumble/mumble.html',
		{
			'login_url':    "%s?next=%s" % ( login_url, show_url ),
			'DBaseObject':  srv,
			'ChannelTable': channelTable,
			'CurrentUserIsAdmin': isAdmin,
			'AdminForm':    adminform,
			'RegForm':      regform,
			'TextureForm':  textureform,
			'Registered':   registered,
			'DisplayTab':   displayTab,
			'MumbleActive': True,
			'MumbleAccount':user,
		},
		context_instance = RequestContext(request)
		);

def mobile_show( request, server ):
	""" Display the channel list for the given Server ID. """
	
	srv = get_object_or_404( Mumble, id=server );
	
	user = None;
	if request.user.is_authenticated():
		try:
			user = MumbleUser.objects.get( server=srv, owner=request.user );
		except MumbleUser.DoesNotExist:
			pass;
	
	return render_to_response(
		'mumble/mobile_mumble.html',
		{
			'DBaseObject':  srv,
			'MumbleActive': True,
			'MumbleAccount':user,
		},
		context_instance = RequestContext(request)
		);
	



def showTexture( request, server, userid ):
	""" Pack the given user's texture into an HttpResponse.
	
	    If userid is none, use the currently logged in User.
	"""
	
	srv  = get_object_or_404( Mumble,     id=int(server) );
	user = get_object_or_404( MumbleUser, server=srv, id=int(userid) );
	
	try:
		img  = user.getTexture();
	except ValueError:
		raise Http404();
	else:
		buf = StringIO();
		img.save( buf, "PNG" );
		return HttpResponse( buf.getvalue(), "image/png" );


@login_required
def users( request, server ):
	""" Create a list of MumbleUsers for a given server serialized as a JSON object.
	
	    If the request has a "data" field, evaluate that and update the user records.
	"""
	
	srv = get_object_or_404( Mumble, id=int(server) );
	
	if "resync" in request.POST and request.POST['resync'] == "true":
		srv.readUsersFromMurmur();
	
	if not srv.isUserAdmin( request.user ):
		return HttpResponse(
			simplejson.dumps({ 'success': False, 'objects': [], 'errormsg': 'Access denied' }),
			mimetype='text/javascript'
			);
	
	if request.method == 'POST':
		data = simplejson.loads( request.POST['data'] );
		for record in data:
			if record['id'] == -1:
				if record['delete']:
					continue;
				mu = MumbleUser( server=srv );
			else:
				mu = MumbleUser.objects.get( id=record['id'] );
				if record['delete']:
					mu.delete();
					continue;
			
			mu.name     = record['name'];
			mu.password = record['password'];
			if record['owner']:
				mu.owner = User.objects.get( id=int(record['owner']) );
			mu.save();
			mu.aclAdmin = record['admin'];
	
	users = [];
	for mu in srv.mumbleuser_set.all():
		owner = None;
		if mu.owner is not None:
			owner = mu.owner.id
		
		users.append( {
			'id':       mu.id,
			'name':     mu.name,
			'password': None,
			'owner':    owner,
			'admin':    mu.aclAdmin,
			} );
	
	return HttpResponse(
		simplejson.dumps( { 'success': True, 'objects': users } ),
		mimetype='text/javascript'
		);


@login_required
def djangousers( request ):
	""" Return a list of all Django users' names and IDs. """
	
	users = [ { 'uid': '', 'uname': '------' } ];
	for du in User.objects.all().order_by( 'username' ):
		users.append( {
			'uid':   du.id,
			'uname': unicode( du ),
			} );
	
	return HttpResponse(
		simplejson.dumps( { 'success': True, 'objects': users } ),
		mimetype='text/javascript'
		);


def mmng_tree( request, server ):
	""" Return a JSON representation of the channel tree suitable for
	    Murmur Manager:
	      http://github.com/cheald/murmur-manager/tree/master/widget/
	
	    To make the client widget query this view, set the URL attribute
	    to "http://<mumble-django base URL>/mumble"
	"""
	
	srv = get_object_or_404( Mumble, id=int(server) );
	
	chanlist = []
	userlist = []
	
	for chanid in srv.channels:
		channel = srv.channels[chanid]
		
		if channel.parent is not None:
			parent = channel.parent.chanid
		else:
			parent = -1
		
		chanlist.append({
			"type":     "channel",
			"id":       channel.chanid,
			"name":     channel.name,
			"parent":   parent,
			"position": channel.position,
			"state":    channel.temporary and "temporary" or "permanent"
			})
	
	for sessionid in srv.players:
		user = srv.players[sessionid]
		userlist.append({
			"type":    "player",
			"name":    user.name,
			"channel": user.channel.chanid,
			"mute":    user.mute or user.selfMute or user.suppress,
			"deaf":    user.deaf or user.selfDeaf,
			"online":  user.onlinesecs,
			"state":   "online"
			})
	
	if "callback" in request.GET:
		prefix = request.GET["callback"]
	else:
		prefix = ""
	
	return HttpResponse(
		prefix + "(" + simplejson.dumps( { 'channels': chanlist, 'users': userlist } ) + ")",
		mimetype='text/javascript'
		);


def mumbleviewer_tree_xml( request, server ):
	""" Get the XML tree from the server and serialize it to the client. """
	from xml.etree.cElementTree import tostring as xml_to_string
	srv = get_object_or_404( Mumble, id=int(server) );
	return HttpResponse(
		xml_to_string( srv.asMvXml(), encoding='utf-8' ),
		mimetype='text/xml'
		);

def mumbleviewer_tree_json( request, server ):
	""" Get the Dict from the server and serialize it as JSON to the client. """
	srv = get_object_or_404( Mumble, id=int(server) );
	
	if "jsonp_callback" in request.GET:
		prefix = request.GET["jsonp_callback"]
	else:
		prefix = ""
	
	return HttpResponse(
		prefix + "(" + simplejson.dumps( srv.asMvJson() ) + ")",
		mimetype='text/javascript'
		);
