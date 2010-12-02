from datetime import datetime, timedelta
from xml.dom import minidom

from celery.decorators import task

from eve_proxy.models import CachedDocument

from eve_api.models import EVEPlayerCorporation, EVEPlayerCharacter, EVEPlayerCharacterRole
from eve_api.app_defines import *
from eve_api.utils import basic_xml_parse
from eve_api.tasks.corporation import import_corp_details


@task()
def import_eve_character(character_id, api_key=None, user_id=None):
    """ 
    Imports a character from the API, providing a API key will populate 
    further details

    """

    char_doc = CachedDocument.objects.api_query('/eve/CharacterInfo.xml.aspx',
                                               params={'characterID': character_id},
                                               no_cache=False)

    dom = minidom.parseString(char_doc.body.encode('utf-8'))
    if dom.getElementsByTagName('error'):
        return
    values = basic_xml_parse(dom.getElementsByTagName('result')[0].childNodes)
    pchar, created = EVEPlayerCharacter.objects.get_or_create(id=character_id)

    pchar.name = values['characterName']
    pchar.security_status = values['securityStatus']

    corp, created = EVEPlayerCorporation.objects.get_or_create(id=values['corporationID'])
    if created:
        import_corp_details.delay(values['corporationID'])
    pchar.corporation = corp
    pchar.corporation_date = values['corporationDate']

    for v in API_RACES_CHOICES:
        val, race = v
        if race == values['race']:
            pchar.race = val
            break

    if api_key and user_id:
        auth_params = {'userID': user_id, 'apiKey': api_key, 'characterID': character_id }
        char_doc = CachedDocument.objects.api_query('/char/CharacterSheet.xml.aspx',
                                                       params=auth_params,
                                                       no_cache=False)

        dom = minidom.parseString(char_doc.body.encode('utf-8'))
        if not dom.getElementsByTagName('error'):

            values = basic_xml_parse(dom.getElementsByTagName('result')[0].childNodes)
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
                    role, created = EVEPlayerCharacterRole.objects.get_or_create(roleid=r['roleID'], name=r['roleName'])
                    pchar.roles.add(role)
                    if r['roleName'] == 'roleDirector':
                        pchar.director = True

            if values['gender'] == 'Male':
                pchar.gender = API_GENDER_MALE
            else:
                pchar.gender = API_GENDER_FEMALE

            total = 0
            for skill in values['skills']:
                total = total + int(skill['skillpoints'])
            pchar.total_sp = total

    pchar.api_last_updated = datetime.utcnow()
    pchar.save()

    return pchar
