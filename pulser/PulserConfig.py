'''
Created on Mar 7, 2015

@author: pmaunz
'''

from lxml import etree
from modules.stringutilit import stringToBool

xmlschema = etree.XMLSchema( etree.fromstring("""<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" attributeFormDefault="unqualified" elementFormDefault="qualified">
  <xs:element name="PulserList" type="PulserListType"/>
  <xs:complexType name="PulserType">
    <xs:sequence>
      <xs:element type="xs:string" name="Description"/>
      <xs:element type="ExtendedWireInsType" name="ExtendedWireIns" minOccurs="0"/>
      <xs:element type="StatusBitsType" name="StatusBits" minOccurs="0"/>
    </xs:sequence>
    <xs:attribute type="xs:string" name="configurationId" use="required"/>
  </xs:complexType>
  <xs:complexType name="ParameterType">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute type="xs:string" name="address" use="required"/>
        <xs:attribute type="xs:byte" name="default" use="optional"/>
        <xs:attribute type="xs:string" name="bitmask" use="required"/>
        <xs:attribute type="xs:byte" name="shift" use="required"/>
        <xs:attribute type="xs:string" name="name" use="required"/>
        <xs:attribute type="xs:string" name="encoding" use="required"/>
        <xs:attribute type="xs:string" name="enabled" use="required"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="ExtendedWireInsType">
    <xs:sequence>
      <xs:element type="ParameterType" name="Parameter" maxOccurs="unbounded" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="StatusBitType">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute type="xs:byte" name="bitNo" use="required"/>
        <xs:attribute type="xs:string" name="active" use="required"/>
        <xs:attribute type="xs:string" name="name" use="required"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="StatusBitsType">
    <xs:sequence>
      <xs:element type="StatusBitType" name="StatusBit" maxOccurs="unbounded" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="PulserListType">
    <xs:sequence>
      <xs:element type="PulserType" name="Pulser" maxOccurs="unbounded" minOccurs="1"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>""") )

class ExtendedWireParameter(object):
    pass

class PulserConfig(object):
    def __init__(self):
        self.description = None
        self.extendedWireIns = list()
        self.statusBits = list()

def startPulseProgrammer(parent, elem):
    context = PulserConfig()
    parent[int(elem.attrib["configurationId"],0)] = context
    return context

def endParameter(parent, elem):
    a = elem.attrib
    p = ExtendedWireParameter()
    p.address = int(a.get('address'), 0)
    p.default = int(a.get('default','0'), 0)
    p.bitmask = int(a.get('bitmask','0xffffffffffffffff'), 0)
    p.shift = int(a.get('shift', '0'), 0)
    p.name = a.get('name')
    p.encoding = a.get('encoding')
    p.enabled = stringToBool(a.get('enabled'))
    parent.append(p)

def endDescription(parent, elem):
    parent.description = elem.text
    
def endStatusbit(parent, elem):
    a = elem.attrib
    parent.append( (a.get('name'), int(a.get('bitNo'),0), a.get('active')))
    
starthandler = { 'Pulser': startPulseProgrammer, 
                 'ExtendedWireIns': lambda parent, elem: parent.extendedWireIns,
                 'StatusBits': lambda parent, elem: parent.statusBits }
endhandler = { 'Parameter': endParameter,
               'Description': endDescription,
               'StatusBit': endStatusbit }


def getPulserConfiguration( filename ):
    xmlschema.assertValid(etree.parse(filename))
    context = etree.iterparse( filename, events=('end','start'), schema=xmlschema )
    
    stack = list() 
    parent = dict()
    for event, elem in context:
        if event=='start':
            stack.append(parent)
            parent = starthandler.get( elem.tag, lambda parent, elem : parent)(parent, elem)
        elif event=='end':
            endhandler.get( elem.tag, lambda parent, elem: parent)(parent, elem)
            parent = stack.pop()
    return parent
            
    

if __name__ == "__main__":
    print getPulserConfiguration('../config/PulserConfig.xml')