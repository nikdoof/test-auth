from celery.task import task

from eve_proxy.models import CachedDocument
from eve_api.utils import basic_xml_parse_doc
from eve_api.models import EVESkill, EVESkillGroup

@task()
def import_eve_skills():
    """
    Imports the skill tree and groups
    """

    char_doc = CachedDocument.objects.api_query('/eve/SkillTree.xml.aspx')
    d = basic_xml_parse_doc(char_doc)['eveapi']
    if 'error' in d:
        return
    values = d['result']

    for group in values['skillGroups']:
        gobj, created = EVESkillGroup.objects.get_or_create(id=group['groupID'])
        if created or not gobj.name or not gobj.name == group['groupName']:
            gobj.name = group['groupName']
            gobj.save()

        for skill in group['skills']:
            skillobj, created = EVESkill.objects.get_or_create(id=skill['typeID'])
            if created or not skillobj.name or not skillobj.group or not skillobj.name == skill['typeName']:
                skillobj.name = skill['typeName']
                skillobj.group = gobj
                skillobj.save()

