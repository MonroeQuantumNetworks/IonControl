import copy
import logging
import os
import itertools
import yaml

import PyQt4.uic
from PyQt4 import QtGui, QtCore
from pyqtgraph.dockarea import DockArea, Dock

from AWG.AWGChannelUi import AWGChannelUi
from AWG.AWGTableModel import AWGTableModel
from AWG.VarAsOutputChannel import VarAsOutputChannel
from modules.PyqtUtility import BlockSignals
from modules.SequenceDict import SequenceDict
from modules.magnitude import mg
from modules.GuiAppearance import saveGuiState, restoreGuiState
from modules.enum import enum
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from ProjectConfig.Project import getProject

AWGuipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\AWG.ui')
AWGForm, AWGBase = PyQt4.uic.loadUiType(AWGuipath)

class Settings(object):
    """Settings associated with AWGUi. Each entry in the settings menu has a corresponding Settings object.

    Attributes:
       deviceSettings(dict): dynamic settings of the device, controlled by the parameterTree widget. Elements are defined
          in the device's 'paramDef' function
       channelSettingsList (list of dicts): each element corresponds to a channel of the AWG. Each element is a dict,
          with keys that determine the channel's setting (e.g. 'equation' and 'plotEnabled', etc.)
       waveformMode (enum): whether the AWG is programmed in equation mode or segment mode
       filename (str): (segment mode only) the filename from which to save/load AWG segment data
       varDict (SequenceDict): the list of variables which determine the AWG waveform
       saveIfNecessary (function): the AWGUi's function that save's the settings
       replot (function): the AWGUi's function that replots all waveforms

    Note that "deviceProperties" are fixed settings of an AWG device, while "deviceSettings" are settings that can be
    changed on the fly.
    """
    waveformModes = enum('equation', 'segments')
    plotStyles = enum('lines', 'points', 'linespoints')
    saveIfNecessary = None
    replot = None
    deviceProperties = dict()
    stateFields = {'channelSettingsList':list(),
                   'deviceSettings':dict(),
                   'waveformMode':waveformModes.equation,
                   'filename':'',
                   'varDict':SequenceDict()
                   }
    def __init__(self):
        [setattr(self, field, copy.copy(fieldDefault)) for field, fieldDefault in self.stateFields.iteritems()]

    def __setstate__(self, state):
        self.__dict__ = state

    def __eq__(self,other):
        return tuple(getattr(self,field,None) for field in self.stateFields.keys())==tuple(getattr(other,field,None) for field in self.stateFields.keys())

    def __ne__(self, other):
        return not self == other

    def update(self, other):
        [setattr(self, field, getattr(other, field)) for field in self.stateFields.keys() if hasattr(other, field)]


