import functools

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from pulser import Ad9912
from modules.magnitude import mg


DDSForm, DDSBase = PyQt4.uic.loadUiType(r'ui\DDS.ui')

def extendTo(array, length, defaulttype):
    for _ in range( len(array), length ):
        array.append(defaulttype())

class DDSUi(DDSForm, DDSBase):
    def __init__(self,config,pulser,parent=None):
        DDSBase.__init__(self,parent)
        DDSForm.__init__(self)
        self.numChannels = 8
        self.config = config
        self.frequency = self.config.get('DDSUi.Frequency',[mg(0,'MHz')]*6)
        extendTo(self.frequency, self.numChannels, lambda: mg(0,'MHz') )
        self.phase = self.config.get('DDSUi.Phase',[mg(0,'rad')]*6)
        extendTo(self.phase, self.numChannels, lambda: mg(0,'rad') )
        self.amplitude = self.config.get('DDSUi.Amplitude',[0]*6)
        extendTo(self.amplitude, self.numChannels, lambda: 0 )
        self.names = self.config.get('DDSUi.Names',['']*6)
        extendTo(self.names, self.numChannels, lambda: '' )
        self.ad9912 = Ad9912.Ad9912(pulser)
        self.autoApply = self.config.get('DDSUi.autoApply',False)
        self.frequencyEven = self.config.get('DDSUi.FrequencyEven',[False]*8)
        self.intFrequency = [0]*8
        
    def setupUi(self,parent):
        DDSForm.setupUi(self,parent)
        self.frequencyUis = [self.frequencyBox0, self.frequencyBox1, self.frequencyBox2, self.frequencyBox3, self.frequencyBox4, self.frequencyBox5, self.frequencyBox6, self.frequencyBox7]
        for channel, box  in enumerate(self.frequencyUis[:7]):  # omit the hardcoded math for channel 7
            box.setValue( self.frequency[channel] )
            box.valueChanged.connect( functools.partial(self.onFrequency, box,channel))
        for channel, box  in enumerate([self.phaseBox0, self.phaseBox1, self.phaseBox2, self.phaseBox3, self.phaseBox4, self.phaseBox5, self.phaseBox6, self.phaseBox7]):
            box.setValue( self.phase[channel] )
            box.valueChanged.connect( functools.partial(self.onPhase, box,channel))
        for channel, box  in enumerate([self.amplitudeBox0, self.amplitudeBox1, self.amplitudeBox2, self.amplitudeBox3, self.amplitudeBox4, self.amplitudeBox5, self.amplitudeBox6, self.amplitudeBox7]):
            box.setValue( self.amplitude[channel] )
            box.editingFinished.connect( functools.partial(self.onAmplitude, box,channel))
        for channel, box in enumerate([self.channelEdit0, self.channelEdit1, self.channelEdit2, self.channelEdit3, self.channelEdit4, self.channelEdit5, self.channelEdit6, self.channelEdit7]):
            box.setText(self.names[channel])
            box.textChanged.connect( functools.partial(self.onName, box,channel) )
        for channel, box in enumerate([self.evenBox0, self.evenBox1, self.evenBox2, self.evenBox3, self.evenBox4, self.evenBox5, self.evenBox6, self.evenBox7]):
            box.setChecked( self.frequencyEven[channel])
            box.stateChanged.connect( functools.partial(self.onEvenChanged, box, channel) )
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

    def onEvenChanged(self, box, channel, state):
        even = state == QtCore.Qt.Checked
        self.frequencyEven[channel] = even
        self.onFrequency(self.frequencyUis[channel], channel, self.frequency[channel])

    def onFrequency(self, box, channel, value):
        intFreq = self.ad9912.setFrequency(channel, box.value(), even=self.frequencyEven[channel] )
        self.intFrequency[channel] = intFreq
        box.setToolTip( hex(intFreq) )
        self.frequency[channel] = box.value()
        if channel in [0,4]:
            intFreq7 = int( (self.intFrequency[4]+self.intFrequency[0])/2 )
            box.setToolTip( hex(intFreq7) )
            value = self.ad9912.rawToMagnitude(intFreq7)
            self.frequencyBox7.setValue(  value )
            self.frequency[7] = value
            self.ad9912.setFrequencyRaw(7, intFreq7)
        if self.autoApply: self.onApply()
        
    def onPhase(self, box, channel, value):
        self.ad9912.setPhase(channel, box.value())
        self.phase[channel] = box.value()
        if self.autoApply: self.onApply()
    
    def onAmplitude(self, box, channel):
        self.ad9912.setAmplitude(channel, box.value())
        self.amplitude[channel] = box.value()
        if self.autoApply: self.onApply()
    
    def onName(self, box, channel, text):
        self.names[channel] = str(text)
        
    def onWriteAll(self):
        for channel, box  in enumerate(self.frequencyUis[:7]):
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
        self.config['DDSUi.FrequencyEven'] = self.frequencyEven
        
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
