# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtCore, QtGui
import PulseProgram
import VariableTableModel
import ShutterTableModel
import TriggerTableModel
import CounterTableModel
import os.path
from modules import configshelve
from modules import dictutil

PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType('ui/PulseProgram.ui')

class ConfiguredParams:
    lastFilename = None
    recentFiles = dict()

class PulseProgramUi(PulseProgramWidget,PulseProgramBase):
    def __init__(self,config,parameterdict):
        PulseProgramWidget.__init__(self)
        PulseProgramBase.__init__(self)
        self.pulseProgram = PulseProgram.PulseProgram()
        self.sourceCodeEdits = dict()
        self.config = config
        self.parameterdict = parameterdict
        self.variabledict = None
    
    def setupUi(self,experimentname,parent):
        super(PulseProgramUi,self).setupUi(parent)
        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.loadButton.setDefaultAction( self.actionOpen )
        self.saveButton.setDefaultAction( self.actionSave )
        self.resetButton.setDefaultAction( self.actionReset )
        self.checkBoxParameter.stateChanged.connect( self.onVariableSelectionChanged )
        self.checkBoxAddress.stateChanged.connect( self.onVariableSelectionChanged )
        self.checkBoxOther.stateChanged.connect( self.onVariableSelectionChanged )
        self.experimentname = experimentname
        self.configname = 'PulseProgramUi.'+self.experimentname
        self.datashelf = configshelve.configshelve(self.configname)
        self.datashelf.open()
        if self.configname not in self.config:
            self.config[self.configname] = ConfiguredParams()
        self.configParams = self.config[self.configname] 
        if hasattr(self.configParams,'recentFiles'):
            self.filenameComboBox.addItems(self.configParams.recentFiles.keys())
        if self.configParams.lastFilename is not None:
            #print self.configname, self.configParams.lastFilename
            self.loadFile( self.configParams.lastFilename )
        if hasattr(self.configParams,'splitterHorizontal'):
            self.splitterHorizontal.restoreState(self.configParams.splitterHorizontal)
        if hasattr(self.configParams,'splitterVertical'):
            self.splitterVertical.restoreState(self.configParams.splitterVertical)
        self.filenameComboBox.currentIndexChanged[QtCore.QString].connect( self.onFilenameChange )

    def onFilenameChange(self, name ):
        name = str(name)
        if name in self.configParams.recentFiles:
            print "Loading: ", self.configParams.recentFiles[name]
            self.loadFile(self.configParams.recentFiles[name])
        
    def onVariableSelectionChanged(self):
        visibledict = dict()
        for tag in [self.checkBoxParameter,self.checkBoxAddress,self.checkBoxOther]:
            visibledict[str(tag.text())] = tag.isChecked()
        self.variableTableModel.setVisible(visibledict)
        
    def onOk(self):
        pass
    
    def onLoad(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Pulse Programmer file'))
        if path!="":
            self.loadFile(path)
            
    def onReset(self):
        if self.configParams.lastFilename is not None:
            self.variabledict = self.pulseProgram.variabledict.copy()
            self.loadFile(self.configParams.lastFilename)
    
    def loadFile(self, path):
        if self.variabledict is not None and self.configParams.lastFilename is not None:
            self.datashelf[self.configParams.lastFilename] = self.variabledict
        self.configParams.lastFilename = path
        key = self.configParams.lastFilename
        try:
            self.pulseProgram.loadSource(path)
        except PulseProgram.ppexception:
            # compilation failed
            pass
        self.variabledict = self.pulseProgram.variabledict.copy()
        if key in self.datashelf:
            self.variabledict.update( dictutil.subdict(self.datashelf[key], self.variabledict.keys() ) )
        self.updateDisplay()
        filename = os.path.basename(path)
        if filename not in self.configParams.recentFiles:
            self.filenameComboBox.addItem(filename)
        self.configParams.recentFiles[filename]=path
        self.filenameComboBox.setCurrentIndex( self.filenameComboBox.findText(filename))

    def onSave(self):
        self.onApply()
        self.pulseProgram.saveSource()
    
    def onApply(self):
        for name, textEdit in self.sourceCodeEdits.iteritems():
            self.pulseProgram.source[name] = str(textEdit.toPlainText())
        self.pulseProgram.loadFromMemory()
        self.updateDisplay()
    
    def updateDisplay(self):
        self.sourceTabs.clear()
        self.sourceCodeEdits = dict()
        for name, text in self.pulseProgram.source.iteritems():
            textEdit = QtGui.QTextEdit()
            textEdit.setPlainText(text)
            self.sourceCodeEdits[name] = textEdit
            self.sourceTabs.addTab( textEdit, name )
        self.variableTableModel = VariableTableModel.VariableTableModel( self.variabledict, self.parameterdict )
        self.variableView.setModel(self.variableTableModel)
        self.shutterTableModel = ShutterTableModel.ShutterTableModel( self.variabledict )
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)
        self.triggerTableModel = TriggerTableModel.TriggerTableModel( self.variabledict )
        self.triggerTableView.setModel(self.triggerTableModel)
        self.triggerTableView.resizeColumnsToContents()
        self.triggerTableView.clicked.connect(self.triggerTableModel.onClicked)
        self.counterTableModel = CounterTableModel.CounterTableModel( self.variabledict )
        self.counterTableView.setModel(self.counterTableModel)
        self.counterTableView.resizeColumnsToContents()
        self.counterTableView.clicked.connect(self.counterTableModel.onClicked)
                    
    def onAccept(self):
        pass
    
    def onReject(self):
        pass
        
    def close(self):
        if not hasattr(self, 'closed'):
            self.configParams.splitterHorizontal = self.splitterHorizontal.saveState()
            self.configParams.splitterVertical = self.splitterVertical.saveState()
            self.config[self.configname] = self.configParams
            self.datashelf[self.configParams.lastFilename] = self.variabledict
            self.datashelf.close()
            self.closed = True
        else:
            print "called close again on", self.configname
        
    def getPulseProgramBinary(self,parameters=dict()):
        # need to update variables self.pulseProgram.updateVariables( self.)
        substitutes = dict()
        for model in [self.variableTableModel, self.shutterTableModel, self.triggerTableModel, self.counterTableModel]:
            substitutes.update( model.getVariables() )
        self.pulseProgram.updateVariables(substitutes)
        return self.pulseProgram.toBinary()
        
