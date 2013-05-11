# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:15:47 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore

SelectionForm, SelectionBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParametersSelection.ui')

import ExternalScannedParameters
import ExternalScannedParametersConfig
import functools

class Settings:
    def __init__(self):
        self.instruments = dict()

class SelectionUi(SelectionForm,SelectionBase):
    selectionChanged = QtCore.pyqtSignal(object)
    
    def __init__(self, config, parent=None):
        SelectionBase.__init__(self,parent)
        SelectionForm.__init__(self)
        self.enabledParameters = dict()
        self.config = config
        self.settings = self.config.get("ExternalScannedParametersSelection.Settings",Settings())
    
    def setupUi(self,MainWindow):
        SelectionForm.setupUi(self,MainWindow)
        for name in ExternalScannedParameters.ExternalScannedParameters.keys():
            widget = ExternalScannedParametersConfig.ConfigUi(name)
            initState = self.settings.instruments.get(name,('',False))
            widget.setupUi(widget,initState)
            self.stackedWidget.addWidget(widget)
            widget.enableCheckBox.stateChanged.connect( functools.partial(self.enableStateChanged,name,widget) )
            if initState[1]:
                self.enableStateChanged(name, widget, QtCore.Qt.Checked)
        self.comboBox.addItems( ExternalScannedParameters.ExternalScannedParameters.keys() )
            
    def enableStateChanged(self,name,widget,state):
        instrument = str(widget.instrumentLineEdit.text())
        print "'{0}' '{1}'".format(name,instrument)
        if state==QtCore.Qt.Checked:
            if name not in self.enabledParameters:
                try:
                    self.settings.instruments[name] = (instrument,True)
                    instance = ExternalScannedParameters.ExternalScannedParameters[name](name,self.config,instrument)
                    self.enabledParameters[name] = instance
                    self.selectionChanged.emit( self.enabledParameters )
                    widget.update( self.enabledParameters[name] )
                except Exception as e:
                    widget.enableCheckBox.setChecked(False)
                    print "Initialization of instrument {0} with option '{1}' failed. Exception: {2}".format(name,instrument,e)
        elif state==QtCore.Qt.Unchecked:
            if name in self.enabledParameters:
                self.settings.instruments[name] = (str(widget.instrumentLineEdit.text()),False)
                self.enabledParameters.pop(name)
                self.selectionChanged.emit( self.enabledParameters )
                widget.update( None )
        print self.enabledParameters.keys()
        
    def onClose(self):
        self.config["ExternalScannedParametersSelection.Settings"] = self.settings
        for inst in self.enabledParameters.values():
            inst.close()
        

if __name__ == "__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = SelectionUi()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())

