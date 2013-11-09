import xml.etree.ElementTree as ElementTree
from xml.dom import minidom


def prettify(elem, commentchar=None):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    text = reparsed.toprettyxml(indent="  ")
    if not commentchar:
        return text
    return ''.join(['# {0}\n'.format(line) for line in text.splitlines()])
