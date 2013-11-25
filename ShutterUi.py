# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 22:00:58 2013

@author: pmaunz
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic
import ShutterHardwareTableModel
from modules import configshelve
import ProjectSelection
import logging

ShutterForm, ShutterBase = PyQt4.uic.loadUiType(r'ui\Shutter.ui')

class ShutterUi(ShutterForm, ShutterBase):
    onColor =  QtGui.QColor(QtCore.Qt.green)
    offColor =  QtGui.QColor(QtCore.Qt.red)
    def __init__(self,pulserHardware,outputname,config,parent=None):
        ShutterBase.__init__(self,parent)
        ShutterForm.__init__(self)
        self.shutterdict = dict()
        self.pulserHardware = pulserHardware
        self.outputname = outputname
        self.config = config
        self.configname = 'ShutterUi.'+self.outputname
        
    def setupUi(self,parent,dynupdate=False):
        logger = logging.getLogger(__name__)
        ShutterForm.setupUi(self,parent)
        self.setAtStartup = self.config.get(self.configname+".SetAtStartup",False)
        self.checkBoxSetAtStartup.setChecked(self.setAtStartup)
        self.shutterdict = self.config.get(self.configname+".dict",dict())
        self.shutterTableModel = ShutterHardwareTableModel.ShutterHardwareTableModel(self.shutterdict,self.pulserHardware,self.outputname)
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
        self.config[self.configname+".dict"] = self.shutterdict
        self.config[self.configname+".SetAtStartup"] = self.checkBoxSetAtStartup.isChecked()
        self.config[(self.configname, 'Value')] = self.shutterTableModel.shutter
        
    def __repr__(self):
        r = "{0}\n".format(self.__class__)
        for key in ['outputname', 'shutterdict', 'configname']:
            r += "{0}: {1}\n".format(key, getattr(self,key))
        return r

class TriggerUi(ShutterUi):
    def __init__(self,pulserHardware,outputname,parent=None):
        super(TriggerUi,self).__init__(pulserHardware,outputname,parent)
        
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
