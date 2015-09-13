"""
Created on 10 Sep 2015 at 11:08 AM

@author: jmizrahi
"""

import os.path
import sys
import logging
from PyQt4 import QtGui, QtCore
import PyQt4.uic
import Experiment_rc
from datetime import datetime
import yaml
from persist.DatabaseConnectionSettings import DatabaseConnectionSettings
from modules.enum import enum
from modules.PyqtUtility import BlockSignals
from functools import partial

uiPath = os.path.join(os.path.dirname(__file__), '..', 'ui/ExptConfig.ui')
Form, Base = PyQt4.uic.loadUiType(uiPath)

gui = enum('hardware', 'software') #two parts of the gui

class ExptConfigUi(Base,Form):
    """Class for configuring an experiment"""
    updateRoles = QtCore.pyqtSignal()
    def __init__(self, project):
        Base.__init__(self)
        Form.__init__(self)
        self.project = project
        self.exptConfig = project.exptConfig
        filename = 'ExptConfigGuiTemplate.yml' #template for creating GUI
        self.widgetDict = dict() #key: tuple (guiType, name). val: widget for configuring that name
        self.subwidgetDict = dict() #key: tuple (guiType, name). val: list of subwidget for configuring that name
        self.roleDict = dict() #key: a role (i.e. voltages, pulser, etc.). val: a list of hardware that can fulfill that role
        self.guiTemplateFilename = os.path.join(self.project.mainConfigDir, filename)
        with open(self.guiTemplateFilename, 'r') as f:
            self.guiTemplate = yaml.load(f)
        self.setupUi(self)

    def setupUi(self, parent):
        """setup the dialog box ui"""
        super(ExptConfigUi,self).setupUi(parent)
        self.infoLabel.setText(
            "Experiment configuration for project {0}.\n\nThis dialog box overwrites the experiment configuration file:\n{1}.".format(
                self.project.name, self.project.exptConfigFilename))
        self.defaultCheckBox.setChecked(not self.exptConfig['showGui'])
        self.hardwareComboBox.addItems(self.guiTemplate['hardware'].keys())
        self.softwareComboBox.addItems(self.guiTemplate['software'].keys())
        self.userEdit.setText(self.exptConfig['databaseConnection'].get('user',''))
        self.passwordEdit.setText(self.exptConfig['databaseConnection'].get('password',''))
        self.databaseEdit.setText(self.exptConfig['databaseConnection'].get('database',''))
        self.hostEdit.setText(self.exptConfig['databaseConnection'].get('host','localhost'))
        self.portEdit.setValue(self.exptConfig['databaseConnection'].get('port',5432))
        self.echoCheck.setChecked(self.exptConfig['databaseConnection'].get('echo',False))

        self.guiDict = {gui.hardware: ('hardware', self.hardwareTabWidget, self.hardwareComboBox, self.hardwareListWidget),
                        gui.software: ('software', self.softwareTabWidget, self.softwareComboBox, self.softwareListWidget)}
        for guiType in [gui.hardware, gui.software]:
            guiName,_,_,_ = self.guiDict[guiType]
            for name in self.exptConfig[guiName]:
                self.addName(guiType, name)

        self.addHardwareButton.clicked.connect( partial(self.onAdd, gui.hardware) )
        self.removeHardwareButton.clicked.connect( partial(self.onRemove, gui.hardware) )
        self.hardwareListWidget.currentTextChanged.connect( partial(self.onSelect, gui.hardware) )
        self.hardwareTabWidget.currentChanged.connect( partial(self.onTabWidgetChanged, gui.hardware) )
        self.addSoftwareButton.clicked.connect( partial(self.onAdd, gui.software) )
        self.removeSoftwareButton.clicked.connect( partial(self.onRemove, gui.software) )
        self.softwareListWidget.currentTextChanged.connect( partial(self.onSelect, gui.software) )
        self.softwareTabWidget.currentChanged.connect( partial(self.onTabWidgetChanged, gui.software) )

    def onTabWidgetChanged(self, guiType, index):
        """Tab widget is clicked. Change the selection in the list widget."""
        guiName,tabWidget,comboBox,listWidget = self.guiDict[guiType]
        name = str(tabWidget.tabText(index))
        item = listWidget.findItems(name, QtCore.Qt.MatchExactly)[0]
        with BlockSignals(listWidget) as w:
            w.setCurrentItem(item)

    def onSelect(self, guiType, name):
        """List widget is clicked. Change the current tab on the tab widget."""
        guiName,tabWidget,comboBox,listWidget = self.guiDict[guiType]
        name = str(name)
        widget = self.widgetDict[(guiType,name)]
        index = tabWidget.indexOf(widget)
        with BlockSignals(tabWidget) as w:
            w.setCurrentIndex(index)

    def onAdd(self, guiType):
        """Add is clicked. Add the name to the list widget, remove it from the combo box, and add the appropriate tab to the tab widget."""
        guiName,tabWidget,comboBox,listWidget = self.guiDict[guiType]
        name = str(comboBox.currentText())
        self.addName(guiType, name)

    def addName(self, guiType, name):
        guiName,tabWidget,comboBox,listWidget = self.guiDict[guiType]
        if name:
            with BlockSignals(listWidget) as w:
                item=QtGui.QListWidgetItem(name,w)
                w.setCurrentItem(item)
            with BlockSignals(tabWidget) as w:
                widget=self.getWidget(guiType,name)
                w.addTab(widget,name)
                w.setCurrentIndex(w.indexOf(widget))
            index=comboBox.findText(name,QtCore.Qt.MatchExactly)
            comboBox.removeItem(index)

    def onRemove(self, guiType):
        """Remove is clicked. Remove it from the list widget, remove it from the tab widget, and add it back to the combo box."""
        guiName,tabWidget,comboBox,listWidget = self.guiDict[guiType]
        if listWidget.currentItem():
            name = str(listWidget.currentItem().text())
            with BlockSignals(listWidget) as w:
                w.takeItem(w.currentRow())
            with BlockSignals(tabWidget) as w:
                widget = self.widgetDict[(guiType,name)]
                w.removeTab(w.indexOf(widget))
            comboBox.addItem(name)
            templateDict= self.guiTemplate[guiName][name]
            role = templateDict.get('role') if templateDict else None
            if role:
                self.roleDict[role].remove(name)
            self.updateRoles.emit()

    def getWidget(self, guiType, name):
        """Get the widget associated with the given name."""
        guiName,tabWidget,comboBox,listWidget = self.guiDict[guiType]
        configDict=self.guiTemplate[guiName][name]
        fields = configDict.get('fields') if configDict else None
        role = configDict.get('role') if configDict else None
        if (guiType,name) not in self.widgetDict:
            self.subwidgetDict[(guiType,name)] = []
            mainwidget = QtGui.QWidget()
            layout = QtGui.QFormLayout(mainwidget)
            if configDict and fields:
                for fieldname, fieldtype in fields.iteritems():
                    try:
                        oldvalue = self.exptConfig[guiName][name][fieldname]
                    except KeyError:
                        oldvalue = None
                    subwidget=configWidget(self,fieldtype,name,oldvalue,parent=mainwidget)
                    self.subwidgetDict[(guiType,name)].append((fieldname,subwidget))
                    layout.addRow(fieldname, subwidget.widget)
            else:
                layout.addRow('No configuration data for this selection', QtGui.QWidget())
            self.widgetDict[(guiType,name)] = mainwidget
        if role:
            if self.roleDict.get(role):
                self.roleDict[role].append(name)
            else:
                self.roleDict[role]=[name]
            self.updateRoles.emit()
        return self.widgetDict[(guiType,name)]

    def accept(self):
        """Ok button is clicked. Checks database settings before proceeding."""
        dbSettings = {'user':str(self.userEdit.text()),
                      'password':str(self.passwordEdit.text()),
                      'database':str(self.databaseEdit.text()),
                      'host':str(self.hostEdit.text()),
                      'port':self.portEdit.value(),
                      'echo':self.echoCheck.isChecked()
                      }
        dbConn = DatabaseConnectionSettings(**dbSettings)
        success = self.project.attemptDatabaseConnection(dbConn)
        if not success:
            QtGui.QMessageBox.information(self, 'Database error', 'Invalid database settings')
        else:
            self.exptConfig=dict()
            self.exptConfig['hardware']=dict()
            self.exptConfig['software']=dict()
            for (guiType,name), subwidgetList in self.subwidgetDict.iteritems():
                guiname=self.guiDict[guiType][0] #'hardware' or 'software'
                if name in self.addedNames(guiType):
                    self.exptConfig[guiname][name]=dict() #name of piece of equipment
                    for fieldname,subwidget in subwidgetList: #fieldname is the specific config field for 'name'
                        self.exptConfig[guiname][name][fieldname] = subwidget.content
            self.exptConfig['databaseConnection'] = dbSettings
            self.exptConfig['showGui']=not self.defaultCheckBox.isChecked()
            Base.accept(self)

    def reject(self):
        """Cancel or close is clicked. Shut down the program."""
        message = "Experiment must be configured for IonControl program to run"
        logging.getLogger(__name__).exception(message)
        sys.exit(message)

    def addedNames(self, guiType):
        """return the names that have been added to the list of hardware or software"""
        listWidget = self.guiDict[guiType][3]
        names = []
        for index in xrange(listWidget.count()):
             names.append(str(listWidget.item(index).text()))
        return names


