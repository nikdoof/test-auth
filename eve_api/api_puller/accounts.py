#!/usr/bin/env python
"""
This module abstracts the pulling of account data from the EVE API.
"""
from xml.dom import minidom
from datetime import datetime

if __name__ == "__main__":
    # Only mess with the environmental stuff if this is being ran directly.
    from importer_path import fix_environment
    fix_environment() 

from datetime import datetime

from django.conf import settings
from eve_proxy.models import CachedDocument
from eve_api.app_defines import *
from eve_api.api_exceptions import APIAuthException, APINoUserIDException
from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCorporation

def import_eve_account(api_key, user_id):
    """
    Imports an account from the API into the EVEAccount model.
    """
    auth_params = {'userID': user_id, 'apiKey': api_key}
    account_doc = CachedDocument.objects.api_query('/account/Characters.xml.aspx',
                                                   params=auth_params,
                                                   no_cache=False)

    dom = minidom.parseString(account_doc.body.encode('utf-8'))

    if dom.getElementsByTagName('error'):
        try:
            account = EVEAccount.objects.get(id=user_id)
        except EVEAccount.DoesNotExist:
            return

        account.api_status = API_STATUS_OTHER_ERROR
        account.api_last_updated = datetime.utcnow()
        account.save()
        return

    characters_node_children = dom.getElementsByTagName('rowset')[0].childNodes

    # Create or retrieve the account last to make sure everything
    # before here is good to go.
    try:
        account = EVEAccount.objects.get(id=user_id)
    except EVEAccount.DoesNotExist:
        account = EVEAccount(id=user_id)

    account.api_key = api_key
    account.api_user_id = user_id
    account.api_status = API_STATUS_OK
    account.api_last_updated = datetime.utcnow()
    account.save()

    for node in characters_node_children:
        try:
            char = import_eve_character(api_key, user_id, node.getAttribute('characterID'))
            if char:
                account.characters.add(char)
        except AttributeError:
            # This must be a Text node, ignore it.
            continue
    return account
    
def import_eve_character(api_key, user_id, character_id):

    auth_params = {'userID': user_id, 'apiKey': api_key, 'characterID': character_id }
    char_doc = CachedDocument.objects.api_query('/char/CharacterSheet.xml.aspx',
                                                   params=auth_params,
                                                   no_cache=False)

    dom = minidom.parseString(char_doc.body)
    if dom.getElementsByTagName('error'):
        return

    nodes = dom.getElementsByTagName('result')[0].childNodes
    pchar, created = EVEPlayerCharacter.objects.get_or_create(id=character_id)

    values = {}
    for node in nodes:
        if node.nodeType == 1:
            node.normalize()
            if len(node.childNodes) == 1:
                values[node.tagName] = node.childNodes[0].nodeValue
            else:
                if node.tagName == "rowset":
                    continue
                nv = {}
                for nd in node.childNodes:
                    if nd.nodeType == 1:
                        nv[nd.tagName] = nd.childNodes[0].nodeValue
                values[node.tagName] = nv

    # Get this first, as it's safe.
    corporation_id = values['corporationID']
    corp, created = EVEPlayerCorporation.objects.get_or_create(id=corporation_id)
    if not corp.name:
        try:
            corp.query_and_update_corp()
        except:
            pass

    name = values['name']
    # Save these for last to keep the save count low.
    pchar.name = name
    pchar.corporation = corp

    pchar.balance = values['balance']
    pchar.attrib_intelligence = values['attributes']['intelligence']
    pchar.attrib_charisma = values['attributes']['charisma']
    pchar.attrib_perception = values['attributes']['perception']
    pchar.attrib_willpower = values['attributes']['willpower']
    pchar.attrib_memory = values['attributes']['memory']

    if values['gender'] == 'Male':
        pchar.gender = 1
    else:
        pchar.gender = 2

    pchar.race = API_RACES[values['race']]

    pchar.api_last_updated = datetime.utcnow()
    pchar.save()

    return pchar

if __name__ == "__main__":
    """
    Test import.
    """
    api_key = settings.EVE_API_USER_KEY 
    #api_key += "1"
    user_id = settings.EVE_API_USER_ID
    import_eve_account(api_key, user_id)
