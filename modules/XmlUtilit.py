from xml.dom import minidom

import xml.etree.ElementTree as ElementTree
from modules.MagnitudeParser import parse


supportedTypes = { 'str': ( lambda v: v, lambda s: s ),
                   'int': ( lambda v: repr(v), lambda s: int(s,0) ),
                   'bool': ( lambda v: repr(v), lambda s: True if s in ['True','true'] else False),
                   'NoneType': (lambda v: repr(None), lambda s: None),
                   'float': (lambda v: repr(v), lambda s: float(s)),
                   'Magnitude': (lambda v: repr(v), lambda s: parse(s)) }

def typeName( obj ):
    tname = type(obj).__name__
    if tname=='instance':
        tname = obj.__class__.__name__
    return tname

def prettify(elem, commentchar=None):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    text = reparsed.toprettyxml(indent="  ")
    if not commentchar:
        return text
    return ''.join(['# {0}\n'.format(line) for line in text.splitlines()])

def stringToStringOrNone(string):
    return string if string != "None" else None


def xmlEncodeDict( dictionary, element, tagName ):
    for name, attr in dictionary.iteritems():
        if typeName(attr) in supportedTypes:
            e = ElementTree.SubElement(element, tagName, attrib={'type': typeName(attr), 'name':name } )
            e.text = supportedTypes[typeName(attr)][0](attr)
    
    
def xmlEncodeAttributes( dictionary, element ):
    return xmlEncodeDict(dictionary, element, "attribute")
            
def xmlParseDictionary( element, tagName ):
    result = dict()
    for e in element.findall(tagName):
        parser = supportedTypes.get( e.attrib['type'][1], None )
        if parser:
            result[e.attrib['name']] = parser(e.text)
    return result

def xmlParseAttributes( element ):
    return xmlParseDictionary(element, "attribute")


