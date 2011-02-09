from datetime import datetime
from xml.dom import minidom

from celery.decorators import task

from eve_proxy.models import CachedDocument

from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance
from eve_api.utils import basic_xml_parse_doc
from eve_api.tasks.corporation import import_corp_details, import_corp_details_result

from django.core.exceptions import ValidationError

@task(ignore_result=True)
def import_alliance_details():
    """
    Imports all in-game alliances and links their related corporations 

    """

    doc = CachedDocument.objects.api_query('/eve/AllianceList.xml.aspx')

    for alliance in basic_xml_parse_doc(doc)['eveapi']['result']['alliances']:
        allobj, created = EVEPlayerAlliance.objects.get_or_create(pk=alliance['allianceID'])
        allobj.name = alliance['name']
        allobj.ticker = alliance['shortName']
        allobj.date_founded = datetime.strptime(alliance['startDate'],"%Y-%m-%d %H:%M:%S")
        allobj.executor, created = EVEPlayerCorporation.objects.get_or_create(id=alliance['executorCorpID'])
        allobj.member_count = alliance['memberCount']
        allobj.api_last_updated = datetime.utcnow()
        allobj.save()

        corplist = allobj.eveplayercorporation_set.all().values_list('id', flat=True)

        validcorps = []
        for corp in alliance['memberCorporations']:
            if int(corp['corporationID']) not in corplist:
                import_corp_details.delay(corp['corporationID'])
            validcorps.append(int(corp['corporationID']))

        delcorps = set(corplist) - set(validcorps)
        EVEPlayerCorporation.objects.filter(id__in=delcorps).update(alliance=None)
