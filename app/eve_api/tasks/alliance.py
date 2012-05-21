from datetime import datetime
from xml.dom import minidom

from celery.task import task

from eve_proxy.models import CachedDocument
from eve_proxy.exceptions import DocumentRetrievalError

from eve_api.models import EVEAccount, EVEPlayerCorporation, EVEPlayerAlliance
from eve_api.utils import basic_xml_parse_doc
from eve_api.tasks.corporation import import_corp_details, import_corp_details_result

from django.core.exceptions import ValidationError
from django.utils.timezone import now, utc

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
            allobj.date_founded = datetime.strptime(alliance['startDate'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=utc)
            allobj.executor, created = EVEPlayerCorporation.objects.get_or_create(id=alliance['executorCorpID'])
            allobj.member_count = alliance['memberCount']
            allobj.api_last_updated = now()
            allobj.save()

            members = [int(corp['corporationID']) for corp in alliance['memberCorporations']]
            EVEPlayerCorporation.objects.filter(id__in=members).update(alliance=allobj)
            EVEPlayerCorporation.objects.filter(alliance=allobj).exclude(id__in=members).update(alliance=None)

            # Import any corps missing from DB
            importlist = set(members) - set(EVEPlayerCorporation.objects.filter(id__in=members).values_list('id', flat=True))
            for id in importlist:
                import_corp_details.delay(id)
    else:
        # We got a error, retry
        import_alliance_details.retry()
