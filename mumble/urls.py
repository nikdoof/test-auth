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

from django.conf.urls.defaults import patterns

urlpatterns = patterns(
	'mumble.views',
	( r'djangousers',					'djangousers'		),
	( r'(?P<server>\d+)/users',				'users' 		),
	
	( r'(?P<server>\d+)/(?P<userid>\d+)/texture.png',	'showTexture'		),
	
	( r'murmur/tree/(?P<server>\d+)',			'mmng_tree'		),
	( r'mumbleviewer/(?P<server>\d+).xml',			'mumbleviewer_tree_xml' ),
	( r'mumbleviewer/(?P<server>\d+).json', 		'mumbleviewer_tree_json'),
	
	( r'mobile/(?P<server>\d+)',				'mobile_show'		),
	( r'mobile/?$',						'mobile_mumbles'	),
	
	( r'(?P<server>\d+)',					'show'			),
	( r'$',							'mumbles'		),
)
