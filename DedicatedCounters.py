# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtCore
       
DedicatedCountersForm, DedicatedCountersBase = PyQt4.uic.loadUiType(r'ui\DedicatedCounters.ui')

class Settings:
    pass

class DedicatedCounters(DedicatedCountersForm,DedicatedCountersBase ):
   
    def __init__(self,config,pulserHardware,parent=0):
        DedicatedCountersForm.__init__(self,parent)
        DedicatedCountersBase.__init__(self)
        self.config = config
        self.settings = self.config.get('DedicatedCounter.Settings',Settings())
        self.pulserHardware = pulserHardware
        self.paused = False

    def setupUi(self, parent):
        DedicatedCountersForm.setupUi(self,parent)
        self.actionSave.triggered.connect( self.onSave )
        self.actionClear.triggered.connect( self.onClear )
        self.actionPause.triggered.connect( self.onPause )
    
    def onClose(self):
        self.config['DedicatedCounter.Settings'] = self.settings
        
    def reject(self):
        self.config['DedicatedCounter.pos'] = self.pos()
        self.config['DedicatedCounter.size'] = self.size()
        self.pulserHardware.dedicatedDataAvailable.disconnect( self.onData )
        self.hide()
        
    def show(self):
        if 'DedicatedCounter.pos' in self.config:
            self.move(self.config['DedicatedCounter.pos'])
        if 'DedicatedCounter.size' in self.config:
            self.resize(self.config['DedicatedCounter.size'])
        super(DedicatedCounters,self).show()
        self.pulserHardware.dedicatedDataAvailable.connect( self.onData )
        
    def onSave(self):
        pass
    
    def onClear(self):
        pass
    
    def onPause(self):
        self.paused = self.actionPause.isChecked()
        
    def onData(self):
        pass