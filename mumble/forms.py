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

import socket
import re

from django			import forms
from django.conf		import settings
from django.forms		import Form, ModelForm
from django.utils.translation	import ugettext_lazy as _

from mumble.models		import MumbleServer, Mumble, MumbleUser


class PropertyModelForm( ModelForm ):
	""" ModelForm that gets/sets fields that are not within the model's
	    fields as model attributes. Necessary to get forms that manipulate
	    properties.
	"""
	
	def __init__( self, *args, **kwargs ):
		ModelForm.__init__( self, *args, **kwargs );
		
		if self.instance:
			instfields = self.instance._meta.get_all_field_names()
			for fldname in self.fields:
				if fldname in instfields:
					continue
				self.fields[fldname].initial = getattr( self.instance, fldname )
				prop = getattr( self.instance.__class__, fldname )
				if prop.__doc__:
					self.fields[fldname].label = _(prop.__doc__)
	
	def save( self, commit=True ):
		inst = ModelForm.save( self, commit=commit )
		
		if commit:
			self.save_to_model( inst )
		else:
			# Update when the model has been saved.
			from django.db.models import signals
			self._update_inst = inst
			signals.post_save.connect( self.save_listener, sender=inst.__class__ )
		
		return inst
	
	def save_listener( self, **kwargs ):
		if kwargs['instance'] is self._update_inst:
			self.save_to_model( self._update_inst )
	
	def save_to_model( self, inst ):
		instfields = inst._meta.get_all_field_names()
		
		for fldname in self.fields:
			if fldname not in instfields:
				setattr( inst, fldname, self.cleaned_data[fldname] )


class MumbleForm( PropertyModelForm ):
	""" The Mumble Server admin form that allows to configure settings which do
	    not necessarily have to be reserved to the server hoster.
	
	    Server hosters are expected to use the Django admin application instead,
	    where everything can be configured freely.
	"""
	
	url     = forms.CharField( required=False )
	motd    = forms.CharField( required=False, widget=forms.Textarea )
	passwd  = forms.CharField( required=False, help_text=_(
		"Password required to join. Leave empty for public servers.") )
	supw    = forms.CharField( required=False )
	obfsc   = forms.BooleanField( required=False, help_text=_(
		"If on, IP adresses of the clients are not logged.") )
	player  = forms.CharField( required=False )
	channel = forms.CharField( required=False )
	defchan = forms.TypedChoiceField( choices=(), coerce=int, required=False )
	timeout = forms.IntegerField( required=False )
	certreq = forms.BooleanField( required=False )
	textlen = forms.IntegerField( required=False )
	html    = forms.BooleanField( required=False )
	
	def __init__( self, *args, **kwargs ):
		PropertyModelForm.__init__( self, *args, **kwargs )
		
		# Populate the `default channel' field's choices
		choices = [ ('', '----------') ]
		
		if self.instance and self.instance.srvid is not None:
			if self.instance.booted:
				def add_item( item, level ):
					if item.is_server or item.is_channel:
						choices.append( ( item.chanid, ( "-"*level + " " + item.name ) ) )
				
				self.instance.rootchan.visit(add_item)
			else:
				current = self.instance.defchan
				if current is not None:
					choices.append( ( current, "Current value: %d" % current ) )
		self.fields['defchan'].choices = choices
	
	class Meta:
		model   = Mumble;
		fields  = ['name'];


class MumbleAdminForm( MumbleForm ):
	""" A Mumble Server admin form intended to be used by the server hoster. """
	
	users    = forms.IntegerField( required=False )
	bwidth   = forms.IntegerField( required=False )
	sslcrt   = forms.CharField( required=False, widget=forms.Textarea )
	sslkey   = forms.CharField( required=False, widget=forms.Textarea )
	booted   = forms.BooleanField( required=False )
	autoboot = forms.BooleanField( required=False )
	bonjour  = forms.BooleanField( required=False )
	
	class Meta:
		fields  = None
		exclude = None
	
	def clean_port( self ):
		""" Check if the port number is valid. """
		
		port = self.cleaned_data['port'];
		
		if port is not None and port != '':
			if port < 1 or port >= 2**16:
				raise forms.ValidationError(
					_("Port number %(portno)d is not within the allowed range %(minrange)d - %(maxrange)d") % {
					'portno':   port,
					'minrange': 1,
					'maxrange': 2**16,
					});
			return port;
		return None


class MumbleServerForm( ModelForm ):
	defaultconf = forms.CharField( label=_("Default config"), required=False, widget=forms.Textarea )
	
	def __init__( self, *args, **kwargs ):
		ModelForm.__init__( self, *args, **kwargs )
		
		if self.instance and self.instance.id:
			if self.instance.online:
				confstr = ""
				conf = self.instance.defaultconf
				for field in conf:
					confstr += "%s: %s\n" % ( field, conf[field] )
				self.fields["defaultconf"].initial = confstr
			else:
				self.fields["defaultconf"].initial = _("This server is currently offline.")
	
	class Meta:
		model = MumbleServer


