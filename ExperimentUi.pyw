# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:37:41 2012

This is the main gui program for the ExperimentalUi

@author: pmaunz
"""

#import sip
#sip.setapi("QString",2)
#sip.setapi("QVariant",2)
#sip.setapi("QDate",2)
#sip.setapi("QDateTime",2)
#sip.setapi("QTextStream",2)
#sip.setapi("QTime",2)
#sip.setapi("QUrl",2)

import CounterWidget
import ScanExperiment
import ExternalScanExperiment
#import TDCWidget
#import FastTDCWidget
import SettingsDialog
import testExperiment
from modules import configshelve
import FromFile
import PulseProgramUi
import ShutterUi
import DDSUi
import PulserHardware
import DedicatedCounters

import VoltageControl
    
import PyQt4.uic
from PyQt4 import QtCore, QtGui 

class Logger(QtCore.QObject):    
    textWritten = QtCore.pyqtSignal(str)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.terminal = sys.stdout
        self.terminal
    
    def write(self, message):
        self.terminal.write(message)
        self.textWritten.emit(str(message))

WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'ui\Experiment.ui')


class WidgetContainerUi(WidgetContainerBase,WidgetContainerForm):
    def __init__(self,config):
        self.config = config
        super(WidgetContainerUi, self).__init__()
        self.settings = SettingsDialog.Settings()
        self.deviceSerial = config.get('Settings.deviceSerial')
        self.deviceDescription = config.get('Settings.deviceDescription')
    
    def setupUi(self, parent):
        super(WidgetContainerUi,self).setupUi(parent)
        self.parent = parent
        self.tabList = list()
        self.tabDict = dict()
        # initialize PulseProgramUi
        self.pulseProgramDialog = PulseProgramUi.PulseProgramSetUi(self.config)
        self.pulseProgramDialog.setupUi(self.pulseProgramDialog)
        
        self.settingsDialog = SettingsDialog.SettingsDialog(self.config,self.parent)
        self.settingsDialog.setupUi(self)

        self.settings = self.settingsDialog.settings        
        self.pulserHardware = PulserHardware.PulserHardware(self.settings.fpga)

        for widget,name in [ (CounterWidget.CounterWidget(self.settings,self.pulserHardware), "Simple Counter"), 
                             (ScanExperiment.ScanExperiment(self.settings,self.pulserHardware), "Scanning"),
                             (ExternalScanExperiment.ExternalScanExperiment(self.settings,self.pulserHardware),"External Scan"),
                             #(TDCWidget.TDCWidget(),"Time to digital converter" ),
                             #(FastTDCWidget.FastTDCWidget(),"Fast Time to digital converter" ),
                             (FromFile.FromFile(),"From File"), 
                             (testExperiment.test(),"test")
                             ]:
            widget.setupUi( widget, self.config )
            if hasattr(widget,'setPulseProgramUi'):
                widget.setPulseProgramUi( self.pulseProgramDialog )
            self.tabWidget.addTab(widget, name)
            self.tabList.append(widget)
            self.tabDict[name] = widget
            widget.ClearStatusMessage.connect( self.statusbar.clearMessage)
            widget.StatusMessage.connect( self.statusbar.showMessage)
               
        self.shutterUi = ShutterUi.ShutterUi(self.pulserHardware, 'shutter', self.config)
        self.shutterUi.setupUi(self.shutterUi)
        self.shutterDockWidget.setWidget( self.shutterUi )
        print "ShutterUi representation:", repr(self.shutterUi)

        self.triggerUi = ShutterUi.TriggerUi(self.pulserHardware, 'trigger', self.config)
        self.triggerUi.offColor =  QtGui.QColor(QtCore.Qt.white)
        self.triggerUi.setupUi(self.triggerUi)
        self.triggerDockWidget.setWidget( self.triggerUi )

        self.DDSUi = DDSUi.DDSUi(self.config, self.pulserHardware.xem )
        self.DDSUi.setupUi(self.DDSUi)
        self.DDSDockWidget.setWidget( self.DDSUi )
        self.tabDict['Scanning'].NeedsDDSRewrite.connect( self.DDSUi.onWriteAll )
               
        self.tabWidget.currentChanged.connect(self.onCurrentChanged)
        self.actionClear.triggered.connect(self.onClear)
        self.actionPause.triggered.connect(self.onPause)
        self.actionSave.triggered.connect(self.onSave)
        self.actionStart.triggered.connect(self.onStart)
        self.actionStop.triggered.connect(self.onStop)
        self.actionSettings.triggered.connect(self.onSettings)
        self.actionExit.triggered.connect(self.onClose)
        self.actionContinue.triggered.connect(self.onContinue)
        self.actionPulses.triggered.connect(self.onPulses)
        self.actionReload.triggered.connect(self.onReload)
        self.actionVoltageControl.triggered.connect(self.onVoltageControl)
        self.actionDedicatedCounters.triggered.connect(self.showDedicatedCounters)
        self.currentTab = self.tabList[self.config.get('MainWindow.currentIndex',0)]
        self.tabWidget.setCurrentIndex( self.config.get('MainWindow.currentIndex',0) )
        self.currentTab.activate()
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
        self.initMenu()
        #if 'MainWindow.pos' in self.config:
        #    self.move(self.config['MainWindow.pos'])
        if 'MainWindow.size' in self.config:
            self.resize(self.config['MainWindow.size'])
            
        self.dedicatedCountersWindow = DedicatedCounters.DedicatedCounters(self.config, self.pulserHardware)
        self.dedicatedCountersWindow.setupUi(self.dedicatedCountersWindow)
        
        self.voltageControlWindow = VoltageControl.VoltageControl(self.config)
        self.voltageControlWindow.setupUi(self.voltageControlWindow)

    def showDedicatedCounters(self):
        self.dedicatedCountersWindow.show()
        self.dedicatedCountersWindow.setWindowState(QtCore.Qt.WindowActive)
        self.dedicatedCountersWindow.raise_()

    def onVoltageControl(self):
        self.voltageControlWindow.show()
        self.voltageControlWindow.setWindowState(QtCore.Qt.WindowActive)
        self.voltageControlWindow.raise_()
        
    def onClear(self):
        self.currentTab.onClear()
    
    def onSave(self):
        self.currentTab.onSave()
    
    def onStart(self):
        self.currentTab.onStart()
    
    def onPause(self):
        self.currentTab.onPause()
    
    def onStop(self):
        self.currentTab.onStop()
        
    def onContinue(self):
        if hasattr(self.currentTab,'onContinue'):
            self.currentTab.onStop()
        else:
            self.statusbar.showMessage("continue not implemented")    
            
    def onReload(self):
        print "OnReload"
        self.currentTab.onReload()
    
    def onCurrentChanged(self, index):
        self.currentTab.deactivate()
        self.currentTab = self.tabList[index]
        self.currentTab.activate()
        self.initMenu()
        
    def initMenu(self):
        self.menuView.clear()
        if hasattr(self.currentTab,'viewActions'):
            self.menuView.addActions(self.currentTab.viewActions())
        for dock in [self.dockWidgetConsole, self.shutterDockWidget, self.triggerDockWidget, self.DDSDockWidget]:
            self.menuView.addAction(dock.toggleViewAction())
        
    def onSettings(self):
        self.settingsDialog.show()
        
    def onPulses(self):
        self.pulseProgramDialog.show()
        self.pulseProgramDialog.setWindowState(QtCore.Qt.WindowActive)
        self.pulseProgramDialog.raise_()
        if hasattr(self.currentTab,'experimentName'):
            self.pulseProgramDialog.setCurrentTab(self.currentTab.experimentName)
        
    def onSettingsApply(self,settings):
        self.settings = settings
        self.pulserHardware.updateSettings(self.settings.fpga)
        #print self.settings.deviceSerial, self.settings.deviceDescription
        for tab in self.tabList:
            if hasattr(tab,'updateSettings'):
                tab.updateSettings(self.settings,active=(tab == self.currentTab))
                
    def onClose(self):
        self.parent.close()
        
    def onMessageWrite(self,message):
        cursor = self.textEditConsole.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(message)
        self.textEditConsole.setTextCursor(cursor)
        self.textEditConsole.ensureCursorVisible()
        
    def closeEvent(self,e):
        print "closeEvent"
        self.pulserHardware.stopPipeReader()
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabList:
            tab.onClose()
        self.config['Settings.deviceSerial'] = self.settings.deviceSerial
        self.config['Settings.deviceDescription'] = self.settings.deviceDescription
        self.config['MainWindow.currentIndex'] = self.tabWidget.currentIndex()
        self.config['MainWindow.pos'] = self.pos()
        self.config['MainWindow.size'] = self.size()
        self.currentTab.deactivate()
        self.pulseProgramDialog.close()
        self.pulseProgramDialog.done(0)
        self.settingsDialog.close()
        self.settingsDialog.done(0)
        self.DDSUi.closeEvent(None)
        self.shutterUi.close()
        self.triggerUi.close()
        self.dedicatedCountersWindow.onClose()
        self.dedicatedCountersWindow.close()
        self.voltageControlWindow.onClose()
        self.voltageControlWindow.close()
        

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    #MainWindow = QtGui.QMainWindow()
    logger = Logger()    
    sys.stdout = logger
    sys.stderr = logger
    with configshelve.configshelve("experiment-gui") as config:
        ui = WidgetContainerUi(config)
        ui.setupUi(ui)
        logger.textWritten.connect(ui.onMessageWrite)
        ui.show()
        sys.exit(app.exec_())
