from xml.dom import minidom
from eve_proxy.models import CachedDocument

def basic_xml_parse(nodes):
    """ Parses a minidom set of nodes into a tree dict """
    values = {}
    for node in nodes:
        if node.nodeType == 1:
            node.normalize()
            if len(node.childNodes) == 1:
                values[node.tagName] = node.childNodes[0].nodeValue
            else:
                nv = {}
                if node.tagName == "rowset":
                    rset = []
                    for nd in node.childNodes:
                        if nd.nodeType == 1:
                            d = {}
                            for e in nd.attributes.keys():
                                d[e] = nd.attributes[e].value

                            if len(nd.childNodes) > 0:
                                p = basic_xml_parse(nd.childNodes)
                                for i in p.keys():
                                    d[i] = p[i]

                            rset.append(d)
                    values[node.attributes['name'].value] = rset
                else:
                    values[node.tagName] = basic_xml_parse(node.childNodes)

    return values

def basic_xml_parse_doc(doc):
    """
    Parses a CachedDocument object into a dict
    """

    if type(doc) == CachedDocument:
        dom = minidom.parseString(doc.body.encode('utf-8'))
        return basic_xml_parse(dom.childNodes)

    return {}


def test():
    doc = CachedDocument.objects.api_query('/server/ServerStatus.xml.aspx')
    #print basic_xml_parse_doc(doc)

    doc = CachedDocument.objects.api_query('/corp/CorporationSheet.xml.aspx', {'corporationID': 1018389948 })
    #print basic_xml_parse_doc(doc)

    return basic_xml_parse_doc(CachedDocument.objects.api_query('/eve/AllianceList.xml.aspx'))

