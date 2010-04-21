"""
This module abstracts the pulling of account data from the EVE API.
"""
from xml.dom import minidom
from datetime import datetime

from datetime import datetime
from django.conf import settings
from eve_proxy.models import CachedDocument
from eve_api.app_defines import *
from eve_api.api_exceptions import APIAuthException, APINoUserIDException
from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation


def pull_corp_members(api_key, user_id, character_id):
    """
    This function pulls all corporation members from the EVE API using a director's 
    API key. It'll add as much information as it can about the character.
    """

    # grab and decode /corp/MemberTracking.xml.aspx 
    auth_params = {'userID': user_id, 'apiKey': api_key, 'characterID': character_id }
    char_doc = CachedDocument.objects.api_query('/corp/MemberTracking.xml.aspx',
                                                   params=auth_params,
                                                   no_cache=False)

    dom = minidom.parseString(char_doc.body)
    if dom.getElementsByTagName('error'):
        return
    nodes = dom.getElementsByTagName('result')[0].childNodes

    values = {}
    for node in nodes:
        if node.nodeType == 1:
            node.normalize()
            if len(node.childNodes) == 1:
                values[node.tagName] = node.childNodes[0].nodeValue
            else:
                nv = {}
                if node.tagName == "rowset":
                    rset = []
                    for nd in node.childNodes:
                        if nd.nodeType == 1:
                            d = {}
                            for e in nd.attributes.keys():
                                d[e] = nd.attributes[e].value
                            rset.append(d)
                    values[node.attributes['name'].value] = rset
                else:
                    for nd in node.childNodes:
                        if nd.nodeType == 1:
                            nv[nd.tagName] = nd.childNodes[0].nodeValue
                    values[node.tagName] = nv


    # corpID from director
    corp = EVEPlayerCharacter.objects.get(id=character_id).corporation
    set = values['members']

    for character in set:

        pchar, created = EVEPlayerCharacter.objects.get_or_create(id=character['characterID'])

        if created:
            pchar.name = character['name']
            pchar.corporation = corp
        pchar.last_login = character['logonDateTime']
        pchar.last_logoff = character['logoffDateTime']
        pchar.current_location_id = int(character['locationID'])

        pchar.save()

    
