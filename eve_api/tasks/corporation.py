import logging
from datetime import datetime, timedelta
from xml.dom import minidom

from celery.decorators import task
from eve_proxy.models import CachedDocument
from eve_api.models import EVEPlayerCorporation, EVEPlayerCharacter, EVEPlayerAlliance
from eve_api.utils import basic_xml_parse_doc
from eve_api.tasks.character import import_eve_character
from eve_api.api_exceptions import APIAccessException
        
@task(ignore_result=True)
def import_corp_details(corp_id, callback=None, **kwargs):
    log = import_corp_details.get_logger()
    try:
        corp = import_corp_details_func(corp_id, log)
    except APIAccessException, exc:
        log.error('Error importing corporation - queueing for retry')
        if not kwargs:
            kwargs = {}
        import_corp_details.retry(args=[corp_id, callback], exc=exc, kwargs=kwargs)
    else:
        if callback:
            subtask(callback).delay(corporation=corp.id)


@task()
def import_corp_details_result(corp_id, callback=None):
    log = import_corp_details_result.get_logger()
    try:
        corp = import_corp_details_func(corp_id, log)
    except APIAccessException, exc:
        log.error('Error importing corporation')
    else:
        if callback:
            subtask(callback).delay(corporation=corp.id)
        else:
            return corp


def import_corp_details_func(corp_id, log=logging.getLogger(__name__)):

    corpobj, created = EVEPlayerCorporation.objects.get_or_create(id=corp_id)   
    if created or not corpobj.api_last_updated or corpobj.api_last_updated < (datetime.utcnow() - timedelta(hours=12)):

        doc = CachedDocument.objects.api_query('/corp/CorporationSheet.xml.aspx', {'corporationID': corp_id})
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
        corpobj.api_last_updated = datetime.utcnow()
        corpobj.save()

        import_eve_character.delay(d['ceoID'], callback=link_ceo.subtask(corporation=corpobj.id))

    return EVEPlayerCorporation.objects.get(pk=corpobj.pk)


@task(ignore_result=True)
def link_ceo(corporation, character):
    """ Links a character to the CEO position of a corporation """
    corpobj = EVEPlayerCorporation.objects.filter(id=corporation).update(ceo_character=EVEPlayerCharacter.objects.get(id=character))


@task(ignore_result=True)
def import_corp_members(api_userid, api_key, character_id):
    """
    This function pulls all corporation members from the EVE API using a director's
    API key. It'll add as much information as it can about the character.
    """

    # grab and decode /corp/MemberTracking.xml.aspx
    auth_params = {'userID': api_userid, 'apiKey': api_key, 'characterID': character_id }
    char_doc = CachedDocument.objects.api_query('/corp/MemberTracking.xml.aspx',
                                                   params=auth_params,
                                                   no_cache=False)

    set = basic_xml_parse_doc(char_doc)['eveapi']['result']['members']
    corp = EVEPlayerCharacter.objects.get(id=character_id).corporation

    charlist = []
    for character in set:
        charlist.append(int(character['characterID']))
        charobj = EVEPlayerCharacter.objects.filter(id=character['characterID'])
        charobj.update(corporation=corp, last_login=character['logonDateTime'], last_logoff=character['logoffDateTime'], current_location_id=int(character['locationID']), corporation_date=character['startDateTime'])

    for char in EVEPlayerCharacter.objects.filter(corporation=corp).exclude(id__in=charlist):
        import_eve_character.delay(char.id)

