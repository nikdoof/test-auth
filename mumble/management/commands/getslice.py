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

import Ice, IcePy, os, getpass
from sys import stderr

from django.core.management.base	import BaseCommand

from mumble.models			import MumbleServer

class Command( BaseCommand ):
	help =  "Check if the known servers support getSlice."
	
	def handle(self, **options):
		prop = Ice.createProperties([])
		prop.setProperty("Ice.ImplicitContext", "Shared")
		
		idd = Ice.InitializationData()
		idd.properties = prop
		
		ice = Ice.initialize(idd)
		
		for serv in MumbleServer.objects.all():
			print "Probing server at '%s'..." % serv.dbus
			
			if serv.secret:
				ice.getImplicitContext().put( "secret", serv.secret.encode("utf-8") )
			
			prx = ice.stringToProxy( serv.dbus.encode("utf-8") )
			
			# Try loading the Slice from Murmur directly via its getSlice method.
			try:
				slice = IcePy.Operation( 'getSlice',
					Ice.OperationMode.Idempotent, Ice.OperationMode.Idempotent,
					True, (), (), (), IcePy._t_string, ()
					).invoke(prx, ((), None))
			except TypeError, err:
				print "  Received TypeError:", err
				print "  It seems your version of IcePy is incompatible."
			except Ice.OperationNotExistException:
				print "  Your version of Murmur does not support getSlice."
			else:
				print "  Successfully received the slice (length: %d bytes.)" % len(slice)
