from PyQt4 import QtGui
import PyQt4.uic
import functools
from modules import configshelve
import Ad9912

DDSForm, DDSBase = PyQt4.uic.loadUiType(r'ui\DDS.ui')

class DDSUi(DDSForm, DDSBase):
    def __init__(self,config,xem,parent=None):
        DDSBase.__init__(self,parent)
        DDSForm.__init__(self,parent)
        self.config = config
        self.frequency = self.config.get('DDSUi.Frequency',[0]*6)
        self.phase = self.config.get('DDSUi.Phase',[0]*6)
        self.amplitude = self.config.get('DDSUi.Amplitude',[0]*6)
        self.names = self.config.get('DDSUi.Names',['']*6)
        self.ad9912 = Ad9912.Ad9912(xem)
        
    def setupUi(self,parent):
        DDSForm.setupUi(self,parent)
        for channel, box  in enumerate([self.frequencyBox0, self.frequencyBox1, self.frequencyBox2, self.frequencyBox3, self.frequencyBox4, self.frequencyBox5]):
            box.setValue( self.frequency[channel] )
            box.editingFinished.connect( functools.partial(self.onFrequency, box,channel))
        for channel, box  in enumerate([self.phaseBox0, self.phaseBox1, self.phaseBox2, self.phaseBox3, self.phaseBox4, self.phaseBox5]):
            box.setValue( self.phase[channel] )
            box.editingFinished.connect( functools.partial(self.onPhase, box,channel))
        for channel, box  in enumerate([self.amplitudeBox0, self.amplitudeBox1, self.amplitudeBox2, self.amplitudeBox3, self.amplitudeBox4, self.amplitudeBox5]):
            box.setValue( self.amplitude[channel] )
            box.editingFinished.connect( functools.partial(self.onAmplitude, box,channel))
        for channel, box in enumerate([self.channelEdit0, self.channelEdit1, self.channelEdit2, self.channelEdit3, self.channelEdit4, self.channelEdit5]):
            box.setText(self.names[channel])
            box.textChanged.connect( functools.partial(self.onName, box,channel) )
        self.applyButton.clicked.connect( self.onApply )

    def onFrequency(self, box, channel):
        self.ad9912.setFrequency(channel, box.value() )
        self.frequency[channel] = box.value()
        
    def onPhase(self, box, channel):
        self.ad9912.setPhase(channel, box.value())
        self.phase[channel] = box.value()
    
    def onAmplitude(self, box, channel):
        self.ad9912.setAmplitude(channel, box.value())
        self.amplitude[channel] = box.value()
    
    def onName(self, box, channel, text):
        self.names[channel] = str(text)
        
    def closeEvent(self, e):
        self.config['DDSUi.Frequency'] = self.frequency
        self.config['DDSUi.Phase'] = self.phase
        self.config['DDSUi.Amplitude'] = self.amplitude
        self.config['DDSUi.Names'] = self.names
        
    def onApply(self):
        pass
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    with configshelve.configshelve("test") as config:
        ui = DDSUi(config,None)
        ui.setupUi(ui)
        ui.show()
        sys.exit(app.exec_())
