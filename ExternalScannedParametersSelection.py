# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:15:47 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore

SelectionForm, SelectionBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParametersSelection.ui')
from ExternalScannedParameters import ExternalScannedParameters
from ExternalParameterTableModel import ExternalParameterTableModel 
import functools

def unique(seq):
    seen = set()
    return [ x for x in seq if x not in seen and not seen.add(x)]

class Settings:
    pass

class EnabledParameter:
    def __init__(self):
        self.className = None
        self.name = None
        self.instrument = None
        self.settings = Settings()

class SelectionUi(SelectionForm,SelectionBase):
    selectionChanged = QtCore.pyqtSignal(object)
    
    def __init__(self, config, parent=None):
        SelectionBase.__init__(self,parent)
        SelectionForm.__init__(self)
        self.config = config
        self.previouslyEnabledParameters = self.config.get("ExternalScannedParametersSelection.EnabledParameters",dict())
        self.enabledParameters = dict()
        self.enabledParametersObjects = dict()
    
    def setupUi(self,MainWindow):
        SelectionForm.setupUi(self,MainWindow)
        self.parameterTableModel = ExternalParameterTableModel(self.enabledParameters)
        self.tableView.setModel( self.parameterTableModel )
        self.classComboBox.addItems( ExternalScannedParameters.keys() )
        self.addParameterButton.clicked.connect( self.onAddParameter )
        self.removeParameterButton.clicked.connect( self.onRemoveParameter )
        for parameter in self.previouslyEnabledParameters:
            try:
                instance = ExternalScannedParameters[name](name,parameter.settings,instrument)
                self.enabledParametersObjects.append(instance)
            except Exception as e:
                pass
        self.selectionChanged.emit( self.enabledParameters )
        self.tableView.selectionModel().currentChanged.connect( self.onActiveInstrumentChanged )
            
    def onAddParameter(self):
        parameter = EnabledParameter()
        parameter.className = str(self.classComboBox.currentText())
        parameter.instrument = str(self.instrumentLineEdit.text())
        parameter.name = str(self.nameLineEdit.text())
        if parameter.name not in self.enabledParameters:
            self.addInstrument(parameter)
        
    def onRemoveParameter(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            self.removeInstrument( self.parameterTableModel.parameterList[index].name )
            
    def addInstrument(self,parameter):
#        try:
        instance = ExternalScannedParameters[parameter.className](parameter.name,parameter.settings,parameter.instrument)
        self.enabledParametersObjects[parameter.name] = instance
        self.enabledParameters[parameter.name] = parameter
        self.selectionChanged.emit( self.enabledParameters )
        self.parameterTableModel.setParameterList( list(self.enabledParameters.values()) )
        self.tableView.resizeColumnsToContents()
#        except Exception as e:
#            print "Initialization of instrument {0} with option '{1}' failed. Exception: {2}".format(parameter.name,parameter.instrument,e)
            
    def removeInstrument(self,name):
        self.enabledParametersObjects.pop( name )
        self.enabledParameters.pop(name)
        self.parameterTableModel.setParameterList( list(self.enabledParameters.values()) )
        self.selectionChanged.emit( self.enabledParameters )
        
    def onActiveInstrumentChanged(self, modelIndex, modelIndex2 ):
        print modelIndex.row()
        self.treeWidget.setParameters( self.enabledParametersObjects[self.parameterTableModel.parameterList[modelIndex.row()].name].parameter )
        
    def onClose(self):
        self.config["ExternalScannedParametersSelection.EnabledParameters"] = self.enabledParameters
        for inst in self.enabledParametersObjects:
            inst.close()
        

if __name__ == "__main__":
    import sys
    import MagnitudeParameter
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = SelectionUi(dict())
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())