class MumbleUserForm( ModelForm ):
	""" The user registration form used to register an account. """
	
	password = forms.CharField( widget=forms.PasswordInput, required=False )
	
	def __init__( self, *args, **kwargs ):
		ModelForm.__init__( self, *args, **kwargs );
		self.server = None;
	
	def clean_name( self ):
		""" Check if the desired name is forbidden or taken. """
		
		name = self.cleaned_data['name'];
		
		if self.server is None:
			raise AttributeError( "You need to set the form's server attribute to the server instance "
				"for validation to work." );
		
		if self.server.player and re.compile( self.server.player ).match( name ) is None:
			raise forms.ValidationError( _( "That name is forbidden by the server." ) );
		
		if not self.instance.id and len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) > 0:
			raise forms.ValidationError( _( "Another player already registered that name." ) );
		
		return name;
	
	def clean_password( self ):
		""" Verify a password has been given. """
		passwd = self.cleaned_data['password'];
		if not passwd and ( not self.instance or self.instance.mumbleid == -1 ):
			raise forms.ValidationError( _( "Cannot register player without a password!" ) );
		return passwd;
	
	class Meta:
		model   = MumbleUser;
		fields  = ( 'name', 'password' );


class MumbleUserPasswordForm( MumbleUserForm ):
	""" The user registration form used to register an account on a private server in protected mode. """
	
	serverpw = forms.CharField(
		label=_('Server Password'),
		help_text=_('This server is private and protected mode is active. Please enter the server password.'),
		widget=forms.PasswordInput(render_value=False)
		);
	
	def clean_serverpw( self ):
		""" Validate the password """
		serverpw = self.cleaned_data['serverpw'];
		if self.server.passwd != serverpw:
			raise forms.ValidationError( _( "The password you entered is incorrect." ) );
		return serverpw;
	
	def clean( self ):
		""" prevent save() from trying to store the password in the Model instance. """
		# clean() will be called after clean_serverpw(), so it has already been validated here.
		if 'serverpw' in self.cleaned_data:
			del( self.cleaned_data['serverpw'] );
		return self.cleaned_data;


class MumbleUserLinkForm( MumbleUserForm ):
	""" Special registration form to either register or link an account. """
	
	linkacc = forms.BooleanField(
		label=_('Link account'),
		help_text=_('The account already exists and belongs to me, just link it instead of creating.'),
		required=False,
		);	
	
	def __init__( self, *args, **kwargs ):
		MumbleUserForm.__init__( self, *args, **kwargs );
		self.mumbleid = None;
	
	def clean_name( self ):
		""" Check if the target account exists in Murmur. """
		if 'linkacc' not in self.data:
			return MumbleUserForm.clean_name( self );
		
		# Check if user exists
		name = self.cleaned_data['name'];
		
		if len( self.server.ctl.getRegisteredPlayers( self.server.srvid, name ) ) != 1:
			raise forms.ValidationError( _( "No such user found." ) );
		
		return name;
	
	def clean_password( self ):
		""" Verify that the password is correct. """
		if 'linkacc' not in self.data:
			return MumbleUserForm.clean_password( self );
		
		if 'name' not in self.cleaned_data:
			# keep clean() from trying to find a user that CAN'T exist
			self.mumbleid = -10;
			return '';
		
		# Validate password with Murmur
		passwd = self.cleaned_data['password'];
		
		self.mumbleid = self.server.ctl.verifyPassword( self.server.srvid, self.cleaned_data['name'], passwd )
		if self.mumbleid <= 0:
			raise forms.ValidationError( _( "The password you entered is incorrect." ) );
		
		return passwd;
	
	def clean( self ):
		""" Create the MumbleUser instance to save in. """
		if 'linkacc' not in self.data or self.mumbleid <= 0:
			return self.cleaned_data;
		
		try:
			m_user = MumbleUser.objects.get( server=self.server, mumbleid=self.mumbleid );
		except MumbleUser.DoesNotExist:
			m_user = MumbleUser( server=self.server, name=self.cleaned_data['name'], mumbleid=self.mumbleid );
			m_user.save( dontConfigureMurmur=True );
		else:
			if m_user.owner is not None:
				raise forms.ValidationError( _( "That account belongs to someone else." ) );
		
		if m_user.getAdmin() and not settings.ALLOW_ACCOUNT_LINKING_ADMINS:
			raise forms.ValidationError( _( "Linking Admin accounts is not allowed." ) );
		self.instance = m_user;
		
		return self.cleaned_data;


class MumbleUserAdminForm( PropertyModelForm ):
	aclAdmin = forms.BooleanField( required=False );
	password = forms.CharField( widget=forms.PasswordInput, required=False )
	
	def clean_password( self ):
		""" Verify a password has been given. """
		passwd = self.cleaned_data['password'];
		if not passwd and ( not self.instance or self.instance.mumbleid == -1 ):
			raise forms.ValidationError( _( "Cannot register player without a password!" ) );
		return passwd;
	
	class Meta:
		model   = Mumble;


class MumbleKickForm( Form ):
	session = forms.IntegerField();
	ban	= forms.BooleanField( required=False );
	reason	= forms.CharField( required=False );


class MumbleTextureForm( Form ):
	""" The form used to upload a new image to be set as texture. """
	texturefile = forms.ImageField( label=_("User Texture") );


