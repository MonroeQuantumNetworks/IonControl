'''
Created on Dec 19, 2014

@author: pmaunz
'''
import PyQt4.uic
import logging
from modules.SequenceDict import SequenceDict

ControlForm, ControlBase = PyQt4.uic.loadUiType(r'ui\AnalysisControl.ui')

class AnalysisDefinitionElement(object):
    def __init__(self):
        self.evaluation = None
        self.analysis = None
        self.pushVariables = tuple()
        
    def __setstate__(self, state):
        self.__dict__ = state
        
    stateFields = ['evaluation', 'analysis', 'pushVariables'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))

class AnalysisControl(ControlForm, ControlBase ):
    def __init__(self, config, globalDict, parentname, parent=None, analysisNames=None):
        ControlForm.__init__(self)
        ControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'AnalysisControl.'+parentname
        self.globalDict = globalDict
        # History and Dictionary
        try:
            self.settingsDict = self.config.get(self.configname+'.dict',dict())
        except TypeError:
            logging.getLogger(__name__).info( "Unable to read scan control settings dictionary. Setting to empty dictionary." )
            self.analysisDefinitionDict = dict()
        self.evaluationConfigurationChanged.emit( self.settingsDict )
        try:
            self.analysisDefinition = self.config.get(self.configname,SequenceDict())
        except TypeError:
            logging.getLogger(__name__).info( "Unable to read scan control settings. Setting to new scan." )
            self.analysisDefinition = SequenceDict()
        self.analysisName = self.config.get(self.configname+'.settingsName',None)
        
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
        self.analysisTableView.
        
        self.removeButton.clicked.connect( self.onRemove )
        self.evalTableModel = EvaluationTableModel( self.checkSettingsSavable, plotnames=self.plotnames, analysisNames=self.analysisNames )
        self.evalTableModel.dataChanged.connect( self.checkSettingsSavable )
        self.evalTableModel.dataChanged.connect( self.onActiveEvalChanged )
        self.evalTableView.setModel( self.evalTableModel )
        self.evalTableView.clicked.connect( self.editEvaluationTable )
        self.delegate = ComboBoxDelegate()
        self.evalTableView.setItemDelegateForColumn(1, self.delegate )
        self.evalTableView.setItemDelegateForColumn(4, self.delegate )
        self.evalTableView.setItemDelegateForColumn(5, self.delegate )        
        self.addEvaluationButton.clicked.connect( self.onAddEvaluation )
        self.removeEvaluationButton.clicked.connect( self.onRemoveEvaluation )
        self.evalTableView.selectionModel().currentChanged.connect( self.onActiveEvalChanged )
        self.evalTableView.resizeColumnsToContents()
       
#        try:
        self.setSettings( self.settings )
