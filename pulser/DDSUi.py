import functools

from PyQt4 import QtGui
import PyQt4.uic

from pulser import Ad9912
from externalParameter.persistence import DBPersist
from externalParameter.decimation import StaticDecimation
from modules.magnitude import is_magnitude, mg
from functools import partial
import time
from collections import defaultdict
from modules.Expression import Expression
from pulser.DDSTableModel import DDSTableModel
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.PyqtUtility import restoreColumnWidth, saveColumnWidth

DDSForm, DDSBase = PyQt4.uic.loadUiType(r'ui\DDS.ui')

def extendTo(array, length, defaulttype):
    for _ in range( len(array), length ):
        array.append(defaulttype())
        
        
class DDSChannelSettings(object):
    expression = Expression()
    def __init__(self):
        self.frequency = mg(0,'MHz')
        self.phase = mg(0)
        self.amplitude = mg(0)
        self.frequencyText = None
        self.phaseText = None
        self.amplitudeText = None
        self.enabled = False
        self.name = ""
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('name','')
        
    def evaluateFrequency(self, globalDict ):
        if self.frequencyText:
            oldfreq = self.frequency
            self.frequency = self.expression.evaluateAsMagnitude(self.frequencyText, globalDict)
            return self.frequency!=oldfreq
        return False
            
    def evaluateAmplitude(self, globalDict ):
        if self.amplitudeText:
            oldamp = self.amplitude
            self.amplitude = self.expression.evaluateAsMagnitude(self.amplitudeText, globalDict)
            return oldamp!=self.amplitude
        return False
    
    def evaluatePhase(self, globalDict ):
        if self.phaseText:
            oldphase= self.phase
            self.phase = self.expression.evaluateAsMagnitude(self.phaseText, globalDict)
            return oldphase!=self.phase
        return False

class DDSUi(DDSForm, DDSBase):
    persistSpace = 'DDS'
    def __init__(self,config,pulser,globalDict,parent=None):
        DDSBase.__init__(self,parent)
        DDSForm.__init__(self)
        self.numChannels = 8
        self.config = config
        self.ad9912 = Ad9912.Ad9912(pulser)
        self.ddsChannels = self.config.get('DDSUi.ddsChannels', [DDSChannelSettings() for _ in range(self.numChannels) ] )
        self.autoApply = self.config.get('DDSUi.autoApply',False)
        self.decimation = defaultdict( lambda: StaticDecimation(mg(30,'s')) )
        self.persistence = DBPersist()
        self.globalDict = globalDict
        self.pulser = pulser
        
    def setupUi(self,parent):
        DDSForm.setupUi(self,parent)
        self.ddsTableModel = DDSTableModel(self.ddsChannels, self.globalDict)
        self.tableView.setModel( self.ddsTableModel )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(2,self.delegate)
        self.tableView.setItemDelegateForColumn(3,self.delegate)
        self.tableView.setItemDelegateForColumn(4,self.delegate)
        restoreColumnWidth( self.tableView, self.config.get('DDSUi.ColumnWidth',[]) )
        self.applyButton.clicked.connect( self.onApply )
        self.resetButton.clicked.connect( self.onReset )
        self.writeAllButton.clicked.connect( self.onWriteAll )
        self.autoApplyBox.setChecked( self.autoApply )
        self.autoApplyBox.stateChanged.connect( self.onStateChanged )
        self.onWriteAll()
        self.onApply()
        self.ddsTableModel.frequencyChanged.connect( self.onFrequency )
        self.ddsTableModel.phaseChanged.connect( self.onPhase )
        self.ddsTableModel.amplitudeChanged.connect( self.onAmplitude )
        self.ddsTableModel.enableChanged.connect( self.onEnableChanged )
        self.pulser.shutterChanged.connect( self.ddsTableModel.onShutterChanged )
            
    def onEnableChanged(self, index, value):
        self.pulser.setShutterBit( 24+index, value )
            
    def setDisabled(self, disabled):
        pass
            
    def onStateChanged(self, state ):
        self.autoApply = self.autoApplyBox.isChecked()

    def onFrequency(self, channel, value):
        self.ad9912.setFrequency(channel, value )
        if self.autoApply: self.onApply()
        self.decimation[(0,channel)].decimate( time.time(), value, partial(self.persistCallback, "Frequency:{0}".format(self.ddsChannels[channel].name if self.ddsChannels[channel].name else channel)) )
        
    def onPhase(self, channel, value):
        self.ad9912.setPhase(channel, value)
        if self.autoApply: self.onApply()
        self.decimation[(1,channel)].decimate( time.time(), value, partial(self.persistCallback, "Phase:{0}".format(self.ddsChannels[channel].name if self.ddsChannels[channel].name else channel)) )

    def onAmplitude(self, channel, value):
        self.ad9912.setAmplitude(channel, value)
        if self.autoApply: self.onApply()
        self.decimation[(2,channel)].decimate( time.time(), value, partial(self.persistCallback, "Amplitude:{0}".format(self.ddsChannels[channel].name if self.ddsChannels[channel].name else channel)) )
 
    def persistCallback(self, source, data):
        time, value, minval, maxval = data
        unit = None
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        self.persistence.persist(self.persistSpace, source, time, value, minval, maxval, unit)
    
    def onWriteAll(self):
        for channel, settings in enumerate( self.ddsChannels ):
            self.ad9912.setFrequency(channel, settings.frequency)
            self.ad9912.setPhase(channel, settings.phase)
            self.ad9912.setAmplitude(channel, settings.amplitude)
        if self.autoApply: 
            self.onApply()
        
    def saveConfig(self):
        self.config['DDSUi.ddsChannels'] = self.ddsChannels
        self.config['DDSUi.autoApply'] = self.autoApply
        self.config['DDSUi.ColumnWidth'] = saveColumnWidth(self.tableView)
        
    def onApply(self):
        self.ad9912.update(0xff)
        
    def onReset(self):
        self.ad9912.reset(0xff)
        
    def evaluate(self, name):
        for channel, setting in enumerate(self.ddsChannels):
            if setting.evaluateFrequency( self.globalDict ):
                self.ad9912.setFrequency(channel, setting.frequency)
            if setting.evaluatePhase( self.globalDict ):
                self.ad9912.setPhase(channel, setting.phase)
            if setting.evaluateAmplitude( self.globalDict ):
                self.ad9912.setAmplitude(channel, setting.amplitude)
        self.tableView.viewport().repaint() 
             
if __name__ == "__main__":
    import sys
    from persist import configshelve
    app = QtGui.QApplication(sys.argv)
    with configshelve.configshelve("test") as config:
        ui = DDSUi(config,None)
        ui.setupUi(ui)
        ui.show()
        sys.exit(app.exec_())