class configWidget(object):
    def __init__(self,exptConfigUi,fieldtype,role,oldvalue,parent=None):
        self.fieldtype = fieldtype
        self.widgetCall = {'bool' :QtGui.QCheckBox,
                           'float':QtGui.QDoubleSpinBox,
                           'int'  :QtGui.QSpinBox,
                           'role' :partial(RoleWidget,role,exptConfigUi),
                           'path' :partial(PathWidget,exptConfigUi.project.baseDir),
                           'str'  :QtGui.QLineEdit
                          }.get(self.fieldtype)
        if not self.widgetCall:
            self.widget=QtGui.QLabel('error: unknown type',parent=parent)
            self.widget.setStyleSheet("QLabel {color: red;}")
        else:
            self.widget=self.widgetCall(parent=parent)
        if oldvalue:
            if self.fieldtype=='bool':
                self.widget.setChecked(oldvalue)
            elif self.fieldtype=='float':
                self.widget.setValue(oldvalue)
            elif self.fieldtype=='int':
                self.widget.setValue(oldvalue)
            elif self.fieldtype=='role':
                index=self.widget.findText(oldvalue, QtCore.Qt.MatchExactly)
                self.widget.setCurrentIndex(index)
            elif self.fieldtype=='path':
                self.widget.lineEdit.setText(oldvalue)
            elif self.fieldtype=='str':
                self.widget.setText(oldvalue)

    @property
    def content(self):
        if self.fieldtype=='bool':
            return self.widget.isChecked()
        elif self.fieldtype=='float':
            return self.widget.value()
        elif self.fieldtype=='int':
            return self.widget.value()
        elif self.fieldtype=='role':
            return str(self.widget.currentText())
        elif self.fieldtype=='path':
            return str(self.widget.lineEdit.text())
        elif self.fieldtype=='str':
            return str(self.widget.text())


