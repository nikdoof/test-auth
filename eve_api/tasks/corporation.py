from datetime import datetime, timedelta
from xml.dom import minidom

from celery.decorators import task
from eve_proxy.models import CachedDocument
from eve_api.models import EVEPlayerCorporation
from eve_api.api_puller.corp_management import pull_corp_members
from eve_api.utils import basic_xml_parse

        
@task(ignore_result=True)
def import_corp_details(corp_id):
    corp, created = EVEPlayerCorporation.objects.get_or_create(id=corp_id)
    
    if created or not corp.api_last_updated or corp.api_last_updated < (datetime.utcnow() - timedelta(hours=12)):
        corp.query_and_update_corp()
        corp.save()


@task(ignore_result=True)
def import_corp_members(api_userid, api_key, character_id):
    pull_corp_members(api_key, api_userid, character_id)

