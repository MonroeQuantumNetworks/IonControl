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
      <xs:element type="ShutterBitsType" name="ShutterBits" minOccurs="0"/>
      <xs:element type="TriggerBitsType" name="TriggerBits" minOccurs="0"/>
      <xs:element type="CounterBitsType" name="CounterBits" minOccurs="0"/>
      <xs:element type="DACType" name="DAC" minOccurs="1"/>
      <xs:element type="ADCType" name="ADC" minOccurs="1"/>
    </xs:sequence>
    <xs:attribute type="xs:string" name="configurationId" use="required"/>
  </xs:complexType>
  <xs:complexType name="DACType">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute type="xs:byte" name="numChannels" use="optional"/>
        <xs:attribute type="xs:string" name="encoding" use="optional"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="ADCType">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute type="xs:byte" name="numChannels" use="optional"/>
        <xs:attribute type="xs:string" name="encoding" use="optional"/>
        <xs:attribute type="xs:string" name="dedicatedfirstChannelNo" use="optional"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="ParameterType">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute type="xs:string" name="address" use="required"/>
        <xs:attribute type="xs:string" name="default" use="optional"/>
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
  <xs:complexType name="ShutterBitType">
    <xs:simpleContent>
      <xs:extension base="xs:string">
        <xs:attribute type="xs:byte" name="bitNo" use="required"/>
        <xs:attribute type="xs:string" name="name" use="required"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:complexType name="ShutterBitsType">
    <xs:sequence>
      <xs:element type="ShutterBitType" name="ShutterBit" maxOccurs="unbounded" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="TriggerBitsType">
    <xs:sequence>
      <xs:element type="ShutterBitType" name="TriggerBit" maxOccurs="unbounded" minOccurs="0"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="CounterBitsType">
    <xs:sequence>
      <xs:element type="ShutterBitType" name="CounterBit" maxOccurs="unbounded" minOccurs="0"/>
    </xs:sequence>
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

class DAADInfo(object):
    def __init__(self, numChannels=0, encoding=None ):
        self.numChannels = numChannels
        self.encoding = encoding

class PulserConfig(object):
    def __init__(self):
        self.description = None
        self.extendedWireIns = list()
        self.statusBits = list()
        self.shutterBits = dict()
        self.triggerBits = dict()
        self.counterBits = dict()
        self.dac = DAADInfo()
        self.adc = DAADInfo()

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
    
def endShutterbit(parent, elem):
    a = elem.attrib
    parent[int(a.get('bitNo'),0)] = a.get('name')
    
def endDAC(parent, elem):
    a = elem.attrib
    parent.dac = DAADInfo( int(a.get("numChannels","0")), a.get("encoding", "None") )
    
def endADC(parent, elem):
    a = elem.attrib
    parent.adc = DAADInfo( int(a.get("numChannels","0")), a.get("encoding", "None") )
    
    
starthandler = { 'Pulser': startPulseProgrammer, 
                 'ExtendedWireIns': lambda parent, elem: parent.extendedWireIns,
                 'StatusBits': lambda parent, elem: parent.statusBits,
                 'ShutterBits': lambda parent, elem: parent.shutterBits,
                 'TriggerBits': lambda parent, elem: parent.triggerBits,
                 'CounterBits': lambda parent, elem: parent.counterBits }
endhandler = { 'Parameter': endParameter,
               'Description': endDescription,
               'StatusBit': endStatusbit,
               'ShutterBit': endShutterbit,
               'TriggerBit': endShutterbit,
               'CounterBit': endShutterbit,
               'DAC': endDAC,
               'ADC': endADC }


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