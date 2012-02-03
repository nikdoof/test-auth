import sys
import logging
from datetime import datetime, timedelta
from xml.dom import minidom

from celery.decorators import task
from gargoyle import gargoyle

from eve_proxy.models import CachedDocument
from eve_proxy.exceptions import DocumentRetrievalError
from eve_api.models import EVEPlayerCorporation, EVEPlayerCharacter, EVEPlayerAlliance, EVEAccount
from eve_api.app_defines import *
from eve_api.utils import basic_xml_parse_doc
from eve_api.tasks.character import import_eve_character
from eve_api.api_exceptions import APIAccessException
        
@task(ignore_result=True)
def import_corp_details(corp_id, callback=None):

    log = import_corp_details.get_logger()

    try:
        corp = import_corp_details_func(corp_id, log)
    except APIAccessException, exc:
        log.error('API Exception while retreiving the corp document', exc_info=sys.exc_info(), extra={'data': {'corp_id': corp_id}})
        return
    except:
        log.error('Unknown exception while retreiving the corp document', exc_info=sys.exc_info(), extra={'data': {'corp_id': corp_id}})
        return
    else:
        if callback:
            subtask(callback).delay(corporation=corp.id)


@task()
def import_corp_details_result(corp_id, callback=None):

    log = import_corp_details_result.get_logger()

    try:
        corp = import_corp_details_func(corp_id, log)
    except APIAccessException, exc:
        log.error('API Exception while retreiving the corp document', exc_info=sys.exc_info(), extra={'data': {'corp_id': corp_id}})
        return None
    except:
        log.error('Unknown exception while retreiving the corp document', exc_info=sys.exc_info(), extra={'data': {'corp_id': corp_id}})
        return None
    else:
        if callback:
            subtask(callback).delay(corporation=corp.id)
        else:
            return corp


def import_corp_details_func(corp_id, log=logging.getLogger(__name__)):

    corpobj, created = EVEPlayerCorporation.objects.get_or_create(id=corp_id)   
    if created or not corpobj.api_last_updated or corpobj.api_last_updated < (datetime.utcnow() - timedelta(hours=12)):

        try:
            doc = CachedDocument.objects.api_query('/corp/CorporationSheet.xml.aspx', {'corporationID': corp_id})
        except DocumentRetrievalError, exc:
            log.error('Error retrieving CorporationSheet.xml.aspx for ID %s - %s' % (corp_id, exc))
            raise APIAccessException

        d = basic_xml_parse_doc(doc)['eveapi']

        if 'error' in d:
            log.error("Error importing Corp %s: %s" % (corp_id, d['error']))
            raise APIAccessException
        else:
            d = d['result']

        tag_mappings = (
            ('corporationName', 'name'),
            ('ticker', 'ticker'),
            ('url', 'url'),
            ('description', 'description'),
            ('memberCount', 'member_count'),
        )

        for tag_map in tag_mappings:
            setattr(corpobj, tag_map[1], d[tag_map[0]])

        logo_mappings = (
            ('graphicID', 'logo_graphic_id'),
            ('shape1', 'logo_shape1'),
            ('shape2', 'logo_shape2'),
            ('shape3', 'logo_shape3'),
            ('color1', 'logo_color1'),
            ('color2', 'logo_color2'),
            ('color3', 'logo_color3'),
        )

        for logo_map in logo_mappings:
            setattr(corpobj, logo_map[1], d['logo'][logo_map[0]])

        if int(d['allianceID']):
            corpobj.alliance, created = EVEPlayerAlliance.objects.get_or_create(id=d['allianceID'])

        # Skip looking up the CEOs for NPC corps and ones with no CEO defined (dead corps)
        if corp_id > 1000182 and int(d['ceoID']) > 1:
            import_eve_character.delay(d['ceoID'], callback=link_ceo.subtask(corporation=corpobj.id))
        else:
            corpobj.ceo_character = None

        corpobj.api_last_updated = datetime.utcnow()
        corpobj.save()

    return EVEPlayerCorporation.objects.get(pk=corpobj.pk)


@task(ignore_result=True)
def link_ceo(corporation, character):
    """ Links a character to the CEO position of a corporation """
    corpobj = EVEPlayerCorporation.objects.filter(id=corporation).update(ceo_character=EVEPlayerCharacter.objects.get(id=character))


@task(ignore_result=True)
def import_corp_members(key_id, character_id):
    """
    This function pulls all corporation members from the EVE API using a director's
    API key. It'll add as much information as it can about the character.
    """

    log = import_corp_members.get_logger()

    try:
        acc = EVEAccount.objects.get(pk=key_id)
    except EVEAccount.DoesNotExist:
        return

    # grab and decode /corp/MemberTracking.xml.aspx
    if gargoyle.is_active('eve-cak') and acc.api_keytype == API_KEYTYPE_CORPORATION:
        if not acc.has_access(11) and not acc.has_access(25):
            log.error('Key does not have access to MemberTrackingLimited or MemberTrackingExtended', extra={'data': {'key_id': key_id, 'character_id': character_id}})
            return
        auth_params = {'keyid': acc.api_user_id, 'vcode': acc.api_key, 'characterID': character_id }
        if acc.has_access(25):
            auth_params['extended'] = 1
    else:
        auth_params = {'userID': acc.api_user_id, 'apiKey': acc.api_key, 'characterID': character_id }
    char_doc = CachedDocument.objects.api_query('/corp/MemberTracking.xml.aspx',
                                                   params=auth_params,
                                                   no_cache=False,
                                                   timeout=60)

    pdoc = basic_xml_parse_doc(char_doc)
    if not 'eveapi' in pdoc or not 'result' in pdoc['eveapi']:
        log.error('Invalid XML document / API Error recceived', extra={'data': {'xml': char_doc.body, 'key_id': key_id, 'character_id': character_id}})
        return

    corp = EVEPlayerCharacter.objects.get(id=character_id).corporation

    charlist = []
    for character in pdoc['eveapi']['result']['members']:
        charlist.append(int(character['characterID']))
        charobj, created = EVEPlayerCharacter.objects.get_or_create(id=character['characterID'])
        if created:
            charobj.name = character['name']
        charobj.corporation = corp
        charobj.corporation_date = character['startDateTime']
        if 'logonDateTime' in character:
            charobj.last_login = character['logonDateTime']
            charobj.last_logoff = character['logoffDateTime']
            charobj.current_location_id = int(character['locationID'])
        else:
            charobj.last_login = None
            charobj.last_logoff = None
            charobj.current_location_id = None
        charobj.save()
        if created:
            import_eve_character.delay(character['characterID'])

    leftlist = set(corp.eveplayercharacter_set.all().values_list('id', flat=True)) - set(charlist)
    for id in leftlist:
        import_eve_character.delay(id)

