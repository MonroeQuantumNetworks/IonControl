# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""

import sys
import logging
import numpy
import modules.magnitude as magnitude
from ExternalParameterBase import ExternalParameterBase
from ProjectConfig.Project import getProject
from PyQt4 import QtGui
from uiModules.ImportErrorPopup import importErrorPopup

project=getProject()
wavemeterEnabled = project.isEnabled('hardware', 'HighFinesse Wavemeter')
visaEnabled = project.isEnabled('hardware', 'VISA')
from PyQt4 import QtCore

if wavemeterEnabled:
    from wavemeter.Wavemeter import Wavemeter

if visaEnabled:
    try:
        import visa
    except ImportError: #popup on failed import of enabled visa
        importErrorPopup('VISA')


class qtHelper(QtCore.QObject):
    newData = QtCore.pyqtSignal(object, object)
    def __init__(self):
        super(qtHelper, self).__init__()

if visaEnabled:
    class N6700BPowerSupply(ExternalParameterBase):
        """
        Adjust the current on the N6700B current supply
        """
        className = "N6700 Powersupply"
        _outputChannels = {"Curr1": "A", "Curr2": "A", "Curr3": "A", "Curr4": "A", "Volt1": "V" , "Volt2": "V", "Volt3": "V", "Volt4": "V"}
        _outputLookup = { "Curr1": ("Curr",1,"A"), "Curr2": ("Curr",2,"A"), "Curr3": ("Curr",3,"A"), "Curr4": ("Curr",4,"A"),
                          "Volt1": ("Volt",1,"V"), "Volt2": ("Volt",2,"V"), "Volt3": ("Volt",3,"V"), "Volt4": ("Volt",4,"V")}
        _inputChannels = dict({"Curr1":"A", "Curr2":"A", "Curr3":"A", "Curr4":"A", "Volt1":"V", "Volt2":"V", "Volt3":"V", "Volt4":"V"})
        def __init__(self, name, config, globalDict, instrument="QGABField"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self, name, config, globalDict)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.rm = visa.ResourceManager()
            self.instrument = self.rm.open_resource( instrument)
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()
            self.initializeChannelsToExternals()
            self.qtHelper = qtHelper()
            self.newData = self.qtHelper.newData

        def setValue(self, channel, v):
            function, index, unit = self._outputLookup[channel]
            command = "{0} {1},(@{2})".format(function, v.toval(unit), index)
            self.instrument.write(command) #set voltage
            return v

        def getValue(self, channel):
            function, index, unit = self._outputLookup[channel]
            command = "{0}? (@{1})".format(function, index)
            return magnitude.mg(float(self.instrument.query(command)), unit) #set voltage

        def getExternalValue(self, channel):
            function, index, unit = self._outputLookup[channel]
            command = "MEAS:{0}? (@{1})".format(function, index)
            value = magnitude.mg( float( self.instrument.query(command)), unit )
            return value

        def close(self):
            del self.instrument
            

    class HP8672A(ExternalParameterBase):
        """
        Scan the laser frequency by scanning a synthesizer HP8672A. (The laser is locked to a sideband)
        setValue is frequency of synthesizer
        currentValue and currentExternalValue are current frequency of synthesizer

        This class programs the 8672A using the directions in the manual, p. 3-17: cp.literature.agilent.com/litweb/pdf/08672-90086.pdf
        """
        className = "HP8672A"
        _outputChannels = {'Freq': 'MHz', 'Power_dBm': ''}
        def __init__(self, name, config, globalDict, instrument="GPIB0::23::INSTR"):
            ExternalParameterBase.__init__(self, name, config, globalDict)
            self.setDefaults()
            initialAmplitudeString = self.createAmplitudeString()
            self.rm = visa.ResourceManager()
            self.synthesizer = self.rm.open_resource( instrument)
            self.synthesizer.write(initialAmplitudeString)

        def setValue(self, channel, value ):
            """Send the command string to the HP8672A to set the frequency to 'value'."""
            if channel =='Freq':
                value = value.round('kHz')
                command = "P{0:0>8.0f}".format(value.toval('kHz')) + 'Z0' + self.createAmplitudeString()
                #Example string: P03205000Z0K1L6O1 would set the oscillator to 3.205 GHz, -13 dBm
            elif channel=='Power_dBm':
                command = self.createAmplitudeString(value)
            self.synthesizer.write(command)
            return value

        def createAmplitudeString(self, value):
            """Create the string for setting the HP8672A amplitude.
            The string is of the form K_L_O_, where _ is a number or symbol indicating an amplitude."""
            KDict = {0:'0', -10:'1', -20:'2', -30:'3', -40:'4', -50:'5', -60:'6', -70:'7', -80:'8', -90:'9', -100:':', -110:';'}
            LDict = {3:'0', 2:'1', 1:'2', 0:'3', -1:'4', -2:'5', -3:'6', -4:'7', -5:'8', -6:'9', -7:':', -8:';', -9:'<', -10:'='}
            amp = round(value.toval()) #convert the amplitude to a number, and round it to the nearest integer
            amp = max(-120, min(amp, 13)) #clamp the amplitude to be between -120 and +13
            Opart = '1' if amp <= 3 else '3' #Determine if the +10 dBm range option is necessary
            if Opart == '3':
                amp -= 10
            if amp >= 0:
                Kpart = KDict[0]
                Lpart = LDict[amp]
            else:
                Kpart = KDict[10*(divmod(amp, 10)[0]+1)]
                Lpart = LDict[divmod(amp, 10)[1]-10]
            return 'K' + Kpart + 'L' + Lpart + 'O' + Opart

        def close(self):
            del self.synthesizer


    class MicrowaveSynthesizer(ExternalParameterBase):
        """
        Scan the microwave frequency of microwave synthesizer
        """
        className = "Microwave Synthesizer"
        _outputChannels = {'Freq': 'MHz', 'Power_dBm': ''}
        def __init__(self, name, config, globalDict, instrument="GPIB0::23::INSTR"):
            ExternalParameterBase.__init__(self, name, config, globalDict)
            self.rm = visa.ResourceManager()
            self.synthesizer = self.rm.open_resource( instrument)
            self.setDefaults()
            self.initializeChannelsToExternals()

        def setValue(self, channel, v):
            if channel =='Freq':
                command = ":FREQ:CW {0:.5f}KHZ".format(v.toval('kHz'))
            elif channel=='Power_dBm':
                command = ":POWER {0:.3f}".format(v.toval())
            self.synthesizer.write(command)
            return v

        def getValue(self, channel):
            if channel=='Frequency':
                answer = self.synthesizer.query(":FREQ:CW?")
                return magnitude.mg( float(answer), "Hz" )
            elif channel=='Power':
                answer = self.synthesizer.query(":POWER?")
                return magnitude.mg( float(answer), "" )

        def close(self):
            del self.synthesizer


    class E4422Synthesizer(ExternalParameterBase):
        """
        Scan the microwave frequency of microwave synthesizer
        """
        className = "E4422 Synthesizer"
        _outputChannels = {'Freq': 'MHz', 'Power_dBm': ''}
        def __init__(self, name, config, globalDict, instrument="GPIB0::23::INSTR"):
            ExternalParameterBase.__init__(self, name, config, globalDict)
            self.rm = visa.ResourceManager()
            self.synthesizer = self.rm.open_resource( instrument)
            self.setDefaults()
            self.initializeChannelsToExternals()

        def setValue(self, channel, v):
            if channel =='Freq':
                command = ":FREQ:CW {0:.5f}KHZ".format(v.toval('kHz'))
            elif channel=='Power_dBm':
                command = ":POWER {0:.3f}".format(v.toval())
            self.synthesizer.write(command)
            return v

        def getValue(self, channel):
            if channel=='Freq':
                answer = self.synthesizer.query(":FREQ:CW?")
                return magnitude.mg( float(answer), "Hz" )
            elif channel=='Power_dBm':
                answer = self.synthesizer.query(":POWER?")
                return magnitude.mg( float(answer), "" )

        def close(self):
            del self.synthesizer


    class AgilentPowerSupply(ExternalParameterBase):
        """
        Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via a VCO.
        setValue is voltage of vco
        currentValue and currentExternalValue are current applied voltage
        """
        className = "Agilent Powersupply"
        _outputChannels = {None: 'V'}
        def __init__(self, name, config, globalDict, instrument="power_supply_next_to_397_box"):
            ExternalParameterBase.__init__(self, name, config, globalDict)
            self.rm = visa.ResourceManager()
            self.powersupply = self.rm.open_resource( instrument)
            self.setDefaults()
            self.initializeChannelsToExternals()

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('AOMFreq' , magnitude.mg(1,'MHz'))     

        def setValue(self, channel, value):
            """
            Move one steps towards the target, return current value
            """
            self.powersupply.write("volt {0}".format(value.toval('V')))
            return value

        def paramDef(self):
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'AOMFreq', 'type': 'magnitude', 'value': self.settings.AOMFreq})
            return superior

        def close(self):
            del self.powersupply

    class HP6632B(ExternalParameterBase):
        """
        Set the HP6632B power supply
        """
        className = "HP6632B Power Supply"
        _outputChannels = {"Curr": "A", "Volt": "V", "OnOff": ""}
        def __init__(self, name, config, globalDict, instrument="GPIB0::8::INSTR"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self, name, config, globalDict)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.rm = visa.ResourceManager()
            self.instrument = self.rm.open_resource(instrument)
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()
            self.initializeChannelsToExternals()

        def setValue(self, channel, v):
            if channel=="OnOff":
                command = "OUTP ON" if v > 0 else "OUTP OFF"
            elif channel=="Curr":
                command = "Curr {0}".format(v.toval("A"))
            elif channel=="Volt":
                command = "Volt {0}".format(v.toval("V"))
            self.instrument.write(command)
            return v

        def getValue(self, channel):
            if channel=="OnOff":
                command, unit = "OUTP?", ""
            elif channel=="Curr":
                command, unit = "MEAS:Curr?", "A"
            elif channel=="Volt":
                command, unit = "Meas:Volt?", "V"
            value = magnitude.mg(float(self.instrument.query(command)), unit)
            return value

        def close(self):
            del self.instrument


    class PTS3500(ExternalParameterBase):
        """
        Set the PTS3500 Frequency Source
        """
        className = "PTS3500 Frequency "
        _outputChannels = {"Freq": "GHz"}
        _outputLookup = { "Freq": ("F","Hz","\\nA1\\n")}
        def __init__(self, name, config, globalDict, instrument="GPIB0::16::INSTR"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self, name, config, globalDict)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.rm = visa.ResourceManager()
            self.instrument = self.rm.open_resource(instrument)
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()
            self.initializeChannelsToExternals()

        def setValue(self, channel, v):
            function, unit, suffix= self._outputLookup[channel]
            command = "{0}{1}{2}".format(function, int(v.toval(unit)), suffix)
            self.instrument.write(command)
            return v

        def close(self):
            del self.instrument


    class DS345(ExternalParameterBase):
        """
        Set the DS345 SRS Function Generator
        """
        className = "DS345 SRS Function Generator "
        _outputChannels = {"Freq": "MHz", "Ampl": "dB"}
        _outputLookup = { "Freq": ("FREQ","Hz"),
                          "Ampl": ("AMPL","dB")}
        def __init__(self, name, config, globalDict, instrument="GPIB0::19::INSTR"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self, name, config, globalDict)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.rm = visa.ResourceManager()
            self.instrument = self.rm.open_resource(instrument)
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()
            self.initializeChannelsToExternals()

        def setValue(self, channel, v):
            function, unit = self._outputLookup[channel]
            if channel=="Ampl":
                command = "{0}{1}DB".format(function, v.toval(unit))
            else:
                command = "{0} {1}".format(function, v.toval(unit))
            self.instrument.write(command)
            return v

        def close(self):
            del self.instrument


