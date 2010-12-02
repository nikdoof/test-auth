from datetime import datetime
from xml.dom import minidom

from celery.decorators import task

from eve_proxy.models import CachedDocument

from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance
from eve_api.utils import basic_xml_parse
from eve_api.tasks.corporation import import_corp_details


@task(ignore_result=True)
def import_alliance_details():
    """
    Imports all in-game alliances and links their related corporations 

    """

    doc = CachedDocument.objects.api_query('/eve/AllianceList.xml.aspx')
    dom = minidom.parseString(doc.body.encode('utf-8'))
    nodes = dom.getElementsByTagName('result')[0].childNodes

    for alliance in basic_xml_parse(nodes)['alliances']:
        print alliance
        allobj, created = EVEPlayerAlliance.objects.get_or_create(pk=alliance['allianceID'])
        if created:
            allobj.name = alliance['name']
            allobj.ticker = alliance['shortName']
            allobj.date_founded = alliance['startDate']
        allobj.member_count = alliance['memberCount']
        allobj.api_last_updated = datetime.utcnow()
        allobj.save()

        corplist = allobj.eveplayercorporation_set.all().values_list('id', flat=True)

        validcorps = []
        for corp in alliance['memberCorporations']:
            if corp.id not in corplist:
                corpobj, created = EVEPlayerCorporation.objects.get_or_create(pk=corp['corporationID'])
                corpobj.alliance = allobj
                corpobj.save()
                if created:
                    import_corp_details.delay(corp['corporationID'])
            validcorps.append(int(corp['corporationID']))

        delcorps = set(corplist) - set(validcorps)
        EVEPlayerCorporation.objects.filter(id__in=delcorps).update(alliance=None)
