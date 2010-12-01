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
                    for nd in node.childNodes:
                        if nd.nodeType == 1:
                            nv[nd.tagName] = nd.childNodes[0].nodeValue
                    values[node.tagName] = nv

    return values
