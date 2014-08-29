# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:15:47 2013

@author: pmaunz
"""

import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from externalParameter.ExternalParameterTableModel import ExternalParameterTableModel
from modules.SequenceDict import SequenceDict
from modules.Utility import unique
from uiModules.KeyboardFilter import KeyListFilter
from uiModules.ComboBoxDelegate import ComboBoxDelegate


SelectionForm, SelectionBase = PyQt4.uic.loadUiType(r'ui\ExternalParameterSelection.ui')

class Settings:
    pass

class Parameter:
    def __init__(self):
        self.className = None
        self.name = None
        self.instrument = None
        self.settings = Settings()
        self.enabled = False
        self.plotName = None
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('plotName',None)

class SelectionUi(SelectionForm,SelectionBase):
    selectionChanged = QtCore.pyqtSignal(object)
    
    def __init__(self, config, classdict, instancename="ExternalParameterSelection.ParametersSequence", newDataSlot=None, plotNames=None, parent=None):
        SelectionBase.__init__(self,parent)
        SelectionForm.__init__(self)
        self.config = config
        self.instancename = instancename
        self.parameters = self.config.get(self.instancename,SequenceDict())
        self.plotNames = plotNames
        self.enabledParametersObjects = SequenceDict()
        self.classdict = classdict
        self.newDataSlot = newDataSlot
    
    def setupUi(self,MainWindow):
        logger = logging.getLogger(__name__)
        SelectionForm.setupUi(self,MainWindow)
        self.parameterTableModel = ExternalParameterTableModel( self.parameters, self.plotNames )
        self.parameterTableModel.enableChanged.connect( self.onEnableChanged )
        self.tableView.setModel( self.parameterTableModel )
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)   
        self.delegate = ComboBoxDelegate()
        self.tableView.setItemDelegateForColumn(4, self.delegate )
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown] )
        self.filter.keyPressed.connect( self.onReorder )
        self.tableView.installEventFilter(self.filter)
        self.classComboBox.addItems( self.classdict.keys() )
        self.addParameterButton.clicked.connect( self.onAddParameter )
        self.removeParameterButton.clicked.connect( self.onRemoveParameter )
        for parameter in self.parameters.values():
            if parameter.enabled:
                try:
                    self.enableInstrument(parameter)
                except Exception as e:
                    logger.error( "{0} while enabling instrument {1}".format(e,parameter.name))
                    parameter.enabled = False     
        self.enabledParametersObjects.sortToMatch( self.parameters.keys() )               
        self.selectionChanged.emit( self.enabledParametersObjects )
        self.tableView.selectionModel().currentChanged.connect( self.onActiveInstrumentChanged )

    def onReorder(self, key):
        if key in [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown]:
            indexes = self.tableView.selectedIndexes()
            up = key==QtCore.Qt.Key_PageUp
            delta = -1 if up else 1
            rows = sorted(unique([ i.row() for i in indexes ]),reverse=not up)
            if self.parameterTableModel.moveRow( rows, up=up ):
                selectionModel = self.tableView.selectionModel()
                selectionModel.clearSelection()
                for index in indexes:
                    selectionModel.select( self.parameterTableModel.createIndex(index.row()+delta,index.column()), QtGui.QItemSelectionModel.Select )
            self.enabledParametersObjects.sortToMatch( self.parameters.keys() )               
            self.selectionChanged.emit( self.enabledParametersObjects )

    def onEnableChanged(self, name):
        logger = logging.getLogger(__name__)
        parameter = self.parameters[name]
        if parameter.enabled:
            try:
                self.enableInstrument(parameter)
            except Exception as e:
                logger.exception( "{0} while enabling instrument {1}".format(e,name))
                parameter.enabled = False                    
                self.parameterTableModel.setParameterDict( self.parameters )
        else:
            self.disableInstrument(name)
                      
    def onAddParameter(self):
        parameter = Parameter()
        parameter.instrument = str(self.instrumentLineEdit.text())
        parameter.className = str(self.classComboBox.currentText())
        parameter.name = str(self.nameEdit.currentText())
        if parameter.name not in self.parameters:
            self.parameters[parameter.name] = parameter
            self.parameterTableModel.setParameterDict( self.parameters )
            self.tableView.resizeColumnsToContents()
            self.tableView.horizontalHeader().setStretchLastSection(True)        
        
    def onRemoveParameter(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            parameter = self.parameters.at(index)
            parameter.enabled=False
            self.disableInstrument(parameter.name)
            self.parameters.pop( parameter.name )
        self.parameterTableModel.setParameterDict( self.parameters )
            
    def enableInstrument(self,parameter):
        if parameter.name not in self.enabledParametersObjects:
            logger = logging.getLogger(__name__)
            if self.newDataSlot is None:
                instance = self.classdict[parameter.className](parameter.name,parameter.settings,parameter.instrument)
            else:
                instance = self.classdict[parameter.className](parameter.name,parameter.settings,parameter.instrument, newDataSlot=self.newDataSlot)
            self.enabledParametersObjects[parameter.name] = instance
            self.enabledParametersObjects.sortToMatch( self.parameters.keys() )               
            self.selectionChanged.emit( self.enabledParametersObjects )
            self.parameterTableModel.setParameterDict( self.parameters )
            logger.info("Enabled Instrument {0} as {1}".format(parameter.className,parameter.name))
            
    def disableInstrument(self,name):
        if name in self.enabledParametersObjects:
            logger = logging.getLogger(__name__)
            instance = self.enabledParametersObjects.pop( name )
            instance.close()
            self.enabledParametersObjects.sortToMatch( self.parameters.keys() )               
            self.selectionChanged.emit( self.enabledParametersObjects )
            parameter = self.parameters[name]
            logger.info("Disabled Instrument {0} as {1}".format(parameter.className,parameter.name))
        
    def onActiveInstrumentChanged(self, modelIndex, modelIndex2 ):
        logger = logging.getLogger(__name__)
        logger.debug( "activeInstrumentChanged {0}".format( modelIndex.row() ) )
        if self.parameters.at(modelIndex.row()).enabled:
            self.treeWidget.setParameters( self.enabledParametersObjects[self.parameters.at(modelIndex.row()).name].parameter )
        
    def saveConfig(self):
        self.config[self.instancename] = self.parameters
        
    def onClose(self):
        for inst in self.enabledParametersObjects.values():
            inst.close()
        

if __name__ == "__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = SelectionUi(dict())
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())

