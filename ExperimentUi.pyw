# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:37:41 2012

@author: pmaunz
"""

import sys
import os.path
#import sip
#sip.setapi("QString",2)
#sip.setapi("QVariant",2)
#sip.setapi("QDate",2)
#sip.setapi("QDateTime",2)
#sip.setapi("QTextStream",2)
#sip.setapi("QTime",2)
#sip.setapi("QUrl",2)

sys.path.append(os.path.abspath(r'modules'))
sys.path.append(os.path.abspath(r'ui'))

import CounterWidget
import ScanExperiment
#import TDCWidget
#import FastTDCWidget
import SettingsDialog
import testExperiment
#import testQwt
import configshelve
import FromFile
import PulseProgramUi
import ShutterUi
import DDSUi
import PulserHardware

import PyQt4.uic
from PyQt4 import QtCore, QtGui 

printconfiguration = False

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
        # initialize PulseProgramUi
        self.pulseProgramDialog = PulseProgramUi.PulseProgramSetUi(self.config)
        self.pulseProgramDialog.setupUi(self.pulseProgramDialog)
        
        self.settingsDialog = SettingsDialog.SettingsDialog(self.config,self.parent)
        self.settingsDialog.setupUi(self)
        self.settings = self.settingsDialog.settings        
        self.pulserHardware = PulserHardware.PulserHardware(self.settingsDialog.settings.xem)

        for widget,name in [ (CounterWidget.CounterWidget(self.settings), "Simple Counter"), 
                             (ScanExperiment.ScanExperiment(self.settings), "Scanning"),
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
            widget.ClearStatusMessage.connect( self.statusbar.clearMessage)
            widget.StatusMessage.connect( self.statusbar.showMessage)
               
        self.shutterUi = ShutterUi.ShutterUi(self.pulserHardware, 'shutter')
        self.shutterUi.setupUi(self.shutterUi)
        self.shutterDockWidget.setWidget( self.shutterUi )

        self.triggerUi = ShutterUi.ShutterUi(self.pulserHardware, 'trigger')
        self.triggerUi.offColor =  QtGui.QColor(QtCore.Qt.white)
        self.triggerUi.setupUi(self.triggerUi)
        self.triggerDockWidget.setWidget( self.triggerUi )

        self.DDSUi = DDSUi.DDSUi()
        self.DDSUi.setupUi(self.DDSUi)
        self.DDSDockWidget.setWidget( self.DDSUi )
               
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
        self.currentTab = self.tabList[self.config.get('MainWindow.currentIndex',0)]
        self.tabWidget.setCurrentIndex( self.config.get('MainWindow.currentIndex',0) )
        self.currentTab.activate()
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
        self.initMenu()
        
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
        
    def onSettingsApply(self,settings):
        self.settings = settings
        self.pulserHardware = PulserHardware.PulserHardware(self.settings.xem)
        print self.settings.deviceSerial, self.settings.deviceDescription
        for tab in self.tabList:
            if hasattr(tab,'updateSettings'):
                tab.updateSettings(self.settings,active=(tab == self.currentTab))
                
    def onClose(self):
        print "onClose"
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabList:
            tab.onClose()
        self.config['Settings.deviceSerial'] = self.settings.deviceSerial
        self.config['Settings.deviceDescription'] = self.settings.deviceDescription
        self.config['MainWindow.currentIndex'] = self.tabWidget.currentIndex()
        print "tabWidget.currentIndex()", self.config['MainWindow.currentIndex']
        self.currentTab.deactivate()
        self.parent.close()
        self.pulseProgramDialog.close()
        self.pulseProgramDialog.done(0)
        self.settingsDialog.close()
        self.settingsDialog.done(0)

    def onMessageWrite(self,message):
        cursor = self.textEditConsole.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(message)
        self.textEditConsole.setTextCursor(cursor)
        self.textEditConsole.ensureCursorVisible()
        
    def closeEvent(self,e):
        self.onClose()

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    #MainWindow = QtGui.QMainWindow()
    logger = Logger()    
    sys.stdout = logger
    sys.stderr = logger
    with configshelve.configshelve("experiment-gui") as config:
        if printconfiguration:
            for name, item in config.iteritems():
                print name, item
        ui = WidgetContainerUi(config)
        ui.setupUi(ui)
        logger.textWritten.connect(ui.onMessageWrite)
        ui.show()
        sys.exit(app.exec_())
