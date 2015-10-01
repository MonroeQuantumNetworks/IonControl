# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""

import sys
import logging
import numpy
import modules.magnitude as magnitude
from ExternalParameterBase import ExternalParameterBase, nextValue
from ProjectConfig.Project import getProject
from PyQt4 import QtGui
from uiModules.ImportErrorPopup import importErrorPopup

project=getProject()
wavemeterEnabled = project.isEnabled('hardware', 'HighFinesse Wavemeter')
visaEnabled = project.isEnabled('hardware', 'VISA')

if wavemeterEnabled:
    from wavemeter.Wavemeter import Wavemeter

if visaEnabled:
    try:
        import visa
    except ImportError: #popup on failed import of enabled visa
        importErrorPopup('VISA')

if visaEnabled:
    class N6700BPowerSupply(ExternalParameterBase):
        """
        Adjust the current on the N6700B current supply
        """
        className = "N6700 Powersupply"
        _dimension = magnitude.mg(1,'A')
        _outputChannels = {"Curr1": "A", "Curr2": "A", "Curr3": "A", "Curr4": "A", "Volt1": "V" , "Volt2": "V", "Volt3": "V", "Volt4": "V"}
        _outputLookup = { "Curr1": ("Curr",1,"A"), "Curr2": ("Curr",2,"A"), "Curr3": ("Curr",3,"A"), "Curr4": ("Curr",4,"A"),
                          "Volt1": ("Volt",1,"V"), "Volt2": ("Volt",2,"V"), "Volt3": ("Volt",3,"V"), "Volt4": ("Volt",4,"V")}
        _inputChannels = dict({"Curr1":"A", "Curr2":"A", "Curr3":"A", "Curr4":"A", "Volt1":"V", "Volt2":"V", "Volt3":"V", "Volt4":"V"})
        def __init__(self,name,config,instrument="QGABField"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self,name,config)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.rm = visa.ResourceManager()
            self.instrument = self.rm.open_resource( instrument)
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()
            for channel in self._outputChannels:
                self.settings.value[channel] = self._getValue(channel)

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'A'))       # if True go to the target value in one jump

        def _setValue(self, channel, v):
            function, index, unit = self._outputLookup[channel]
            command = "{0} {1},(@{2})".format(function, v.toval(unit), index)
            self.instrument.write(command)#set voltage
            self.settings.value[channel] = v

        def _getValue(self, channel):
            function, index, unit = self._outputLookup[channel]
            command = "{0}? (@{1})".format(function, index)
            self.settings.value[channel] = magnitude.mg(float(self.instrument.query(command)), unit) #set voltage
            return self.settings.value[channel]

        def currentValue(self, channel):
            return self.settings.value[channel]

        def currentExternalValue(self, channel):
            function, index, unit = self._outputLookup[channel]
            command = "MEAS:{0}? (@{1})".format(function, index)
            value = magnitude.mg( float( self.instrument.query(command)), unit )
            return value

        def paramDef(self):
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            return superior

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
        _dimension = magnitude.mg(1,'MHz')
        def __init__(self,name,config, instrument="GPIB0::23::INSTR"):
            ExternalParameterBase.__init__(self,name,config)
            self.setDefaults()
            initialAmplitudeString = self.createAmplitudeString()
            self.rm = visa.ResourceManager()
            self.synthesizer = self.rm.open_resource( instrument)
            self.synthesizer.write(initialAmplitudeString)

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('lockPoint', magnitude.mg(384227.944,'GHz') )      # s delay between subsequent updates
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump
            self.settings.__dict__.setdefault('amplitude_dBm', magnitude.mg(-13) )

        def setValue(self, channel, value):
            """
            Move one steps towards the target, return current value
            """
            if value is None:
                return True
            newvalue, arrived = nextValue(self.settings.value[channel], value, self.settings.stepsize, self.settings.jump)
            self._setValue( channel, newvalue )
            self.displayValueObservable[channel].fire( value=self.settings.value[channel], tip="{0}".format( self.settings.lockPoint - self.settings.value[channel] ) )
            if arrived:
                self.persist(channel, self.settings.value[channel])
            return arrived

        def _setValue(self, channel, value ):
            """Send the command string to the HP8672A to set the frequency to 'value'."""
            value = value.round('kHz')
            command = "P{0:0>8.0f}".format(value.toval('kHz')) + 'Z0' + self.createAmplitudeString()
            #Example string: P03205000Z0K1L6O1 would set the oscillator to 3.205 GHz, -13 dBm
            self.synthesizer.write(command)
            self.settings.value[channel] = value

        def createAmplitudeString(self):
            """Create the string for setting the HP8672A amplitude.

            The string is of the form K_L_O_, where _ is a number or symbol indicating an amplitude."""
            KDict = {0:'0', -10:'1', -20:'2', -30:'3', -40:'4', -50:'5', -60:'6', -70:'7', -80:'8', -90:'9', -100:':', -110:';'}
            LDict = {3:'0', 2:'1', 1:'2', 0:'3', -1:'4', -2:'5', -3:'6', -4:'7', -5:'8', -6:'9', -7:':', -8:';', -9:'<', -10:'='}
            amp = round(self.settings.amplitude_dBm.toval()) #convert the amplitude to a number, and round it to the nearest integer
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

        def paramDef(self):
            """
            return the parameter definition used by pyqtgraph parametertree to show the gui
            """
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'lockpoint', 'type': 'magnitude', 'value': self.settings.lockPoint})
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            superior.append({'name': 'amplitude_dBm', 'type': 'magnitude', 'value': self.settings.amplitude_dBm})
            return superior

        def close(self):
            del self.synthesizer

        def update(self, param, changes):
            """update the parameter. If the amplitude was changed, write the new value to the HP8672A."""
            super(HP8672A, self).update(param, changes) #call parent method
            logger = logging.getLogger(__name__)
            for param, _, data in changes:
                if param.name() == 'amplitude_dBm':
                    self.synthesizer.write(self.createAmplitudeString())
                    logger.info("HP8672A output amplitude set to {0} dBm".format(data))

    class MicrowaveSynthesizerScan(ExternalParameterBase):
        """
        Scan the microwave frequency of microwave synthesizer
        """
        className = "Microwave Synthesizer"
        _dimension = magnitude.mg(1,'MHz')
        def __init__(self,name,config, instrument="GPIB0::23::INSTR"):
            ExternalParameterBase.__init__(self,name,config)
            self.rm = visa.ResourceManager()
            self.synthesizer = self.rm.open_resource( instrument)
            self.setDefaults()

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump

        def _setValue(self, channel, v):
            v = v.round('kHz')
            command = ":FREQ:CW {0:.0f}KHZ".format(v.toval('kHz'))
            self.synthesizer.write(command)
            self.settings.value[channel] = v

        def paramDef(self):
            """
            return the parameter definition used by pyqtgraph parametertree to show the gui
            """
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            return superior

        def close(self):
            del self.synthesizer

    class E4422Synthesizer(ExternalParameterBase):
        """
        Scan the microwave frequency of microwave synthesizer
        """
        className = "E4422 Synthesizer"
        _dimension = magnitude.mg(1,'MHz')
        def __init__(self,name,config, instrument="GPIB0::23::INSTR"):
            ExternalParameterBase.__init__(self,name,config)
            self.rm = visa.ResourceManager()
            self.synthesizer = self.rm.open_resource( instrument)
            self.setDefaults()
            self.settings.value[None] = self._getValue(None)
            self.settings.value['Power'] = self._getValue('Power')
            self.settings.amplitude_dBm = self.settings.value['Power']

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump
            self.settings.__dict__.setdefault('amplitude_dBm', magnitude.mg(-13) )

        def _setValue(self, channel, v):
            if channel is None or channel=='Frequency':
                command = ":FREQ:CW {0:.5f}KHZ".format(v.toval('kHz'))
            elif channel=='Power':
                command = ":POWER {0:.3f}".format(v.toval())
            self.synthesizer.write(command)
            self.settings.value[channel] = v

        def _getValue(self, channel):
            if channel is None or channel=='Frequency':
                answer = self.synthesizer.query(":FREQ:CW?")
                self.settings.value[channel] = magnitude.mg( float(answer), "Hz" )
                return self.settings.value[channel]
            elif channel=='Power':
                answer = self.synthesizer.query(":POWER?")
                self.settings.value[channel] = magnitude.mg( float(answer), "" )
                return self.settings.value[channel]

        def paramDef(self):
            """
            return the parameter definition used by pyqtgraph parametertree to show the gui
            """
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            superior.append({'name': 'amplitude_dBm', 'type': 'magnitude', 'value': self.settings.amplitude_dBm})
            return superior

        def close(self):
            del self.synthesizer

        def update(self, param, changes):
            """update the parameter. If the amplitude was changed, write the new value to the HP8672A."""
            super(E4422Synthesizer, self).update(param, changes) #call parent method
            logger = logging.getLogger(__name__)
            for param, _, data in changes:
                if param.name() == 'amplitude_dBm':
                    self._setValue('Power', self.settings.value['Power'])
                    logger.info("E4422B output amplitude set to {0} dBm".format(data))

    class AgilentPowerSupply(ExternalParameterBase):
        """
        Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via a VCO.
        setValue is voltage of vco
        currentValue and currentExternalValue are current applied voltage
        """
        className = "Agilent Powersupply"
        _dimension = magnitude.mg(1,'V')
        def __init__(self,name,config,instrument="power_supply_next_to_397_box"):
            ExternalParameterBase.__init__(self,name,config)
            self.rm = visa.ResourceManager()
            self.powersupply = self.rm.open_resource( instrument)
            self.savedValue = magnitude.mg( float(self.powersupply.query("volt?")), 'V')
            self.setDefaults()

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(10,'mV'))       # if True go to the target value in one jump
            self.settings.__dict__.setdefault('AOMFreq' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump

        def _setValue(self, channel, value):
            """
            Move one steps towards the target, return current value
            """
            self.powersupply.write("volt {0}".format(value.toval('V')))
            self.settings.value[channel] = value
            logger = logging.getLogger(__name__)
            logger.debug( "setValue volt {0}".format(value.toval('V')) )

        def paramDef(self):
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'AOMFreq', 'type': 'magnitude', 'value': self.settings.AOMFreq})
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            return superior

        def close(self):
            del self.powersupply

    class HP6632B(ExternalParameterBase):
        """
        Set the HP6632B power supply
        """
        className = "HP6632B Power Supply"
        _dimension = magnitude.mg(1,'A')
        _outputChannels = {"Curr": "A", "Volt": "V", "OnOff": ""}
        def __init__(self,name,config,instrument="GPIB0::8::INSTR"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self,name,config)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.instrument = visa.instrument(instrument) #open visa session
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'A'))       # if True go to the target value in one jump

        def _setValue(self, channel, v):
            if channel=="OnOff":
                command = "OUTP ON" if v > 0 else "OUTP OFF"
            elif channel=="Curr":
                command = "Curr {0}".format(v.toval("A"))
            elif channel=="Volt":
                command = "Volt {0}".format(v.toval("V"))
            self.instrument.write(command)
            self.settings.value[channel] = v
            for ch in self._outputChannels:
                self.displayValueObservable[ch].fire( value=self._getValue(ch) )
            return v

        def _getValue(self, channel):
            if channel=="OnOff":
                command, unit = "OUTP?", ""
            elif channel=="Curr":
                command, unit = "MEAS:Curr?", "A"
            elif channel=="Volt":
                command, unit = "Meas:Volt?", "V"
            value = magnitude.mg(float(self.instrument.ask(command)), unit)
            return value

        def currentValue(self, channel):
            return self.settings.value[channel]

        def currentExternalValue(self, channel):
            return self._getValue(channel)

        def setValue(self, channel, value):
            self._setValue(channel, value)
            return True

        def paramDef(self):
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            return superior

        def close(self):
            del self.instrument


    class PTS3500(ExternalParameterBase):
        """
        Set the PTS3500 Frequency Source
        """
        className = "PTS3500 Frequency "
        _dimension = magnitude.mg(1,'Hz')
        _outputChannels = {"Freq": "Hz"}
        _inputChannels = dict({"Freq": "Hz"})
        def __init__(self,name,config,instrument="GPIB0::8::INSTR"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self,name,config)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.instrument = visa.instrument(instrument) #open visa session
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()
    #        for channel in self._outputChannels:
    #            self.settings.value[channel] = self._getValue(channel)

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'Hz'))       # if True go to the target value in one jump

        def _setValue(self, channel, v):
            unit= self._outputChannels[channel]
            command = "F{0}\nA1\n".format(v.toval(unit))
            self.instrument.write(command)
            self.settings.value[channel] = v

        # def _getValue(self, channel):
        #     function, unit = self._outputLookup[channel]
        #     if channel=="OnOff":
        #         command = "OUTP?"
        #     else:
        #         command = "MEAS:{0}?".format(function)
        #     self.settings.value[channel] = magnitude.mg(float(self.instrument.ask(command)), unit)
        #     return self.settings.value[channel]

        def currentValue(self, channel):
            return self.settings.value[channel]

    #     def currentExternalValue(self, channel):
    #         function, unit = self._outputLookup[channel]
    #         if channel=="OnOff":
    #             command = "OUTP?"
    #         else:
    #             command = "MEAS:{0}?".format(function)
    #         value = magnitude.mg( float( self.instrument.ask(command)), unit )
    #         return value

        def paramDef(self):
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            return superior

        def close(self):
            del self.instrument


    class DS345(ExternalParameterBase):
        """
        Set the DS345 SRS Function Generator
        """
        className = "DS345 SRS Function Generator "
        _dimension = magnitude.mg(1,'Hz')
        _outputChannels = {"Freq": "Hz", "Ampl": "dB"}
        _outputLookup = { "Freq": ("FREQ","Hz"),
                          "Ampl": ("AMPL","dB")}
        _inputChannels = dict({"Freq":"MHz", "Ampl":"dB"})
        def __init__(self,name,config,instrument="GPIB0::8::INSTR"):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self,name,config)
            logger.info( "trying to open '{0}'".format(instrument) )
            self.instrument = visa.instrument(instrument) #open visa session
            logger.info( "opened {0}".format(instrument) )
            self.setDefaults()
    #        for channel in self._outputChannels:
    #            self.settings.value[channel] = self._getValue(channel)

        def setDefaults(self):
            ExternalParameterBase.setDefaults(self)
            self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'Hz'))       # if True go to the target value in one jump

        def _setValue(self, channel, v):
            function, unit = self._outputLookup[channel]
            if channel=="Ampl":
             command = "{0}{1}DB".format(function, v.toval(unit))
            else:
             command = "{0} {1}".format(function, v.toval(unit))
            self.instrument.write(command)
            self.settings.value[channel] = v

        # def _getValue(self, channel):
        #     function, unit = self._outputLookup[channel]
        #     command = "MEAS:{0} ?".format(function)
        #     self.settings.value[channel] = magnitude.mg(float(self.instrument.ask(command)), unit)
        #     return self.settings.value[channel]

        def currentValue(self, channel):
            return self.settings.value[channel]

    #     def currentExternalValue(self, channel):
    #         function, unit = self._outputLookup[channel]
    #         if channel=="OnOff":
    #             command = "OUTP?"
    #         else:
    #             command = "MEAS:{0}?".format(function)
    #         value = magnitude.mg( float( self.instrument.ask(command)), unit )
    #         return value

        def paramDef(self):
            superior = ExternalParameterBase.paramDef(self)
            superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
            return superior

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
        def __init__(self,name,config,instrument="power_supply_next_to_397_box"):
            AgilentPowerSupply.__init__(self,name,config,instrument)
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
        _dimension = magnitude.mg(1,'GHz')
        def __init__(self,name,config,instrument=None):
            logger = logging.getLogger(__name__)
            ExternalParameterBase.__init__(self,name,config)
            self.wavemeter = Wavemeter(instrument)
            logger.info( "LaserWavemeterScan savedValue {0}".format(self.savedValue) )
            self.setDefaults()

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
                self.settings.value[channel] = value
                if self.savedValue is None:
                    self.savedValue = self.currentFrequency
            logger.debug( "setFrequency {0}, current frequency {1}".format(self.settings.value[channel], self.currentFrequency) )
            arrived = self.currentFrequency is not None and abs(self.currentFrequency-self.settings.value[channel])<self.settings.maxDeviation
            if arrived:
                self.persist(channel, self.settings.value[channel])
            return arrived


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
    def __init__(self,name,settings,instrument=''):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,settings)
        logger.info( "Opening DummyInstrument {0}".format(instrument) )

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('AOMFreq', magnitude.mg(123,'MHz') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump
        self.settings.value.setdefault('O1', magnitude.mg(1,'kHz'))
        self.settings.value.setdefault('O7', magnitude.mg(7,'kHz'))
        
   
    def _setValue(self, channel, value):
        logger = logging.getLogger(__name__)
        logger.debug( "Dummy output channel {0} set to: {1}".format( channel, value ) )
        self.settings.value[channel] = value
         
    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'AOMFreq', 'type': 'magnitude', 'value': self.settings.AOMFreq})
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior

class DummySingleParameter(ExternalParameterBase):
    """
    DummyParameter, used to debug this part of the software.
    """
    className = "DummySingle"
    _dimension = magnitude.mg(1,'kHz')
    def __init__(self,name,settings,instrument=''):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,settings)
        logger.info( "Opening DummyInstrument {0}".format(instrument) )

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('AOMFreq', magnitude.mg(123,'MHz') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump        
   
    def _setValue(self, channel, value):
        logger = logging.getLogger(__name__)
        logger.debug( "Dummy output channel {0} set to: {1}".format( channel, value ) )
        self.settings.value[channel] = value
         
    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'AOMFreq', 'type': 'magnitude', 'value': self.settings.AOMFreq})
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior
