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

    dom = minidom.parseString(account_doc.body)

    if dom.getElementsByTagName('error'):
        try:
            account = EVEAccount.objects.get(id=user_id)
        except EVEAccount.DoesNotExist:
            return

        account.api_status = API_STATUS_OTHER_ERROR
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
    account.api_last_updated = datetime.utcnow()
    account.api_status = API_STATUS_OK
    account.save()

    for node in characters_node_children:
        try:
            # Get this first, as it's safe.
            corporation_id = node.getAttribute('corporationID')
            corp, created = EVEPlayerCorporation.objects.get_or_create(id=corporation_id)
            if not corp.name:
                try:
                    corp.query_and_update_corp()
                except:
                    pass
            # Do this last, since the things we retrieved above are used
            # on the EVEPlayerCharacter object's fields.
            character_id = node.getAttribute('characterID')
            pchar, created = EVEPlayerCharacter.objects.get_or_create(id=character_id)
            name = node.getAttribute('name')
            # Save these for last to keep the save count low.
            pchar.name = name
            pchar.corporation = corp
            pchar.api_last_updated = datetime.utcnow()
            pchar.save()
            account.characters.add(pchar)
        except AttributeError:
            # This must be a Text node, ignore it.
            continue

    return account
    
if __name__ == "__main__":
    """
    Test import.
    """
    api_key = settings.EVE_API_USER_KEY 
    #api_key += "1"
    user_id = settings.EVE_API_USER_ID
    import_eve_account(api_key, user_id)
