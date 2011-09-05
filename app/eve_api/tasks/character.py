from datetime import datetime, timedelta
from xml.dom import minidom
import logging

from celery.decorators import task
from celery.task.sets import subtask
from gargoyle import gargoyle

from eve_proxy.exceptions import *
from eve_proxy.models import CachedDocument

from eve_api.api_exceptions import *
from eve_api.models import EVEPlayerCorporation, EVEPlayerCharacter, EVEPlayerCharacterRole, EVEPlayerCharacterSkill, EVESkill, EVEAccount, EVEPlayerCharacterEmploymentHistory
from eve_api.app_defines import *
from eve_api.utils import basic_xml_parse, basic_xml_parse_doc


@task()
def import_eve_character(character_id, key_id=None, callback=None, **kwargs):
    """ 
    Imports a character from the API, providing a API key will populate 
    further details. Returns a single EVEPlayerCharacter object

    """

    log = import_eve_character.get_logger()
    try:
        pchar = import_eve_character_func(character_id, key_id, log)
    except APIAccessException, exc:
        log.error('Error importing character - flagging for retry')
        import_eve_character.retry(args=[character_id, key_id, callback], exc=exc, kwargs=kwargs)

    if not pchar:
        log.error('Error importing character %s' % character_id)
    else:
        if callback:
            subtask(callback).delay(character=pchar.id)
        else:
            return pchar


@task()
def import_eve_characters(character_list, key_id=None, callback=None, **kwargs):
    """
    Imports characters from the API, providing a API key will populate
    further details. Returns a list of EVEPlayerCharacter objects

    """

    log = import_eve_characters.get_logger()
    try:
        results = [import_eve_character_func(char, key_id, log) for char in character_list]
    except APIAccessException, exc:
        log.error('Error importing characters - flagging for retry')
        import_eve_characters.retry(args=[character_list, key_id, callback], exc=exc, kwargs=kwargs)
    if callback:
        subtask(callback).delay(characters=results)
    else:
        return results


