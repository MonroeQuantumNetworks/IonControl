import copy
import logging
import os
import itertools

import PyQt4.uic
from PyQt4 import QtGui, QtCore
from pyqtgraph.dockarea import DockArea, Dock

from AWG.AWGChannelUi import AWGChannelUi
from AWG.AWGTableModel import AWGTableModel
from AWG.VarAsOutputChannel import VarAsOutputChannel
from modules.PyqtUtility import BlockSignals
from modules.SequenceDict import SequenceDict
from modules.magnitude import mg
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate

AWGuipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\AWG.ui')
AWGForm, AWGBase = PyQt4.uic.loadUiType(AWGuipath)

class Settings(object):
    """Settings associated with AWGUi. Each entry in the settings menu has a corresponding Settings object.

    Attributes:
       deviceSettings(dict): dynamic settings of the device, controlled by the parameterTree widget. Elements are defined
          in the device's 'paramDef' function
       channelSettingsList (list of dicts): each element corresponds to a channel of the AWG. Each element is a dict,
          with keys 'equation' and 'plotEnabled'
    """
    saveIfNecessary = None
    stateFields = {'channelSettingsList':list(),
                   'deviceSettings':dict(),
                   'deviceProperties':dict(),
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
        Settings.saveIfNecessary = self.saveIfNecessary
        self.settings = Settings() #we always run settings through the constructor
        if self.settingsName in self.settingsDict:
            self.settings.update(self.settingsDict[self.settingsName])
        self.settings.deviceProperties = deviceClass.deviceProperties
        self.device = deviceClass(self.settings, self.globalDict)

    def setupUi(self,parent):
        logger = logging.getLogger(__name__)
        AWGForm.setupUi(self,parent)
        self.setWindowTitle(self.device.displayName)

        self._varAsOutputChannelDict = dict()
        self.area = DockArea()
        self.splitter.insertWidget(0, self.area)
        self.awgChannelUiList = []
        for channel in range(self.device.deviceProperties['numChannels']):
            awgChannelUi = AWGChannelUi(channel, self.settings, parent=self)
            awgChannelUi.setupUi(awgChannelUi)
            awgChannelUi.dependenciesChanged.connect(self.onDependenciesChanged)
            self.awgChannelUiList.append(awgChannelUi)
            dock = Dock("AWG Channel {0}".format(channel))
            dock.addWidget(awgChannelUi)
            self.area.addDock(dock, 'right')
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

        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.autoSave )
        self.saveButton.setEnabled( not self.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )

        #Restore GUI state
        dockAreaState = self.config.get(self.configname+'.dockAreaState')
        mainWindowState = self.config.get(self.configname+'.mainWindowState')
        splitterState = self.config.get(self.configname+'.splitterState')
        try:
            if mainWindowState:
                self.restoreState(mainWindowState)
            if splitterState:
                self.splitter.restoreState(splitterState)
            if dockAreaState:
                self.area.restoreState(dockAreaState)
        except Exception as e:
            logger.warning("Error on restoring GUI state in AWGUi {0}: {1}".format(self.device.displayName, e))

        self.saveIfNecessary()

    def onComboBoxEditingFinished(self):
        self.settingsName = str(self.settingsComboBox.currentText())
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

    def onSave(self):
        self.settingsName = str(self.settingsComboBox.currentText())
        self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
        with BlockSignals(self.settingsComboBox) as w:
            self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
            w.setCurrentIndex(w.findText(self.settingsName))
        self.saveButton.setEnabled(False)

    def saveConfig(self):
        self.config[self.configname+'.mainWindowState'] = self.saveState()
        self.config[self.configname+'.dockAreaState'] = self.area.saveState()
        self.config[self.configname+'.splitterState'] = self.splitter.saveState()
        self.config[self.configname+'.settingsDict'] = self.settingsDict
        self.config[self.configname+'.settingsName'] = self.settingsName
        self.config[self.configname+'.autoSave'] = self.autoSave

    def onRemove(self):
        name = str(self.settingsComboBox.currentText())
        if name in self.settingsDict:
            self.settingsDict.pop(name)
            if self.settingsDict:
                self.settingsName = self.settingsDict.keys()[0]
                self.onLoad(self.settingsName)
            else:
                self.settingsName = ''
            with BlockSignals(self.settingsComboBox) as w:
                self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
                w.setCurrentIndex(w.findText(self.settingsName))

    def onReload(self):
        name = str(self.settingsComboBox.currentText())
        self.onLoad(name)
       
    def onLoad(self, name):
        name = str(name)
        if name in self.settingsDict:
            self.settingsName = name
            self.tableModel.beginResetModel()
            self.settings.update(self.settingsDict[self.settingsName])
            self.tableModel.endResetModel()
            self.programmingOptionsTreeWidget.setParameters( self.device.parameter() )
            self.saveButton.setEnabled(False)
            for channelUi in self.awgChannelUiList:
                equation = self.settings.channelSettingsList[channelUi.channel]['equation']
                channelUi.equationEdit.setText(equation)
                channelUi.equation = equation
                channelUi.plotCheckbox.setChecked(self.settings.channelSettingsList[channelUi.channel]['plotEnabled'])
                channelUi.replot()
            self.saveButton.setEnabled(False)

    def onAutoSave(self, checked):
        self.autoSave = checked
        self.saveButton.setEnabled(not checked)
        if checked:
            self.onSave()

    def onValue(self, var=None, value=None):
        self.saveIfNecessary()
        for channelUi in self.awgChannelUiList:
            channelUi.replot()
        
    def evaluate(self, name):
        self.tableModel.evaluate(name)

    def refreshVarDict(self):
        allDependencies = set()
        [allDependencies.update(channelUi.waveform.dependencies) for channelUi in self.awgChannelUiList]
        default = lambda varname:{'value':mg(1, 'us'), 'text':None} if varname.startswith('Duration') else {'value':mg(0), 'text':None}
        deletions = [varname for varname in self.settings.varDict if varname not in allDependencies]
        [self.settings.varDict.pop(varname) for varname in deletions] #remove all values that aren't dependencies anymore
        [self.settings.varDict.setdefault(varname, default(varname)) for varname in allDependencies] #add missing values
        self.settings.varDict.sort(key = lambda val: -1 if val[0].startswith('Duration') else ord( str(val[0])[0] ))
        self.varDictChanged.emit(self.varAsOutputChannelDict)
        for channelUi in self.awgChannelUiList:
            channelUi.replot()

    def onDependenciesChanged(self, channel):
        self.tableModel.beginResetModel()
        self.refreshVarDict()
        self.tableModel.endResetModel()
        self.saveIfNecessary()

    @QtCore.pyqtProperty(dict)
    def varAsOutputChannelDict(self):
        for name in self.settings.varDict:
            if name not in self._varAsOutputChannelDict:
                self._varAsOutputChannelDict[name] = VarAsOutputChannel(self, name, self.globalDict)
        return self._varAsOutputChannelDict

    def close(self):
        self.saveConfig()
        super(AWGUi, self).close()

if __name__ == '__main__':
    from AWGDevices import DummyAWG
    import sys
    from ProjectConfig.Project import Project
    from persist import configshelve
    app = QtGui.QApplication(sys.argv)
    project = Project()
    guiConfigFile = os.path.join(project.projectDir, '.gui-config\\ExperimentUi.config.db')
    with configshelve.configshelve(project.guiConfigFile) as config:
        ui = AWGUi(DummyAWG, config, dict())
        ui.setupUi(ui)
        ui.show()
        sys.exit(app.exec_())