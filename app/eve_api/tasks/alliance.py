from datetime import datetime
from xml.dom import minidom

from celery.decorators import task

from eve_proxy.models import CachedDocument
from eve_proxy.exceptions import DocumentRetrievalError

from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance
from eve_api.utils import basic_xml_parse_doc
from eve_api.tasks.corporation import import_corp_details, import_corp_details_result

from django.core.exceptions import ValidationError

@task(ignore_result=True, default_retry_delay=10 * 60)
def import_alliance_details():
    """
    Imports all in-game alliances and links their related corporations 

    """

    try:
        doc = CachedDocument.objects.api_query('/eve/AllianceList.xml.aspx')
    except DocumentRetrievalError, exc:
        import_alliance_details.retry(exc=exc)
        return

    parsedoc = basic_xml_parse_doc(doc)

    if 'eveapi' in parsedoc and not 'error' in parsedoc['eveapi']:
        for alliance in parsedoc['eveapi']['result']['alliances']:
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
    else:
        # We got a error, retry
        import_alliance_details.retry()
