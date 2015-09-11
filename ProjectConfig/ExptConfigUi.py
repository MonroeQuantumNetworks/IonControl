"""
Created on 10 Sep 2015 at 11:08 AM

@author: jmizrahi
"""

import os.path
import sys
import logging
from PyQt4 import QtGui, QtCore
import PyQt4.uic
from datetime import datetime
import yaml
from persist.DatabaseConnectionSettings import DatabaseConnectionSettings
from modules.enum import enum
from modules.PyqtUtility import BlockSignals
from functools import partial

uiPath = os.path.join(os.path.dirname(__file__), '..', 'ui/ExptConfig.ui')
Form, Base = PyQt4.uic.loadUiType(uiPath)

hardwareTypes = ['OpalKellyFPGA'] #Categories of hardware which share configuration interfaces
gui = enum('hardware', 'software')


class ExptConfigUi(Base,Form):
    """Class for configuring an experiment"""
    def __init__(self, project):
        Base.__init__(self)
        Form.__init__(self)
        self.project = project
        self.exptConfig = project.exptConfig
        filename = 'ExptConfigGuiTemplate.yml'
        self.widgetDict = dict()
        self.guiTemplateFilename = os.path.join(self.project.mainConfigDir, filename)
        with open(self.guiTemplateFilename, 'r') as f:
            self.guiTemplate = yaml.load(f)
        self.setupUi(self)

    def setupUi(self, parent):
        """setup the dialog box ui"""
        super(ExptConfigUi,self).setupUi(parent)
        self.infoLabel.setText(
            "This dialog box overwrites the experiment configuration file:\n{0}.".format(
                self.project.exptConfigFilename))
        self.defaultCheckBox.setChecked(not self.exptConfig['showGui'])
        self.hardwareComboBox.addItems(self.guiTemplate['knownHardware'].keys())
        self.softwareComboBox.addItems(self.guiTemplate['softwareFeatures'].keys())
        self.guiDict = {gui.hardware: (self.hardwareTabWidget, self.hardwareComboBox, self.hardwareListWidget),
                        gui.software: (self.softwareTabWidget, self.softwareComboBox, self.softwareListWidget)}
        self.addHardwareButton.clicked.connect( partial(self.onAdd, gui.hardware) )
        self.removeHardwareButton.clicked.connect( partial(self.onRemove, gui.hardware) )
        self.hardwareListWidget.currentTextChanged.connect( partial(self.onSelect, gui.hardware) )
        self.hardwareTabWidget.currentChanged.connect( partial(self.onTabWidgetChanged, gui.hardware) )
        self.addSoftwareButton.clicked.connect( partial(self.onAdd, gui.software) )
        self.removeSoftwareButton.clicked.connect( partial(self.onRemove, gui.software) )
        self.softwareListWidget.currentTextChanged.connect( partial(self.onSelect, gui.software) )
        self.softwareTabWidget.currentChanged.connect( partial(self.onTabWidgetChanged, gui.software) )

    def onTabWidgetChanged(self, guiType, index):
        tabWidget,comboBox,listWidget = self.guiDict[guiType]
        item = str(tabWidget.tabText(index))
        listItem = listWidget.findItems(item, QtCore.Qt.MatchExactly)
        if listItem:
            listWidget.setCurrentItem(listItem[0])

    def onSelect(self, guiType, item):
        tabWidget,comboBox,listWidget = self.guiDict[guiType]
        item = str(item)
        widget = self.widgetDict[item]
        index = tabWidget.indexOf(widget)
        tabWidget.setCurrentIndex(index)

    def onAdd(self, guiType):
        tabWidget,comboBox,listWidget = self.guiDict[guiType]
        item = str(comboBox.currentText())
        if item:
            listWidget.addItem(item)
            index=comboBox.findText(item,QtCore.Qt.MatchExactly)
            comboBox.removeItem(index)
            tabWidget.addTab(self.getWidget(item),item)

    def onRemove(self, guiType):
        tabWidget,comboBox,listWidget = self.guiDict[guiType]
        if listWidget.currentItem():
            item = str(listWidget.currentItem().text())
            with BlockSignals(listWidget) as w:
                w.takeItem(w.currentRow())
            tabWidget.removeTab(tabWidget.currentIndex())
            comboBox.addItem(item)

    def getWidget(self, key):
        if key not in self.widgetDict:
             self.widgetDict[key] = QtGui.QWidget() #TODO: make this something real
        return self.widgetDict[key]

    def accept(self):
        """Ok button is clicked. Checks database settings before proceeding."""
        dbConn = DatabaseConnectionSettings(**{'user':str(self.userEdit.text()),
                                             'password':str(self.passwordEdit.text()),
                                             'database':str(self.databaseEdit.text()),
                                             'host':str(self.hostEdit.text()),
                                             'port':str(self.portEdit.text()),
                                             'echo':self.echoCheck.isChecked()
                                             })
        success = self.project.attemptDatabaseConnection(dbConn)
        if not success:
            QtGui.QMessageBox.information(self, 'Database error', 'Invalid database settings')
        else:
            Base.accept(self)

    def reject(self):
        message = "Experiment must be configured for IonControl program to run"
        logging.getLogger(__name__).exception(message)
        sys.exit(message)
