from xml.dom import minidom
from django.db import models
from eve_proxy.models import CachedDocument

class InvalidCorpID(Exception):
    """
    Thrown when an invalid corp id is given in an api query.
    """
    def __init__(self, id):
        self.value = "ID: %s does not match any corporation." % id
        
    def __str___(self):
        return repr(self.value)
    
def _api_get_id_from_name(name):
    """
    Queries the EVE API looking for the ID of the specified corporation,
    alliance, or character based on its name. This is not case sensitive.
    
    name: (str) Corporation name to search for.
    """
    query_doc = CachedDocument.objects.api_query('/eve/CharacterID.xml.aspx',
                                                 params={'names': name})
    query_dat = query_doc.body.decode("utf-8", "replace")
    dom = minidom.parseString(query_dat)
    
    id_node = dom.getElementsByTagName('row')[0]
    object_id = id_node.getAttribute('characterID')
    
    if object_id == '0':
        raise self.model.DoesNotExist('EVE API returned no matches for the provided corp name.')
    else:
        return int(object_id)
    
class EVEPlayerCharacterManager(models.Manager):
    def api_get_id_from_name(self, name):
        """
        This uses a common call for corps, characters, and alliances.
        """
        return _api_get_id_from_name(name)

class EVEPlayerAllianceManager(models.Manager):
    def api_get_id_from_name(self, name):
        """
        This uses a common call for corps, characters, and alliances.
        """
        return _api_get_id_from_name(name)

class EVEPlayerCorporationManager(models.Manager):
    def get_or_query_by_id(self, corp_id):
        """
        Queries for a corporation. If the corp can't be founded, check the
        EVE API service for information on it. If a match still can't be
        found, return EVEPlayerCorporation.DoesNotExist.
        
        corp_id: (int) Corp's ID.
        """
        try:
            return self.get(id=corp_id)
        except self.model.DoesNotExist:
            try:
                self.api_corp_sheet_xml(corp_id)
                new_corp = self.create(id=corp_id)
                new_corp.query_and_update_corp()
                return new_corp
            except InvalidCorpID:
                raise
    
    def api_get_id_from_name(self, name):
        """
        This uses a common call for corps, characters, and alliances.
        """
        return _api_get_id_from_name(name)
        
    def api_corp_sheet_xml(self, id):
        """
        Returns a corp's data sheet from the EVE API in the form of an XML 
        minidom doc.  
        """
        corp_doc = CachedDocument.objects.api_query('/corp/CorporationSheet.xml.aspx',
                                                    params={'corporationID': id})
        
        # Convert incoming data to UTF-8.
        dom = minidom.parseString(corp_doc.body.encode('utf-8'))
        
        error_node = dom.getElementsByTagName('error')
        
        # If there's an error, see if it's because the corp doesn't exist.
        if error_node:
            error_code = error_node[0].getAttribute('code')
            if error_code == '523':
                raise InvalidCorpID(id)
        
        return dom
        
