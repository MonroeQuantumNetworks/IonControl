from PyQt4 import QtGui
import PyQt4.uic
import functools
from modules import configshelve
import Ad9912
from modules.magnitude import mg

DDSForm, DDSBase = PyQt4.uic.loadUiType(r'ui\DDS.ui')

class DDSUi(DDSForm, DDSBase):
    def __init__(self,config,pulser,parent=None):
        DDSBase.__init__(self,parent)
        DDSForm.__init__(self)
        self.config = config
        self.frequency = self.config.get('DDSUi.Frequency',[mg(0,'MHz')]*6)
        self.phase = self.config.get('DDSUi.Phase',[mg(0,'rad')]*6)
        self.amplitude = self.config.get('DDSUi.Amplitude',[0]*6)
        self.names = self.config.get('DDSUi.Names',['']*6)
        self.ad9912 = Ad9912.Ad9912(pulser)
        self.writeOnStartup = self.config.get('DDSUi.WriteOnStartup',False)
        self.autoApply = self.config.get('DDSUi.autoApply',False)
        
    def setupUi(self,parent):
        DDSForm.setupUi(self,parent)
        for channel, box  in enumerate([self.frequencyBox0, self.frequencyBox1, self.frequencyBox2, self.frequencyBox3, self.frequencyBox4, self.frequencyBox5]):
            box.setValue( self.frequency[channel] )
            box.valueChanged.connect( functools.partial(self.onFrequency, box,channel))
        for channel, box  in enumerate([self.phaseBox0, self.phaseBox1, self.phaseBox2, self.phaseBox3, self.phaseBox4, self.phaseBox5]):
            box.setValue( self.phase[channel] )
            box.valueChanged.connect( functools.partial(self.onPhase, box,channel))
        for channel, box  in enumerate([self.amplitudeBox0, self.amplitudeBox1, self.amplitudeBox2, self.amplitudeBox3, self.amplitudeBox4, self.amplitudeBox5]):
            box.setValue( self.amplitude[channel] )
            box.editingFinished.connect( functools.partial(self.onAmplitude, box,channel))
        for channel, box in enumerate([self.channelEdit0, self.channelEdit1, self.channelEdit2, self.channelEdit3, self.channelEdit4, self.channelEdit5]):
            box.setText(self.names[channel])
            box.textChanged.connect( functools.partial(self.onName, box,channel) )
        self.applyButton.clicked.connect( self.onApply )
        self.resetButton.clicked.connect( self.onReset )
        self.writeAllButton.clicked.connect( self.onWriteAll )
        self.checkBoxWriteOnStartup.setChecked(self.writeOnStartup)
        self.autoApplyBox.setChecked( self.autoApply )
        self.autoApplyBox.stateChanged.connect( self.onStateChanged )
        if self.writeOnStartup:
            self.onWriteAll()
            self.onApply()
            
    def onStateChanged(self, state ):
        self.autoApply = self.autoApplyBox.isChecked()

    def onFrequency(self, box, channel, value):
        self.ad9912.setFrequency(channel, box.value() )
        self.frequency[channel] = box.value()
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
        for channel, box  in enumerate([self.frequencyBox0, self.frequencyBox1, self.frequencyBox2, self.frequencyBox3, self.frequencyBox4, self.frequencyBox5]):
            self.onFrequency( box, channel, box.value() )
        for channel, box  in enumerate([self.phaseBox0, self.phaseBox1, self.phaseBox2, self.phaseBox3, self.phaseBox4, self.phaseBox5]):
            self.onPhase( box, channel, box.value() )
        for channel, box  in enumerate([self.amplitudeBox0, self.amplitudeBox1, self.amplitudeBox2, self.amplitudeBox3, self.amplitudeBox4, self.amplitudeBox5]):
            self.onAmplitude( box, channel )
        if self.autoApply: self.onApply
        
    def saveConfig(self):
        self.config['DDSUi.Frequency'] = self.frequency
        self.config['DDSUi.Phase'] = self.phase
        self.config['DDSUi.Amplitude'] = self.amplitude
        self.config['DDSUi.Names'] = self.names
        self.config['DDSUi.WriteOnStartup'] = self.checkBoxWriteOnStartup.isChecked()
        self.config['DDSUi.autoApply'] = self.autoApply
        
    def onApply(self):
        self.ad9912.update(0x3f)
        
    def onReset(self):
        self.ad9912.reset(0x3f)
             
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    with configshelve.configshelve("test") as config:
        ui = DDSUi(config,None)
        ui.setupUi(ui)
        ui.show()
        sys.exit(app.exec_())
