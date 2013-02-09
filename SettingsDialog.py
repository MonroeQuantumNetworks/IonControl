# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 22:34:06 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
#import ftd2xx

class Settings:
    def __init__(self):
        self.deviceSerial = None
        self.deviceDescription = None

SettingsDialogForm, SettingsDialogBase = PyQt4.uic.loadUiType(r'ui\SettingsDialog.ui')

class SettingsDialog(SettingsDialogForm, SettingsDialogBase):
    def __init__(self,parent):
        SettingsDialogBase.__init__(self,parent)    
        SettingsDialogForm.__init__(self)
        self.deviceMap = dict()
        self.deviceSerialMap = dict()
        self.settings = Settings()
        
    def setupUi(self,recipient):
        super(SettingsDialog,self).setupUi(self)
        self.recipient = recipient
        self.pushButtonScan.clicked.connect( self.scanInstruments )
        self.comboBoxInstruments.currentIndexChanged[str].connect( self.onIndexChanged )
        
    def scanInstruments(self):
        self.comboBoxInstruments.clear()
        self.deviceMap.clear()
        self.deviceSerialMap.clear()
        numdevices = ftd2xx.createDeviceInfoList()
        for num in range(0,numdevices):
            info = ftd2xx.getDeviceInfoDetail(num)
            self.deviceMap[info['description']] = info['serial']
            self.deviceSerialMap[info['serial']] = info
            self.comboBoxInstruments.addItem(info['description'])
        print self.deviceMap
        
    def onIndexChanged(self,description):
        print "New instrument", description, self.deviceMap[str(description)]
        self.settings.deviceSerial = self.deviceMap[str(description)]
        self.settings.deviceDescription = str(description)
        self.settings.deviceInfo = self.deviceSerialMap[self.settings.deviceSerial]
        
    def accept(self):
        print "accept"
        self.lastPos = self.pos()
        self.hide()
        self.recipient.onSettingsApply()        
        
    def reject(self):
        print "reject"
        self.lastPos = self.pos()
        self.hide()
        
    def show(self):
        if hasattr(self, 'lastPos'):
            self.move(self.lastPos)
        QtGui.QDialog.show(self)
        
    def apply(self,button):
        print button.text(), "button pressed"
        if str(button.text())=="Apply":
            self.recipient.onSettingsApply()