if visaEnabled and wavemeterEnabled:
    class LaserWavemeterScan(AgilentPowerSupply):
        """
        Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via a VCO.
        setValue is voltage of vco
        currentValue is applied voltage
        currentExternalValue are frequency read from wavemeter
        """

        className = "Laser VCO Wavemeter"
        _dimension = magnitude.mg(1,'V')
        def __init__(self, name, config, globalDict, instrument="power_supply_next_to_397_box"):
            AgilentPowerSupply.__init__(self, name, config, globalDict, instrument)
            self.setDefaults()
            self.wavemeter = None

        def setDefaults(self):
            AgilentPowerSupply.setDefaults(self)
            self.settings.__dict__.setdefault('wavemeter_address' , 'http://132.175.165.36:8082')       # if True go to the target value in one jump
            self.settings.__dict__.setdefault('wavemeter_channel' , 6 )       # if True go to the target value in one jump
            self.settings.__dict__.setdefault('use_external' , True )       # if True go to the target value in one jump

        def currentExternalValue(self, channel):
            self.wavemeter = Wavemeter(self.settings.wavemeter_address)
            logger = logging.getLogger(__name__)
            self.lastExternalValue = self.wavemeter.get_frequency(self.settings.wavemeter_channel)
            logger.debug( str(self.lastExternalValue) )
            self.detuning=(self.lastExternalValue)
            counter = 0
            while self.detuning is None or numpy.abs(self.detuning)>=1 and counter<10:
                self.lastExternalValue = self.wavemeter.get_frequency(self.settings.wavemeter_channel)
                self.detuning=(self.lastExternalValue-self.settings.value[channel])
                counter += 1
            return self.lastExternalValue

        def asyncCurrentExternalValue(self, callbackfunc ):
            self.wavemeter = Wavemeter(self.settings.wavemeter_address) if self.wavemeter is None else self.wavemeter
            self.wavemeter.asyncGetFrequency(self.settings.wavemeter_channel, callbackfunc)

        def paramDef(self):
            superior = AgilentPowerSupply.paramDef(self)
            superior.append({'name': 'wavemeter_address', 'type': 'str', 'value': self.settings.wavemeter_address})
            superior.append({'name': 'wavemeter_channel', 'type': 'int', 'value': self.settings.wavemeter_channel})
            superior.append({'name': 'use_external', 'type': 'bool', 'value': self.settings.use_external})
            return superior

        def useExternalValue(self, channel):
            return self.settings.use_external