class AWGUi(AWGForm, AWGBase):
    varDictChanged = QtCore.pyqtSignal(object)
    def __init__(self, deviceClass, config, globalDict, parent=None):
        AWGBase.__init__(self, parent)
        AWGForm.__init__(self)
        self.config = config
        self.configname = 'AWGUi.' + deviceClass.displayName
        self.globalDict = globalDict
        self.autoSave = self.config.get(self.configname+'.autoSave', True)
        self.settingsDict = self.config.get(self.configname+'.settingsDict', dict())
        self.settingsName = self.config.get(self.configname+'.settingsName', '')
        self.recentFiles = self.config.get(self.configname+'.recentFiles', dict()) #dict of form {basename: filename}, where filename has path and basename doesn't
        self.lastDir = self.config.get(self.configname+'.lastDir', getProject().configDir)
        Settings.deviceProperties = deviceClass.deviceProperties
        Settings.saveIfNecessary = self.saveIfNecessary
        Settings.replot = self.replot
        for settings in self.settingsDict.values(): #make sure all pickled settings are consistent with device, in case it changed
            for channel in range(deviceClass.deviceProperties['numChannels']):
                if channel >= len(settings.channelSettingsList): #create new channels if it's necessary
                    settings.channelSettingsList.append({
                        'equation' : 'A*sin(w*t+phi) + offset',
                        'segmentList':[],
                        'plotEnabled':True,
                        'plotStyle':Settings.plotStyles.lines})
                else:
                    settings.channelSettingsList[channel].setdefault('equation', 'A*sin(w*t+phi) + offset')
                    settings.channelSettingsList[channel].setdefault('segmentList', [])
                    settings.channelSettingsList[channel].setdefault('plotEnabled', True)
                    settings.channelSettingsList[channel].setdefault('plotStyle', Settings.plotStyles.lines)
        self.settings = Settings() #we always run settings through the constructor
        if self.settingsName in self.settingsDict:
            self.settings.update(self.settingsDict[self.settingsName])
        self.device = deviceClass(self.settings, self.globalDict)

    def setupUi(self,parent):
        logger = logging.getLogger(__name__)
        AWGForm.setupUi(self,parent)
        self.setWindowTitle(self.device.displayName)

        #mode
        self.waveformModeComboBox.setCurrentIndex(self.settings.waveformMode)
        self.waveformModeComboBox.currentIndexChanged[int].connect(self.onWaveformModeChanged)
        equationMode = self.settings.waveformMode==self.settings.waveformModes.equation
        self.fileFrame.setEnabled(not equationMode)
        self.fileFrame.setVisible(not equationMode)

        self._varAsOutputChannelDict = dict()
        self.area = DockArea()
        self.splitter.insertWidget(0, self.area)
        self.awgChannelUiList = []
        for channel in range(self.device.deviceProperties['numChannels']):
            awgChannelUi = AWGChannelUi(channel, self.settings, self.globalDict, parent=self)
            awgChannelUi.setupUi(awgChannelUi)
            awgChannelUi.dependenciesChanged.connect(self.onDependenciesChanged)
            self.awgChannelUiList.append(awgChannelUi)
            dock = Dock("AWG Channel {0}".format(channel))
            dock.addWidget(awgChannelUi)
            self.area.addDock(dock, 'right')
            awgChannelUi.equationFrame.setEnabled(equationMode)
            awgChannelUi.equationFrame.setVisible(equationMode)
            awgChannelUi.addRemoveSegmentFrame.setEnabled(not equationMode)
            awgChannelUi.addRemoveSegmentFrame.setVisible(not equationMode)
            awgChannelUi.segmentView.setEnabled(not equationMode)
            awgChannelUi.segmentView.setVisible(not equationMode)
        self.refreshVarDict()

        # Settings control
        self.saveButton.clicked.connect( self.onSave )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )
        self.settingsModel = QtGui.QStringListModel()
        self.settingsComboBox.setModel(self.settingsModel)
        self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
        self.settingsComboBox.setCurrentIndex( self.settingsComboBox.findText(self.settingsName) )
        self.settingsComboBox.currentIndexChanged[str].connect( self.onLoad )
        self.settingsComboBox.lineEdit().editingFinished.connect( self.onComboBoxEditingFinished )

        #programming options widget
        self.programmingOptionsTreeWidget.setParameters( self.device.parameter() )

        # Table
        self.tableModel = AWGTableModel(self.settings, self.globalDict)
        self.tableView.setModel(self.tableModel)
        self.tableModel.valueChanged.connect(self.onValue)
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(self.tableModel.column.value, self.delegate)

        #File
        self.filenameModel = QtGui.QStringListModel()
        self.filenameComboBox.setModel(self.filenameModel)
        self.filenameModel.setStringList( [basename for basename, filename in self.recentFiles.iteritems() if os.path.exists(filename)] )
        self.filenameComboBox.setCurrentIndex(self.filenameComboBox.findText(os.path.basename(self.settings.filename)))
        self.filenameComboBox.currentIndexChanged[str].connect(self.onFilename)
        self.removeFileButton.clicked.connect(self.onRemoveFile)
        self.newFileButton.clicked.connect(self.onNewFile)
        self.openFileButton.clicked.connect(self.onOpenFile)
        self.saveFileButton.clicked.connect(self.onSaveFile)
        self.reloadFileButton.clicked.connect(self.onReloadFile)

        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.autoSave )
        self.saveButton.setEnabled( not self.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )

        #Restore GUI state
        state = self.config.get(self.configname+'.state')
        pos = self.config.get(self.configname+'.pos')
        size = self.config.get(self.configname+'.size')
        isMaximized = self.config.get(self.configname+'.isMaximized')
        dockAreaState = self.config.get(self.configname+'.dockAreaState')
        guiState = self.config.get(self.configname+".guiState")
        restoreGuiState(self, guiState)
        try:
            if pos:
                self.move(pos)
            if size:
                self.resize(size)
            if isMaximized:
                self.showMaximized()
            if state:
                self.restoreState(state)
            for awgChannelUi in self.awgChannelUiList:
                channelGuiState = self.config[self.configname+"channel{0}.guiState".format(awgChannelUi.channel)]
                restoreGuiState(awgChannelUi, channelGuiState)
        except Exception as e:
            logger.warning("Error on restoring state in AWGUi {0}. Exception occurred: {1}".format(self.device.displayName, e))
        try:
            if dockAreaState:
                self.area.restoreState(dockAreaState)
        except Exception as e:
            logger.warning("Cannot restore dock state in AWGUi {0}. Exception occurred: {1}".format(self.device.displayName, e))
            self.area.deleteLater()
            self.area = DockArea()
            self.splitter.insertWidget(0, self.area)
            for channelUi in self.awgChannelUiList:
                dock = Dock("AWG Channel {0}".format(channel))
                dock.addWidget(channelUi)
                self.area.addDock(dock, 'right')
        self.saveIfNecessary()

    def onComboBoxEditingFinished(self):
        """a settings name is typed into the combo box"""
        currentText = str(self.settingsComboBox.currentText())
        if self.settingsName != currentText:
            self.settingsName = currentText
            if self.settingsName not in self.settingsDict:
                self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
            self.onLoad(self.settingsName)

    def saveIfNecessary(self):
        """save the current settings if autosave is on and something has changed"""
        currentText = str(self.settingsComboBox.currentText())
        if self.settingsDict.get(self.settingsName)!=self.settings or currentText!=self.settingsName:
            if self.autoSave:
                self.onSave()
            else:
                self.saveButton.setEnabled(True)

    def replot(self):
        """plot all channels"""
        for channelUi in self.awgChannelUiList:
            channelUi.replot()

    def onSave(self):
        """save current settings"""
        self.settingsName = str(self.settingsComboBox.currentText())
        self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
        with BlockSignals(self.settingsComboBox) as w:
            self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
            w.setCurrentIndex(w.findText(self.settingsName))
        self.saveButton.setEnabled(False)

    def saveConfig(self):
        """save GUI configuration to config"""
        self.config[self.configname+".guiState"] = saveGuiState(self)
        for awgChannelUi in self.awgChannelUiList:
            self.config[self.configname+"channel{0}.guiState".format(awgChannelUi.channel)] = saveGuiState(awgChannelUi)
        self.config[self.configname+'.state'] = self.saveState()
        self.config[self.configname+'.pos'] = self.pos()
        self.config[self.configname+'.size'] = self.size()
        self.config[self.configname+'.isMaximized'] = self.isMaximized()
        self.config[self.configname+'.isVisible'] = self.isVisible()
        self.config[self.configname+'.dockAreaState'] = self.area.saveState()
        self.config[self.configname+'.settingsDict'] = self.settingsDict
        self.config[self.configname+'.settingsName'] = self.settingsName
        self.config[self.configname+'.autoSave'] = self.autoSave
        self.config[self.configname+'.recentFiles'] = self.recentFiles
        self.config[self.configname+'.lastDir'] = self.lastDir

    def onRemove(self):
        """Remove current settings from combo box"""
        name = str(self.settingsComboBox.currentText())
        if name in self.settingsDict:
            self.settingsDict.pop(name)
            self.settingsName = self.settingsDict.keys()[0] if self.settingsDict else ''
            with BlockSignals(self.settingsComboBox) as w:
                self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
                w.setCurrentIndex(w.findText(self.settingsName))
            self.onLoad(self.settingsName)

    def onReload(self):
        """Reload segment data from file"""
        name = str(self.settingsComboBox.currentText())
        self.onLoad(name)
       
    def onLoad(self, name):
        """load segment data from file"""
        name = str(name)
        if name in self.settingsDict:
            self.settingsName = name
            self.tableModel.beginResetModel()
            [channelUi.segmentModel.beginResetModel() for channelUi in self.awgChannelUiList]
            self.settings.update(self.settingsDict[self.settingsName])
            self.programmingOptionsTreeWidget.setParameters( self.device.parameter() )
            self.saveButton.setEnabled(False)
            with BlockSignals(self.waveformModeComboBox) as w:
                w.setCurrentIndex(self.settings.waveformMode)
            with BlockSignals(self.filenameComboBox) as w:
                w.setCurrentIndex(w.findText(os.path.basename(self.settings.filename)))
            equationMode = self.settings.waveformMode==self.settings.waveformModes.equation
            self.fileFrame.setEnabled(not equationMode)
            self.fileFrame.setVisible(not equationMode)
            for channelUi in self.awgChannelUiList:
                channelUi.equationFrame.setEnabled(equationMode)
                channelUi.equationFrame.setVisible(equationMode)
                channelUi.addRemoveSegmentFrame.setEnabled(not equationMode)
                channelUi.addRemoveSegmentFrame.setVisible(not equationMode)
                channelUi.segmentView.setEnabled(not equationMode)
                channelUi.segmentView.setVisible(not equationMode)
                equation = self.settings.channelSettingsList[channelUi.channel]['equation']
                channelUi.equationEdit.setText(equation)
                channelUi.waveform.updateDependencies()
                channelUi.plotCheckbox.setChecked(self.settings.channelSettingsList[channelUi.channel]['plotEnabled'])
                with BlockSignals(channelUi.styleComboBox) as w:
                    w.setCurrentIndex(self.settings.channelSettingsList[channelUi.channel]['plotStyle'])
                channelUi.replot()
            self.onDependenciesChanged()
            self.saveButton.setEnabled(False)
            self.tableModel.endResetModel()
            [channelUi.segmentModel.endResetModel() for channelUi in self.awgChannelUiList]

    def onAutoSave(self, checked):
        """autosave is changed"""
        self.autoSave = checked
        self.saveButton.setEnabled(not checked)
        if checked:
            self.onSave()

    def onValue(self, var=None, value=None):
        """variable value is changed in the table"""
        self.saveIfNecessary()
        self.replot()

    def evaluate(self, name):
        """re-evaluate the text in the tableModel (happens when a global changes)"""
        self.tableModel.evaluate(name)

    def refreshVarDict(self):
        """refresh the variable dictionary by checking all waveform dependencies"""
        allDependencies = set()
        [channelUi.waveform.updateDependencies() for channelUi in self.awgChannelUiList]
        [allDependencies.update(channelUi.waveform.dependencies) for channelUi in self.awgChannelUiList]
        default = lambda varname:{'value':mg(1, 'us'), 'text':None} if varname.startswith('Duration') else {'value':mg(0), 'text':None}
        deletions = [varname for varname in self.settings.varDict if varname not in allDependencies]
        [self.settings.varDict.pop(varname) for varname in deletions] #remove all values that aren't dependencies anymore
        [self.settings.varDict.setdefault(varname, default(varname)) for varname in allDependencies] #add missing values
        self.settings.varDict.sort(key = lambda val: -1 if val[0].startswith('Duration') else ord( str(val[0])[0] ))
        self.varDictChanged.emit(self.varAsOutputChannelDict)
        for channelUi in self.awgChannelUiList:
            channelUi.replot()

    def onDependenciesChanged(self, channel=None):
        """When dependencies change, refresh all variables"""
        self.tableModel.beginResetModel()
        self.refreshVarDict()
        self.tableModel.endResetModel()
        self.saveIfNecessary()

    def onWaveformModeChanged(self, mode):
        """Waveform mode (equation/segment) changed"""
        self.settings.waveformMode = mode
        equationMode = mode==self.settings.waveformModes.equation
        self.fileFrame.setEnabled(not equationMode)
        self.fileFrame.setVisible(not equationMode)
        for channelUi in self.awgChannelUiList:
            channelUi.equationFrame.setVisible(equationMode)
            channelUi.equationFrame.setEnabled(equationMode)
            channelUi.addRemoveSegmentFrame.setVisible(not equationMode)
            channelUi.addRemoveSegmentFrame.setEnabled(not equationMode)
            channelUi.segmentView.setEnabled(not equationMode)
            channelUi.segmentView.setVisible(not equationMode)
        self.onDependenciesChanged()

    def onFilename(self, basename):
        """filename combo box is changed. Open selected file"""
        basename = str(basename)
        filename = self.recentFiles[basename]
        if os.path.isfile(filename) and filename!=self.settings.filename:
            self.openFile(filename)

    def onRemoveFile(self):
        """Remove file button is clicked. Remove filename from combo box."""
        text = str(self.filenameComboBox.currentText())
        index = self.filenameComboBox.findText(text)
        if text in self.recentFiles:
            self.recentFiles.pop(text)
        with BlockSignals(self.filenameComboBox) as w:
            self.filenameModel.setStringList(self.recentFiles.keys())
            w.setCurrentIndex(-1)
            self.onFilename(w.currentText())

    def onNewFile(self):
        """New button is clicked. Pop up dialog asking for new name, and create file."""
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'New File', self.lastDir,'YAML (*.yml)'))
        if filename:
            self.lastDir, basename = os.path.split(filename)
            self.recentFiles[basename] = filename
            self.settings.filename = filename
            with BlockSignals(self.filenameComboBox) as w:
                self.filenameModel.setStringList(self.recentFiles.keys())
                w.setCurrentIndex(w.findText(basename))
            self.onSaveFile()

    def onOpenFile(self):
        """Open file button is clicked. Pop up dialog asking for filename."""
        filename = str(QtGui.QFileDialog.getOpenFileName(self, 'Select File', self.lastDir,'YAML (*.yml)'))
        if filename:
            self.openFile(filename)

    def openFile(self, filename):
        """Open the file 'filename'"""
        if os.path.exists(filename):
            self.lastDir, basename = os.path.split(filename)
            self.recentFiles[basename] = filename
            self.settings.filename = filename
            with BlockSignals(self.filenameComboBox) as w:
                self.filenameModel.setStringList(self.recentFiles.keys())
                w.setCurrentIndex(w.findText(basename))
            with open(filename, 'r') as f:
                yamldata = yaml.load(f)
            variables = yamldata.get('variables')
            channelData = yamldata.get('channelData')
            self.tableModel.beginResetModel()
            [channelUi.segmentModel.beginResetModel() for channelUi in self.awgChannelUiList]
            if channelData:
                for channel, channelSettings in enumerate(self.settings.channelSettingsList):
                    if channel < len(channelData):
                        channelSettings['segmentList'] = channelData[channel]
            if variables:
                for varname, vardata in variables.iteritems():
                    self.settings.varDict.setdefault(varname, dict())
                    self.settings.varDict[varname]['value'] = mg(vardata['value'], vardata['unit'])
                    self.settings.varDict[varname]['text'] = vardata['text']
            for channelUi in self.awgChannelUiList:
                channelUi.waveform.updateDependencies()
                channelUi.replot()
            self.onDependenciesChanged()
            self.tableModel.endResetModel()
            [channelUi.segmentModel.endResetModel() for channelUi in self.awgChannelUiList]
        else:
            logging.getLogger(__name__).warning("file '{0}' does not exist".format(filename))
            if filename in self.recentFiles:
                del self.recentFiles[filename]
                with BlockSignals(self.filenameComboBox) as w:
                    self.filenameModel.setStringList(self.recentFiles.keys())
                    w.setCurrentIndex(-1)

    def onSaveFile(self):
        """Save button is clicked. Save data to segment file"""
        channelData = [channelSettings['segmentList']
                    for channelSettings in self.settings.channelSettingsList]
        yamldata = {'channelData': channelData}
        variables={varname:
                             {'value':float(varValueTextDict['value'].toStringTuple()[0]),
                              'unit':varValueTextDict['value'].toStringTuple()[1],
                              'text':varValueTextDict['text']}
                         for varname, varValueTextDict in self.settings.varDict.iteritems()}
        yamldata.update({'variables':variables})
        with open(self.settings.filename, 'w') as f:
            yaml.dump(yamldata, f, default_flow_style=False)

    def onReloadFile(self):
        self.openFile(self.settings.filename)

    @QtCore.pyqtProperty(dict)
    def varAsOutputChannelDict(self):
        """dict of output channels, for use in scans"""
        for varname in self.settings.varDict:
            if varname not in self._varAsOutputChannelDict:
                self._varAsOutputChannelDict[varname] = VarAsOutputChannel(self, varname, self.globalDict)
        deletions = [varname for varname in self._varAsOutputChannelDict if varname not in self.settings.varDict]
        [self._varAsOutputChannelDict.pop(varname) for varname in deletions] #remove all values that aren't dependencies anymore
        return self._varAsOutputChannelDict

    def close(self):
        self.saveConfig()
        super(AWGUi, self).close()

if __name__ == '__main__':
    from AWGDevices import DummyAWG
    import sys
    from ProjectConfig.Project import Project
    from persist import configshelve
    from GlobalVariables.GlobalVariable import GlobalVariablesLookup
    app = QtGui.QApplication(sys.argv)
    project = Project()
    guiConfigFile = os.path.join(project.projectDir, '.gui-config\\ExperimentUi.config.db')
    with configshelve.configshelve(guiConfigFile) as config:
        globalDict = GlobalVariablesLookup(config.get('GlobalVariables', dict()))
        ui = AWGUi(DummyAWG, config, globalDict)
        ui.setupUi(ui)
        ui.show()
        sys.exit(app.exec_())