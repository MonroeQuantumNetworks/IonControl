# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 22:00:58 2013

@author: pmaunz
"""
import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic

import ShutterHardwareTableModel


ShutterForm, ShutterBase = PyQt4.uic.loadUiType(r'ui\Shutter.ui')

class ShutterUi(ShutterForm, ShutterBase):
    onColor =  QtGui.QColor(QtCore.Qt.green)
    offColor =  QtGui.QColor(QtCore.Qt.red)
    def __init__(self,pulserHardware,outputname,config, dataContainer, parent=None):
        ShutterBase.__init__(self,parent)
        ShutterForm.__init__(self)
        self.pulserHardware = pulserHardware
        self.outputname = outputname
        self.config = config
        self.configname = 'ShutterUi.'+self.outputname
        self.dataContainer = dataContainer
        
    def setupUi(self,parent,dynupdate=False):
        logger = logging.getLogger(__name__)
        ShutterForm.setupUi(self,parent)
        self.setAtStartup = self.config.get(self.configname+".SetAtStartup",False)
        self.checkBoxSetAtStartup.setChecked(self.setAtStartup)
        self.shutterTableModel = ShutterHardwareTableModel.ShutterHardwareTableModel(self.pulserHardware,self.outputname, self.dataContainer )
        if self.setAtStartup:
            logger.info( "Set old shutter values {0} {1}".format( (self.configname, 'Value') in self.config, self.config.get((self.configname, 'Value'),0) ) )
            self.shutterTableModel.shutter = self.config.get((self.configname, 'Value'),0) 
        self.shutterTableModel.offColor = self.offColor
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.resizeRowsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)
        if dynupdate:    # we only want this connection for the shutter, not the trigger
            self.pulserHardware.shutterChanged.connect( self.shutterTableModel.updateShutter )
        
    def saveConfig(self):
        self.config[self.configname+".SetAtStartup"] = self.checkBoxSetAtStartup.isChecked()
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
        self.applyButton.clicked.connect( self.onApply )
        
    def onApply(self):
        self.pulserHardware.xem.ActivateTriggerIn(0x41,2)
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = ShutterUi()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
