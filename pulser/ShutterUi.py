# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 22:00:58 2013

@author: pmaunz
"""
import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from pulser import ShutterHardwareTableModel

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\Shutter.ui')
ShutterForm, ShutterBase = PyQt4.uic.loadUiType(uipath)

class ShutterUi(ShutterForm, ShutterBase):
    onColor =  QtGui.QColor(QtCore.Qt.green)
    offColor =  QtGui.QColor(QtCore.Qt.red)
    def __init__(self,pulserHardware,outputname,config, dataContainer, size=32, parent=None):
        ShutterBase.__init__(self,parent)
        ShutterForm.__init__(self)
        self.pulserHardware = pulserHardware
        self.outputname = outputname
        self.config = config
        self.configname = 'ShutterUi.'+self.outputname
        self.dataContainer = dataContainer
        self.size = size
        self.bitsLookup = sorted(dataContainer[0].defaultDict.keys())
        self.size = max(size, self.bitsLookup[-1] + 1) if self.bitsLookup else size
        
    def setupUi(self,parent,dynupdate=False):
        logger = logging.getLogger(__name__)
        ShutterForm.setupUi(self,parent)
        self.applyButton.setVisible(False)
        self.shutterTableModel = ShutterHardwareTableModel.ShutterHardwareTableModel(self.pulserHardware,self.outputname, self.dataContainer, size=self.size )
        logger.info( "Set old shutter values {0} 0x{1:x}".format( (self.configname, 'Value') in self.config, self.config.get((self.configname, 'Value'),0) ) )
        self.shutterTableModel.shutter = self.config.get((self.configname, 'Value'),0) 
        self.shutterTableModel.offColor = self.offColor
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.resizeRowsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)
        if dynupdate:    # we only want this connection for the shutter, not the trigger
            self.pulserHardware.shutterChanged.connect( self.shutterTableModel.updateShutter )
        
    def saveConfig(self):
        self.config[(self.configname, 'Value')] = self.shutterTableModel.shutter
        
    def __repr__(self):
        r = "{0}\n".format(self.__class__)
        for key in ['outputname', 'configname']:
            r += "{0}: {1}\n".format(key, getattr(self,key))
        return r
    
    def setDisabled(self, disabled):
        self.shutterTableView.setEnabled( not disabled )

class TriggerUi(ShutterUi):
    def __init__(self,pulserHardware,outputname,dataContainer, parent=None):
        super(TriggerUi,self).__init__(pulserHardware,outputname,dataContainer, parent)
        
    def setupUi(self,parent):
        super(TriggerUi,self).setupUi(parent)
        self.applyButton.setVisible(True)
        self.applyButton.clicked.connect( self.onApply )
        
    def onApply(self):
        self.pulserHardware.ActivateTriggerIn(0x41,2)
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = ShutterUi()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
