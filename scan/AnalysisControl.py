'''
Created on Dec 19, 2014

@author: pmaunz
'''
import PyQt4.uic
import logging
from modules.SequenceDict import SequenceDict
from scan.AnalysisTableModel import AnalysisTableModel
from modules.GuiAppearance import saveGuiState, restoreGuiState
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from fit.FitFunctionBase import PushVariable
from modules.Utility import unique
import copy
from PyQt4 import QtCore
from scan.PushVariableTableModel import PushVariableTableModel
from scan.DatabasePushDestination import DatabasePushDestination

ControlForm, ControlBase = PyQt4.uic.loadUiType(r'..\ui\AnalysisControl.ui')

class AnalysisDefinitionElement(object):
    def __init__(self):
        self.enabled = True
        self.evaluation = None
        self.analysis = None
        self.pushVariables = tuple()
        
    def __setstate__(self, state):
        self.__dict__ = state
        
    stateFields = ['enabled', 'evaluation', 'analysis', 'pushVariables'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))

class AnalysisControl(ControlForm, ControlBase ):
    def __init__(self, config, globalDict, parentname, parent=None):
        ControlForm.__init__(self)
        ControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'AnalysisControl.'+parentname
        self.globalDict = globalDict
        # History and Dictionary
        try:
            self.analysisDefinitionDict = self.config.get(self.configname+'.dict',dict())
        except TypeError:
            logging.getLogger(__name__).info( "Unable to read scan control settings dictionary. Setting to empty dictionary." )
            self.analysisDefinitionDict = dict()
        try:
            self.analysisDefinition = self.config.get(self.configname,SequenceDict())
        except TypeError:
            logging.getLogger(__name__).info( "Unable to read scan control settings. Setting to new scan." )
            self.analysisDefinition = SequenceDict()
        self.pushDestinations = dict()
        self.currentAnalysisName =  self.config.get(self.configname+'.settingsName',None)
        
    def setupUi(self, parent):
        ControlForm.setupUi(self,parent)
        # History and Dictionary
        self.removeAnalysisConfigurationButton.clicked.connect( self.onRemoveAnalysis )
        self.saveButton.clicked.connect( self.onSave )
        self.reloadButton.clicked.connect( self.onReload )
        self.addAnalysisButton.clicked.connect( self.onAddAnalysis )
        self.removeAnalysisButton.clicked.connect( self.onRemoveAnalysis )
        self.addPushButton.clicked.connect( self.onAddPushVariable )
        self.removePushButton.clicked.connect( self.onRemovePushVariable )
        self.pushButton.clicked.connect( self.onPush )
        self.analysisTableModel = AnalysisTableModel(self.config, self.globalDict)
        self.analysisTableView.setModel( self.analysisTableModel )
        self.analysisTableView.selectionModel().currentChanged.connect( self.onActiveAnalysisChanged )
        self.pushTableModel = PushVariableTableModel(self.config, self.globalDict)
        self.pushTableView.setModel( self.pushTableModel )
        self.pushItemDelegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.pushComboDelegate = ComboBoxDelegate()
        self.pushTableView.setItemDelegateForColumn(1,self.pushComboDelegate)
        self.pushTableView.setItemDelegateForColumn(2,self.pushComboDelegate)
        self.pushTableView.setItemDelegateForColumn(3,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(4,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(5,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(6,self.pushItemDelegate)
        self.pushDestinations['Database'] = DatabasePushDestination('fit')

        self.analysisConfigurationComboBox.addItems( self.analysisDefinitionDict.keys() )
        if self.currentAnalysisName in self.analysisDefinitionDict:
            self.analysisConfigurationComboBox.setCurrentIndex( self.analysisConfigurationComboBox.findText(self.currentAnalysisName))
        else:
            self.currentAnalysisName = str( self.analysisConfigurationComboBox.currentText() )
        self.analysisConfigurationComboBox.currentIndexChanged[QtCore.QString].connect( self.onLoadAnalysisConfiguration )
        restoreGuiState( self, self.config.get(self.configname+'.guiState') )
        self.config[self.configname+'.guiState'] = saveGuiState(self)
            
    def onActiveAnalysisChanged(self):
        pass
            
    def onRemoveAnalysis(self):
        pass
    
    def onAddAnalysis(self):
        pass
        
    def onAddPushVariable(self):
        self.pushTableModel.addVariable( PushVariable() )
    
    def onRemovePushVariable(self):
        for index in sorted(unique([ i.row() for i in self.pushTableView.selectedIndexes() ]),reverse=True):
            self.pushTableModel.removeVariable(index)
        self.fitfunction.updatePushVariables( self.globalDict )
        self.pushTableModel.setFitfunction(self.fitfunction)

    def addPushDestination(self, name, destination ):
        self.pushDestinations[name] = destination
        self.pushTableModel.updateDestinations(self.pushDestinations )

    def onPush(self):
        for destination, variable, value in self.fitfunction.pushVariableValues(self.globalDict):
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )
                
    def pushVariables(self, pushVariables):
        for destination, variable, value in pushVariables:
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )

    def onAutoSave(self, checked):
        self.parameters.autoSave = checked
        if self.parameters.autoSave:
            self.onSave()     
                
    def saveConfig(self):
        self.config[self.configname+'.dict'] = self.analysisDefinitionDict
        self.config[self.configname] = self.analysisDefinition
        self.config[self.configname+'.settingsName'] = self.currentAnalysisName
        self.config[self.configname+'.guiState'] = saveGuiState( self )
    
    def onSave(self):
        self.currentAnalysisName = str(self.analysisConfigurationComboBox.currentText())
        if self.currentAnalysisName != '':
            if self.currentAnalysisName not in self.analysisDefinitionDict:
                if self.analysisConfigurationComboBox.findText(self.currentAnalysisName)==-1:
                    self.analysisConfigurationComboBox.addItem(self.currentAnalysisName)
            self.analysisDefinitionDict[self.currentAnalysisName] = copy.deepcopy(self.analysisDefinition)
        
    def onRemove(self):
        name = str(self.analysisConfigurationComboBox.currentText())
        if name != '':
            if name in self.analysisDefinitionDict:
                self.analysisDefinitionDict.pop(name)
            idx = self.analysisConfigurationComboBox.findText(name)
            if idx>=0:
                self.analysisConfigurationComboBox.removeItem(idx)
       
    def onLoadAnalysisConfiguration(self,name):
        name = str(name)
        if name and name in self.analysisDefinitionDict:
            self.currentAnalysisName = name
            self.setAnalysisDefinition( self.analysisDefinitionDict )

    def setAnalysisDefinition(self, analysisDef ):
        self.analysisDefinition = copy.deepcopy(analysisDef)

    def onReload(self):
        self.onLoadAnalysisConfiguration( self.analysisConfigurationComboBox.currentText() )
   
             
if __name__=="__main__":
    import sys
    from PyQt4 import QtGui
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = AnalysisControl(config,dict(),"parent")
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())



