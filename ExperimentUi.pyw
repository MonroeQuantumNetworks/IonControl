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

#import CounterWidget
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


class WidgetContainerUi(WidgetContainerForm):
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
        
        for widget,name in [ #(CounterWidget.CounterWidget(), "Simple Counter"), 
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
               
        self.shutterUi = ShutterUi.ShutterUi()
        self.shutterUi.setupUi(self.shutterUi)
        self.shutterDockWidget.setWidget( self.shutterUi )

        self.triggerUi = ShutterUi.ShutterUi()
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
        self.currentTab = self.tabList[0]
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
        if not hasattr(self, 'settingsDialog'):
            self.settingsDialog = SettingsDialog.SettingsDialog(self.parent)
            self.settingsDialog.setupUi(self)
        self.settingsDialog.show()
        
    def onPulses(self):
        self.pulseProgramDialog.show()
        
    def onSettingsApply(self):
        self.settings = self.settingsDialog.settings
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
        self.parent.close()
        self.pulseProgramDialog.close()

    def onMessageWrite(self,message):
        cursor = self.textEditConsole.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(message)
        self.textEditConsole.setTextCursor(cursor)
        self.textEditConsole.ensureCursorVisible()

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    logger = Logger()    
    sys.stdout = logger
    sys.stderr = logger
    with configshelve.configshelve("experiment-gui") as config:
        ui = WidgetContainerUi(config)
        ui.setupUi(MainWindow)
        logger.textWritten.connect(ui.onMessageWrite)
        MainWindow.show()
        sys.exit(app.exec_())
