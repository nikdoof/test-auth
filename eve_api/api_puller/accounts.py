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
from eve_api.models import EVEAccount, EVEPlayerCharacter, EVEPlayerCharacterRole, EVEPlayerCorporation

def import_eve_account(api_key, user_id, force_cache=False):
    """
    Imports an account from the API into the EVEAccount model.
    """
    auth_params = {'userID': user_id, 'apiKey': api_key}

    try:
        account_doc = CachedDocument.objects.api_query('/account/Characters.xml.aspx',
                                                   params=auth_params,
                                                   no_cache=force_cache)
    except APIAuthException:
        try:
            account = EVEAccount.objects.get(id=user_id)
        except EVEAccount.DoesNotExist:
            return
        if api_key == account.api_key:
            account.api_status = API_STATUS_AUTH_ERROR
            account.api_last_updated = datetime.utcnow()
            account.save()
            return
    except APINoUserIDException:
        try:
            account = EVEAccount.objects.get(id=user_id)
            account.delete()
        except EVEAccount.DoesNotExist:
            return

    dom = minidom.parseString(account_doc.body.encode('utf-8'))

    enode = dom.getElementsByTagName('error')
    if enode:
        try:
            account = EVEAccount.objects.get(id=user_id)
        except EVEAccount.DoesNotExist:
            return

        error = enode[0].getAttribute('code')

        if int(error) >= 900:
            # API disabled, down or rejecting, return without changes
            return

        if error == '211':
            account.api_status = API_STATUS_ACC_EXPIRED
        else:
            account.api_status = API_STATUS_OTHER_ERROR
        account.api_last_updated = datetime.utcnow()
        account.save()
        return

    characters_node_children = dom.getElementsByTagName('rowset')[0].childNodes

    # Create or retrieve the account last to make sure everything
    # before here is good to go.
    account, created = EVEAccount.objects.get_or_create(id=user_id)
    account.api_key = api_key
    account.api_user_id = user_id
    account.api_status = API_STATUS_OK
    account.save()

    for node in characters_node_children:
        try:
            char = import_eve_character(api_key, user_id, node.getAttribute('characterID'))
            if char:
                account.characters.add(char)
        except AttributeError:
            # This must be a Text node, ignore it.
            continue

    # Check API keytype if we have a character and a unknown key status
    if account.api_keytype == API_KEYTYPE_UNKNOWN and len(account.characters.all()):
        auth_params['characterID'] = account.characters.all()[0].id
        keycheck = CachedDocument.objects.api_query('/char/AccountBalance.xml.aspx', params=auth_params, no_cache=True)

        if keycheck:
            dom = minidom.parseString(keycheck.body.encode('utf-8'))
            enode = dom.getElementsByTagName('error')

            if enode and int(enode[0].getAttribute('code')) == 200:
                account.api_keytype = API_KEYTYPE_LIMITED
            elif not enode:
                account.api_keytype = API_KEYTYPE_FULL
            else:
                account.api_keytype = API_KEYTYPE_UNKNOWN
        else:
            account.api_keytype = API_KEYTYPE_UNKNOWN

    account.api_last_updated = datetime.utcnow()
    account.save()
    return account
    
def import_eve_character(api_key, user_id, character_id):

    auth_params = {'userID': user_id, 'apiKey': api_key, 'characterID': character_id }
    char_doc = CachedDocument.objects.api_query('/char/CharacterSheet.xml.aspx',
                                                   params=auth_params,
                                                   no_cache=False)

    dom = minidom.parseString(char_doc.body.encode('utf-8'))
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

    # Process the character's roles
    pchar.director = False
    pchar.roles.clear()
    roles = values.get('corporationRoles', None)
    if roles and len(roles):
        for r in roles:
            role, created = EVEPlayerCharacterRole.objects.get_or_create(id=r['roleID'], name=r['roleName'])
            pchar.roles.add(role)
            if r['roleName'] == 'roleDirector':
                pchar.director = True

    if values['gender'] == 'Male':
        pchar.gender = 1
    else:
        pchar.gender = 2

    for v in API_RACES_CHOICES:
        val, race = v
        if race == values['race']:
            pchar.race = val
            break

    total = 0
    for skill in values['skills']:
        total = total + int(skill['skillpoints'])
    pchar.total_sp = total

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