#         except AttributeError:
#             logger.error( "Ignoring exception" )
        self.comboBox.addItems( sorted(self.settingsDict.keys()))
        if self.settingsName and self.comboBox.findText(self.settingsName):
            self.comboBox.setCurrentIndex( self.comboBox.findText(self.settingsName) )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        self.comboBox.lineEdit().editingFinished.connect( self.checkSettingsSavable ) 
        # Evaluation
        self.histogramBinsBox.valueChanged.connect(self.onHistogramBinsChanged)
        self.integrateHistogramCheckBox.stateChanged.connect( self.onIntegrateHistogramClicked )
                
        # Timestamps
        self.binwidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'binwidth') )
        self.roiStartSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiStart') )
        self.roiWidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiWidth') )
        self.enableCheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'enableTimestamps' ) )
        self.saveRawDataCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'saveRawData' ) )
        self.integrateCombo.currentIndexChanged[int].connect( self.onIntegrationChanged )
        self.channelSpinBox.valueChanged.connect( functools.partial(self.onBareValueChanged, 'timestampsChannel') )
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        
    def onAutoSave(self, checked):
        self.parameters.autoSave = checked
        if self.parameters.autoSave:
            self.onSave()     
                
    def setAnalysisNames(self, names):
        self.evalTableModel.setAnalysisNames(names)
        
    def setSettings(self, settings):
        self.settings = copy.deepcopy(settings)
        # Evaluation
        self.histogramBinsBox.setValue(self.settings.histogramBins)
        self.integrateHistogramCheckBox.setChecked( self.settings.integrateHistogram )
        # Timestamps
        self.enableCheckBox.setChecked(self.settings.enableTimestamps )
        self.saveRawDataCheckBox.setChecked(self.settings.saveRawData)
        self.binwidthSpinBox.setValue(self.settings.binwidth)
        self.roiStartSpinBox.setValue(self.settings.roiStart)
        self.roiWidthSpinBox.setValue(self.settings.roiWidth)
        self.integrateCombo.setCurrentIndex( self.settings.integrateTimestamps )
        self.channelSpinBox.setValue( self.settings.timestampsChannel )
        self.checkSettingsSavable()
        self.evalAlgorithmList = []
        for evaluation in self.settings.evalList:
            self.addEvaluation(evaluation)
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.evalTableView.resizeColumnsToContents()

    def addEvaluation(self, evaluation):
        algo =  EvaluationAlgorithms[evaluation.evaluation]()
        algo.subscribe( self.checkSettingsSavable )   # track changes of the algorithms settings so the save status is displayed correctly
        algo.setSettings( evaluation.settings, evaluation.name )
        self.evalAlgorithmList.append(algo)      

    def onAddEvaluation(self):
        evaluation = EvaluationDefinition()
        evaluation.counter = 0
        evaluation.plotname = "Scan Data" #Default to "Scan Data" plot
        evaluation.evaluation = EvaluationAlgorithms.keys()[0]
        self.settings.evalList.append( evaluation )
        self.addEvaluation( evaluation )
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.evalTableView.resizeColumnsToContents()
        self.evalTableView.horizontalHeader().setStretchLastSection(True)
        self.checkSettingsSavable()
 
    def removeEvaluation(self, index):
        del self.evalAlgorithmList[index]

    def onRemoveEvaluation(self):
        for index in sorted(unique([ i.row() for i in self.evalTableView.selectedIndexes() ]),reverse=True):
            del self.settings.evalList[index]
            self.removeEvaluation(index)
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.checkSettingsSavable()
        
    def onActiveEvalChanged(self, modelIndex, modelIndex2 ):
        self.evalParamTreeWidget.setParameters( self.evalAlgorithmList[modelIndex.row()].parameter)

    def checkSettingsSavable(self, savable=None):
        if not isinstance(savable, bool):
            currentText = str(self.comboBox.currentText())
            try:
                if currentText is None or currentText=="":
                    savable = False
                elif self.settingsName and self.settingsName in self.settingsDict:
                    savable = self.settingsDict[self.settingsName]!=self.settings or currentText!=self.settingsName
                else:
                    savable = True
                if self.parameters.autoSave and savable:
                    self.onSave()
                    savable = False
            except MagnitudeError:
                pass
        self.saveButton.setEnabled( savable )
            
    def onStateChanged(self, attribute, state):
        setattr( self.settings, attribute, (state == QtCore.Qt.Checked)  )
        self.checkSettingsSavable()
        
    def onValueChanged(self, attribute, value):
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )
        self.checkSettingsSavable()

    def onBareValueChanged(self, attribute, value):
        setattr( self.settings, attribute, value )
        self.checkSettingsSavable()
              
    def getEvaluation(self):
        evaluation = copy.deepcopy(self.settings)
        evaluation.evalAlgorithmList = copy.deepcopy( self.evalAlgorithmList )
        evaluation.settingsName = self.settingsName
        return evaluation
        
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.config[self.configname+'.dict'] = self.settingsDict
        self.config[self.configname+'.settingsName'] = self.settingsName
        self.config[self.configname+'.parameters'] = self.parameters
    
    def onSave(self):
        self.settingsName = str(self.comboBox.currentText())
        if self.settingsName != '':
            if self.settingsName not in self.settingsDict:
                if self.comboBox.findText(self.settingsName)==-1:
                    self.comboBox.addItem(self.settingsName)
            self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
            self.evaluationConfigurationChanged.emit( self.settingsDict )
        self.checkSettingsSavable(False)
        
    def onRemove(self):
        name = str(self.comboBox.currentText())
        if name != '':
            if name in self.settingsDict:
                self.settingsDict.pop(name)
            idx = self.comboBox.findText(name)
            if idx>=0:
                self.comboBox.removeItem(idx)
            self.evaluationConfigurationChanged.emit( self.settingsDict )
       
    def onLoad(self,name):
        self.settingsName = str(name)
        if self.settingsName !='' and self.settingsName in self.settingsDict:
            self.setSettings(self.settingsDict[self.settingsName])
        self.checkSettingsSavable()

    def loadSetting(self, name):
        if name and self.comboBox.findText(name)>=0:
            self.comboBox.setCurrentIndex( self.comboBox.findText(name) )  
            self.onLoad(name)      

    def onReload(self):
        self.onLoad( self.comboBox.currentText() )
   
    def onIntegrationChanged(self, value):
        self.settings.integrateTimestamps = value
        self.checkSettingsSavable()
        
    def onAlgorithmValueChanged(self, algo, name, value):
        self.checkSettingsSavable()

    def onIntegrateHistogramClicked(self, state):
        self.settings.integrateHistogram = self.integrateHistogramCheckBox.isChecked()
        self.checkSettingsSavable()
 
    def onHistogramBinsChanged(self, bins):
        self.settings.histogramBins = bins
        self.checkSettingsSavable()
        
    def onAlgorithmNameChanged(self, name):
        self.checkSettingsSavable()
        
    def editEvaluationTable(self, index):
        if index.column() in [0,1,2,4]:
            self.evalTableView.edit(index)
            
if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = EvaluationControl(config,"parent")
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())

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

