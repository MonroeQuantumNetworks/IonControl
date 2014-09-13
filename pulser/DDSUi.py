import functools

from PyQt4 import QtGui
import PyQt4.uic

from pulser import Ad9912
from modules.magnitude import mg
from externalParameter.persistence import DBPersist
from externalParameter.decimation import StaticDecimation
from modules.magnitude import is_magnitude, mg
from functools import partial
import time
from collections import defaultdict

DDSForm, DDSBase = PyQt4.uic.loadUiType(r'ui\DDS.ui')

def extendTo(array, length, defaulttype):
    for _ in range( len(array), length ):
        array.append(defaulttype())

class DDSUi(DDSForm, DDSBase):
    persistSpace = 'DDS'
    def __init__(self,config,pulser,parent=None):
        DDSBase.__init__(self,parent)
        DDSForm.__init__(self)
        self.numChannels = 8
        self.config = config
        self.frequency = self.config.get('DDSUi.Frequency',[mg(0,'MHz')]*8)
        extendTo(self.frequency, self.numChannels, lambda: mg(0,'MHz') )
        self.phase = self.config.get('DDSUi.Phase',[mg(0,'rad')]*8)
        extendTo(self.phase, self.numChannels, lambda: mg(0,'rad') )
        self.amplitude = self.config.get('DDSUi.Amplitude',[0]*8)
        extendTo(self.amplitude, self.numChannels, lambda: 0 )
        self.names = self.config.get('DDSUi.Names',['']*8)
        extendTo(self.names, self.numChannels, lambda: '' )
        self.ad9912 = Ad9912.Ad9912(pulser)
        self.autoApply = self.config.get('DDSUi.autoApply',False)
        self.decimation = defaultdict( lambda: StaticDecimation(mg(30,'s')) )
        self.persistence = DBPersist()
        
    def setupUi(self,parent):
        DDSForm.setupUi(self,parent)
        for channel, box  in enumerate([self.frequencyBox0, self.frequencyBox1, self.frequencyBox2, self.frequencyBox3, self.frequencyBox4, self.frequencyBox5, self.frequencyBox6, self.frequencyBox7]):
            box.setValue( self.frequency[channel] )
            box.valueChanged.connect( functools.partial(self.onFrequency, box,channel))
        for channel, box  in enumerate([self.phaseBox0, self.phaseBox1, self.phaseBox2, self.phaseBox3, self.phaseBox4, self.phaseBox5, self.phaseBox6, self.phaseBox7]):
            box.setValue( self.phase[channel] )
            box.valueChanged.connect( functools.partial(self.onPhase, box,channel))
        for channel, box  in enumerate([self.amplitudeBox0, self.amplitudeBox1, self.amplitudeBox2, self.amplitudeBox3, self.amplitudeBox4, self.amplitudeBox5, self.amplitudeBox6, self.amplitudeBox7]):
            box.setValue( self.amplitude[channel] )
            box.valueChanged.connect( functools.partial(self.onAmplitude, box,channel))
        for channel, box in enumerate([self.channelEdit0, self.channelEdit1, self.channelEdit2, self.channelEdit3, self.channelEdit4, self.channelEdit5, self.channelEdit6, self.channelEdit7]):
            box.setText(self.names[channel])
            box.textChanged.connect( functools.partial(self.onName, box,channel) )
        self.applyButton.clicked.connect( self.onApply )
        self.resetButton.clicked.connect( self.onReset )
        self.writeAllButton.clicked.connect( self.onWriteAll )
        self.autoApplyBox.setChecked( self.autoApply )
        self.autoApplyBox.stateChanged.connect( self.onStateChanged )
        self.onWriteAll()
        self.onApply()
            
    def setDisabled(self, disabled):
        for widget  in [self.frequencyBox0, self.frequencyBox1, self.frequencyBox2, self.frequencyBox3, self.frequencyBox4, self.frequencyBox5, self.frequencyBox6, self.frequencyBox7,
                        self.phaseBox0, self.phaseBox1, self.phaseBox2, self.phaseBox3, self.phaseBox4, self.phaseBox5, self.phaseBox6, self.phaseBox7,
                        self.amplitudeBox0, self.amplitudeBox1, self.amplitudeBox2, self.amplitudeBox3, self.amplitudeBox4, self.amplitudeBox5, self.amplitudeBox6, self.amplitudeBox7]:
            widget.setEnabled( not disabled )        
            
    def onStateChanged(self, state ):
        self.autoApply = self.autoApplyBox.isChecked()

    def onFrequency(self, box, channel, value):
        self.ad9912.setFrequency(channel, box.value() )
        self.frequency[channel] = box.value()
        if self.autoApply: self.onApply()
        self.decimation[(0,channel)].decimate( time.time(), value, partial(self.persistCallback, "Frequency:{0}".format(self.names[channel] if self.names[channel] else channel)) )
        
    def onPhase(self, box, channel, value):
        self.ad9912.setPhase(channel, box.value())
        self.phase[channel] = box.value()
        if self.autoApply: self.onApply()
        self.decimation[(1,channel)].decimate( time.time(), value, partial(self.persistCallback, "Phase:{0}".format(self.names[channel] if self.names[channel] else channel)) )

    def onAmplitude(self, box, channel):
        self.ad9912.setAmplitude(channel, box.value())
        self.amplitude[channel] = box.value()
        if self.autoApply: self.onApply()
        self.decimation[(2,channel)].decimate( time.time(), box.value(), partial(self.persistCallback, "Amplitude:{0}".format(self.names[channel] if self.names[channel] else channel)) )
 
    def persistCallback(self, source, data):
        time, value, minval, maxval = data
        unit = None
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        self.persistence.persist(self.persistSpace, source, time, value, minval, maxval, unit)
    
    def onName(self, box, channel, text):
        self.names[channel] = str(text)
        
    def onWriteAll(self):
        for channel, box  in enumerate([self.frequencyBox0, self.frequencyBox1, self.frequencyBox2, self.frequencyBox3, self.frequencyBox4, self.frequencyBox5, self.frequencyBox6, self.frequencyBox7]):
            self.onFrequency( box, channel, box.value() )
        for channel, box  in enumerate([self.phaseBox0, self.phaseBox1, self.phaseBox2, self.phaseBox3, self.phaseBox4, self.phaseBox5, self.phaseBox6, self.phaseBox7]):
            self.onPhase( box, channel, box.value() )
        for channel, box  in enumerate([self.amplitudeBox0, self.amplitudeBox1, self.amplitudeBox2, self.amplitudeBox3, self.amplitudeBox4, self.amplitudeBox5, self.amplitudeBox6, self.amplitudeBox7]):
            self.onAmplitude( box, channel )
        if self.autoApply: self.onApply
        
    def saveConfig(self):
        self.config['DDSUi.Frequency'] = self.frequency
        self.config['DDSUi.Phase'] = self.phase
        self.config['DDSUi.Amplitude'] = self.amplitude
        self.config['DDSUi.Names'] = self.names
        self.config['DDSUi.autoApply'] = self.autoApply
        
    def onApply(self):
        self.ad9912.update(0xff)
        
    def onReset(self):
        self.ad9912.reset(0xff)
             
if __name__ == "__main__":
    import sys
    from persist import configshelve
    app = QtGui.QApplication(sys.argv)
    with configshelve.configshelve("test") as config:
        ui = DDSUi(config,None)
        ui.setupUi(ui)
        ui.show()
        sys.exit(app.exec_())