def import_eve_character_func(character_id, key_id=None, logger=logging.getLogger(__name__)):

    try:
        char_doc = CachedDocument.objects.api_query('/eve/CharacterInfo.xml.aspx', params={'characterID': character_id}, no_cache=False)
    except DocumentRetrievalError, exc:
        logger.error('Error retrieving CharacterInfo.xml.aspx for Character ID %s - %s' % (character_id, exc))
        raise APIAccessException

    d = basic_xml_parse_doc(char_doc)['eveapi']
    if 'error' in d:
        logger.debug('EVE API Error enountered in API document')
        return

    values = d['result']
    pchar, created = EVEPlayerCharacter.objects.get_or_create(id=character_id)

    # Set the character's name, avoid oddities in the XML feed
    if not values['characterName'] == {}:
        pchar.name = values['characterName']
    else:
        pchar.name = ""
    pchar.security_status = values['securityStatus']

    # Set corporation and join date
    corp, created = EVEPlayerCorporation.objects.get_or_create(pk=values['corporationID'])
    from eve_api.tasks.corporation import import_corp_details
    if created or not corp.name or corp.api_last_updated < (datetime.utcnow() - timedelta(hours=12)):
        import_corp_details.delay(values['corporationID'])

    pchar.corporation = corp
    pchar.corporation_date = values['corporationDate']

    # Derrive Race value from the choices
    for v in API_RACES_CHOICES:
        val, race = v
        if race == values['race']:
            pchar.race = val
            break

    # Import employment history if its made available
    if 'employmentHistory' in values:
        reclist = pchar.employmenthistory.values_list('pk', flat=True)
        for emp in values['employmentHistory']:
            if not emp['recordID'] in reclist:
                corp, created = EVEPlayerCorporation.objects.get_or_create(pk=emp['corporationID'])
                if created:
                    import_corp_details.delay(emp['corporationID'])
                eobj, created = EVEPlayerCharacterEmploymentHistory.objects.get_or_create(pk=emp['recordID'], corporation=corp, character=pchar, start_date=emp['startDate'])

    # We've been passed a Key ID, try and work with it
    if key_id:
        try:
            acc = EVEAccount.objects.get(pk=key_id)
        except EVEAccount.DoesNotExist:
            acc = None
    else:
        acc = None

    # Actual Key? Get further information
    if acc:
        if gargoyle.is_active('eve-cak') and acc.is_cak:
            if not acc.has_access(3):
                logger.error('Key %s does not have access to CharacterSheet' % acc.pk)
                return
            auth_params = {'keyid': acc.api_user_id, 'vcode': acc.api_key, 'characterid': character_id }
        else:
            auth_params = {'userID': acc.api_user_id, 'apiKey': acc.api_key, 'characterID': character_id }
        try:
            char_doc = CachedDocument.objects.api_query('/char/CharacterSheet.xml.aspx', params=auth_params, no_cache=False)
        except DocumentRetrievalError, exc:
            logger.error('Error retrieving CharacterSheet.xml.aspx for User ID %s, Character ID %s - %s' % (acc.pk, character_id, exc))
            raise APIAccessException

        doc = basic_xml_parse_doc(char_doc)['eveapi']
        if not 'error' in doc:

            values = doc['result']
            pchar.name = values['name']
            pchar.balance = values['balance']
            pchar.attrib_intelligence = values['attributes']['intelligence']
            pchar.attrib_charisma = values['attributes']['charisma']
            pchar.attrib_perception = values['attributes']['perception']
            pchar.attrib_willpower = values['attributes']['willpower']
            pchar.attrib_memory = values['attributes']['memory']

            # Process the character's skills
            pchar.total_sp = 0
            for skill in values.get('skills', None):
                skillobj, created = EVESkill.objects.get_or_create(pk=skill['typeID'])
                charskillobj, created = EVEPlayerCharacterSkill.objects.get_or_create(skill=skillobj, character=pchar)
                if created or not charskillobj.level == int(skill['level']) or not charskillobj.skillpoints == int(skill['skillpoints']):
                    charskillobj.level = int(skill['level'])
                    charskillobj.skillpoints = int(skill['skillpoints'])
                    charskillobj.save()
                pchar.total_sp = pchar.total_sp + int(skill['skillpoints'])

            if not acc.is_cak or acc.has_access(18):
                try:
                    skillqueue = CachedDocument.objects.api_query('/char/SkillInTraining.xml.aspx', params=auth_params, no_cache=False)
                except DocumentRetrievalError, exc:
                    logger.error('Error retrieving SkillInTraining.xml.aspx for User ID %s, Character ID %s - %s' % (key_id, character_id, exc))
                else:
                    queuedoc = basic_xml_parse_doc(skillqueue)
                    if not 'error' in queuedoc['eveapi'] and 'result' in queuedoc['eveapi']:
                        queuedoc = queuedoc['eveapi']['result']
                        EVEPlayerCharacterSkill.objects.filter(character=pchar).update(in_training=0)
                        if int(queuedoc['skillInTraining']):
                            skillobj, created = EVESkill.objects.get_or_create(pk=queuedoc['trainingTypeID'])
                            charskillobj, created = EVEPlayerCharacterSkill.objects.get_or_create(skill=skillobj, character=pchar)
                            charskillobj.in_training = queuedoc['trainingToLevel']
                            charskillobj.save()
            else:
                EVEPlayerCharacterSkill.objects.filter(character=pchar).update(in_training=0)

            # Process the character's roles
            pchar.roles.clear()
            roles = values.get('corporationRoles', None)
            if roles and len(roles):
                for r in roles:
                    role, created = EVEPlayerCharacterRole.objects.get_or_create(roleid=r['roleID'], name=r['roleName'])
                    pchar.roles.add(role)

            if values['gender'] == 'Male':
                pchar.gender = API_GENDER_MALE
            else:
                pchar.gender = API_GENDER_FEMALE

    pchar.api_last_updated = datetime.utcnow()
    pchar.save()

    if acc:
        if not pchar.id in acc.characters.all().values_list('id', flat=True):
            acc.characters.add(pchar)
        if pchar.director and acc.api_keytype in [API_KEYTYPE_FULL, API_KEYTYPE_CORPORATION]:
            from eve_api.tasks.corporation import import_corp_members
            import_corp_members.delay(key_id=acc.pk, character_id=pchar.id)

    return pchar