class PathWidget(QtGui.QHBoxLayout):
    def __init__(self,baseDir,parent=None):
        super(PathWidget, self).__init__()
        self.lineEdit=QtGui.QLineEdit(parent)
        self.lineEdit.setReadOnly(True)
        self.openButton=QtGui.QPushButton(parent)
        icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(":/openicon/icons/document-open-5.png")
        icon.addPixmap(pixmap)
        self.openButton.setIcon(icon)
        self.addWidget(self.lineEdit)
        self.addWidget(self.openButton)
        self.openButton.clicked.connect(self.onOpen)
        self.baseDir=baseDir
        self.parent=parent

    def onOpen(self):
        filename = str(QtGui.QFileDialog.getOpenFileName(self.parent, 'Select File',self.baseDir,'All files (*.*)'))
        if filename:
            self.lineEdit.setText(filename)


class RoleWidget(QtGui.QComboBox):
    """Combo box for selecting what hardware to use for a specific software role"""
    def __init__(self,role,exptConfigUi,parent=None):
        super(RoleWidget, self).__init__()
        self.role = role
        self.exptConfigUi = exptConfigUi
        self.onUpdate()
        self.exptConfigUi.updateRoles.connect(self.onUpdate)

    def onUpdate(self):
        currentText=self.currentText()
        self.clear()
        self.addItem('')
        hardwareList = self.exptConfigUi.roleDict.get(self.role)
        if hardwareList:
            self.addItems(hardwareList)
        self.setCurrentIndex( self.findText(currentText,QtCore.Qt.MatchExactly) )