class PulseProgramSetUi(QtGui.QDialog):
    class Parameters:
        pass
    def __init__(self,config):
        super(PulseProgramSetUi,self).__init__()
        self.config = config
        self.pulseProgramSet = dict()        # ExperimentName -> PulseProgramUi
        self.lastExperimentFile = dict()     # ExperimentName -> last pp file used for this experiment
        self.isShown = False
    
    def setupUi(self,parent):
        self.horizontalLayout = QtGui.QHBoxLayout(parent)
        self.tabWidget = QtGui.QTabWidget(parent)
        self.horizontalLayout.addWidget(self.tabWidget)
        self.setWindowTitle('Pulse Program')
        self.setWindowFlags(QtCore.Qt.WindowMinMaxButtonsHint)

    def addExperiment(self, experiment, parameterdict=dict()):
        if not experiment in self.pulseProgramSet:
            programUi = PulseProgramUi(self.config, parameterdict)
            programUi.setupUi(experiment,programUi)
            programUi.myindex = self.tabWidget.addTab(programUi,experiment)
            self.pulseProgramSet[experiment] = programUi
        return self.pulseProgramSet[experiment]
            
    def getPulseProgram(self, experiment):
        return self.pulseProgramSet[experiment]
        
    def accept(self):
        self.config['PulseProgramSetUi.pos'] = self.pos()
        self.config['PulseProgramSetUi.size'] = self.size()
        self.hide()
        self.recipient.onSettingsApply()  
        for page in self.pulseProgramSet.values():
            page.onAccept()
        
    def reject(self):
        self.config['PulseProgramSetUi.pos'] = self.pos()
        self.config['PulseProgramSetUi.size'] = self.size()
        self.hide()
        for page in self.pulseProgramSet.values():
            page.onAccept()
        
    def show(self):
        if 'PulseProgramSetUi.pos' in self.config:
            self.move(self.config['PulseProgramSetUi.pos'])
        if 'PulseProgramSetUi.size' in self.config:
            self.resize(self.config['PulseProgramSetUi.size'])
        QtGui.QDialog.show(self)
        self.isShown = True
        
    def close(self):
        if self.isShown:
            for page in self.pulseProgramSet.values():
                page.close()
            self.reject()

#    def resizeEvent(self, event):
#        self.config['PulseProgramSetUi.size'] = event.size()
#        super(PulseProgramSetUi,self).resizeEvent(event)
#    
#    def moveEvent(self,event):
#        super(PulseProgramSetUi,self).moveEvent(event)
#        self.config['PulseProgramSetUi.pos'] = self.pos()
        
        
    
if __name__ == "__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = PulseProgramSetUi(config)
    ui.setupUi(ui)
    ui.addExperiment("Sequence")
    ui.addExperiment("Doppler Recooling")
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
    print config
