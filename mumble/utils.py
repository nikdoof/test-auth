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

class ObjectInfo( object ):
	""" Wraps arbitrary information to be easily accessed. """
	
	def __init__( self, **kwargs ):
		self.__dict__ = kwargs;
	
	def __str__( self ):
		return unicode( self );
	
	def __repr__( self ):
		return unicode( self );
	
	def __unicode__( self ):
		return unicode( self.__dict__ );
