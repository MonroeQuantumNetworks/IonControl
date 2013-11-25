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
from modules.PyqtUtility import updateComboBoxItems
import functools
import logging

def unique(seq):
    seen = set()
    return [ x for x in seq if x not in seen and not seen.add(x)]

class Settings:
    pass

class Parameter:
    def __init__(self):
        self.className = None
        self.name = None
        self.instrument = None
        self.settings = Settings()
        self.enabled = False
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('enabled', False)        

class SelectionUi(SelectionForm,SelectionBase):
    selectionChanged = QtCore.pyqtSignal(object)
    
    def __init__(self, config, parent=None):
        SelectionBase.__init__(self,parent)
        SelectionForm.__init__(self)
        self.config = config
        self.parameters = self.config.get("ExternalScannedParametersSelection.Parameters",dict())
        self.enabledParametersObjects = dict()
    
    def setupUi(self,MainWindow):
        logger = logging.getLogger(__name__)
        SelectionForm.setupUi(self,MainWindow)
        self.parameterTableModel = ExternalParameterTableModel( list(self.parameters.values()) )
        self.parameterTableModel.enableChanged.connect( self.onEnableChanged )
        self.tableView.setModel( self.parameterTableModel )
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)        
        self.classComboBox.addItems( ExternalScannedParameters.keys() )
        self.addParameterButton.clicked.connect( self.onAddParameter )
        self.removeParameterButton.clicked.connect( self.onRemoveParameter )
        for parameter in self.parameters.values():
            if parameter.enabled:
                try:
                    self.enableInstrument(parameter)
                except Exception as e:
                    logger.error( "{0} while enabling instrument {1}".format(e,parameter.name))
                    parameter.enabled = False                    
        self.selectionChanged.emit( self.enabledParametersObjects )
        self.tableView.selectionModel().currentChanged.connect( self.onActiveInstrumentChanged )

    def onEnableChanged(self, name):
        logger = logging.getLogger(__name__)
        parameter = self.parameters[name]
        if parameter.enabled:
            try:
                self.enableInstrument(parameter)
            except Exception as e:
                logger.exception( "{0} while enabling instrument {1}".format(e,name))
                parameter.enabled = False                    
                self.parameterTableModel.setParameterList( list(self.parameters.values()) )
        else:
            self.disableInstrument(name)
                      
    def onAddParameter(self):
        logger = logging.getLogger(__name__)
        name = str(self.nameEdit.currentText())
        parameter = Parameter()
        parameter.instrument = str(self.instrumentLineEdit.text())
        parameter.className = str(self.classComboBox.currentText())
        parameter.name = str(self.nameEdit.currentText())
        if parameter.name not in self.parameters:
            self.parameters[parameter.name] = parameter
            self.parameterTableModel.setParameterList( list(self.parameters.values()) )
            self.tableView.resizeColumnsToContents()
            self.tableView.horizontalHeader().setStretchLastSection(True)        
        
    def onRemoveParameter(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            parameter = self.parameterTableModel.parameterList[index]
            parameter.enabled=False
            self.disableInstrument(parameter.name)
            self.parameters.pop( parameter.name )
        self.parameterTableModel.setParameterList( list(self.parameters.values()) )
            
    def enableInstrument(self,parameter):
        if parameter.name not in self.enabledParametersObjects:
            logger = logging.getLogger(__name__)
            instance = ExternalScannedParameters[parameter.className](parameter.name,parameter.settings,parameter.instrument)
            self.enabledParametersObjects[parameter.name] = instance
            self.selectionChanged.emit( self.enabledParametersObjects )
            self.parameterTableModel.setParameterList( list(self.parameters.values()) )
            logger.info("Enabled Instrument {0} as {1}".format(parameter.className,parameter.name))
            
    def disableInstrument(self,name):
        if name in self.enabledParametersObjects:
            logger = logging.getLogger(__name__)
            self.enabledParametersObjects.pop( name )
            self.selectionChanged.emit( self.enabledParametersObjects )
            parameter = self.parameters[name]
            logger.info("Disabled Instrument {0} as {1}".format(parameter.className,parameter.name))
        
    def onActiveInstrumentChanged(self, modelIndex, modelIndex2 ):
        logger = logging.getLogger(__name__)
        logger.debug( "activeInstrumentChanged {0}".format( modelIndex.row() ) )
        if self.parameterTableModel.parameterList[modelIndex.row()].enabled:
            self.treeWidget.setParameters( self.enabledParametersObjects[self.parameterTableModel.parameterList[modelIndex.row()].name].parameter )
        
    def saveConfig(self):
        self.config["ExternalScannedParametersSelection.Parameters"] = self.parameters
        
    def onClose(self):
        for inst in self.enabledParametersObjects.values():
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

