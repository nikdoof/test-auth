from xml.dom import minidom
from eve_proxy.models import CachedDocument

def basic_xml_parse(nodes):
    """ Parses a minidom set of nodes into a tree dict """
    values = {}
    for node in nodes:
        print node
        if node.nodeType == 1:
            node.normalize()
            if len(node.childNodes) == 1:
                if node.attributes.keys():
                    values[node.tagName] = {}
                    for e in node.attributes.keys():
                        values[node.tagName][e] = node.attributes[e].value
                    values[node.tagName]['value'] = node.childNodes[0].nodeValue
                else:
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