if wavemeterEnabled:
    class LaserWavemeterLockScan(ExternalParameterBase):
        """
        Scan a laser by setting the lock point on the wavemeter lock.
        setValue is laser frequency
        currentValue is currently set value
        currentExternalValue is frequency read from wavemeter
        """
        className = "Laser Wavemeter Lock"
        _outputChannels = { None: "GHz"}
        def __init__(self, name, config, globalDict, instrument=None):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self, name, config, globalDict)
            self.wavemeter = Wavemeter(instrument)
            logger.info( "LaserWavemeterScan savedValue {0}".format(self.savedValue) )
            self.setDefaults()
            self.initializeChannelsToExternals()

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('channel' , 6)
            self.settings.__dict__.setdefault('maxDeviation', magnitude.mg(5,'MHz'))
            self.settings.__dict__.setdefault('maxAge', magnitude.mg(2,'s'))

        def setValue(self, channel, value):
            """
            Move one steps towards the target, return current value
            """
            logger = logging.getLogger(__name__)
            if value is not None:
                self.currentFrequency = self.wavemeter.set_frequency(value, self.settings.channel, self.settings.maxAge)
            logger.debug( "setFrequency {0}, current frequency {1}".format(self.settings.value[channel], self.currentFrequency) )
            arrived = self.currentFrequency is not None and abs(self.currentFrequency-self.settings.value[channel])<self.settings.maxDeviation
            return value, arrived

        def currentExternalValue(self, channel):
            logger = logging.getLogger(__name__)
            self.lastExternalValue = self.wavemeter.get_frequency(self.settings.channel, self.settings.maxAge )
            logger.debug( str(self.lastExternalValue) )
            self.detuning=(self.lastExternalValue)
            self.currentFrequency = self.wavemeter.get_frequency(self.settings.channel, self.settings.maxAge )
            return self.lastExternalValue

        def paramDef(self):
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'channel', 'type': 'int', 'value': self.settings.channel})
            superior.append({'name': 'maxDeviation', 'type': 'magnitude', 'value': self.settings.maxDeviation})
            superior.append({'name': 'maxAge', 'type': 'magnitude', 'value': self.settings.maxAge})
            return superior

class DummyParameter(ExternalParameterBase):
    """
    DummyParameter, used to debug this part of the software.
    """
    className = "Dummy"
    _outputChannels = { 'O1':"Hz",'O7': "Hz"}
    def __init__(self, name, settings, globalDict, instrument=''):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,settings,globalDict)
        logger.info( "Opening DummyInstrument {0}".format(instrument) )
        self.initializeChannelsToExternals()

    def setValue(self, channel, value):
        logger = logging.getLogger(__name__)
        logger.info( "Dummy output channel {0} set to: {1}".format( channel, value ) )
        return value
            

class DummySingleParameter(ExternalParameterBase):
    """
    DummyParameter, used to debug this part of the software.
    """
    className = "DummySingle"
    _outputChannels = {None: "Hz"}

    def __init__(self, name, settings, globalDict, instrument=''):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,settings,globalDict)
        logger.info( "Opening DummyInstrument {0}".format(instrument) )
        self.initializeChannelsToExternals()

    def setValue(self, channel, value):
        logger = logging.getLogger(__name__)
        logger.info("Dummy output channel {0} set to: {1}".format(channel, value))
        return value

    @classmethod
    def connectedInstruments(cls):
        return ['Anything will do']
         
