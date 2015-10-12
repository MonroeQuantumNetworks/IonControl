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
from modules.PyqtUtility import BlockSignals, textSize
from functools import partial

uiPath = os.path.join(os.path.dirname(__file__), '..', 'ui/ExptConfig.ui')
Form, Base = PyQt4.uic.loadUiType(uiPath)

class ExptConfigUi(Base,Form):
    """Class for configuring an experiment"""
    updateRoles = QtCore.pyqtSignal()
    def __init__(self, project):
        Base.__init__(self)
        Form.__init__(self)
        self.project = project
        self.exptConfig = project.exptConfig
        filename = 'ExptConfigGuiTemplate.yml' #template for creating GUI
        self.widgetDict = dict() #key: tuple (guiName, name). val: widget for configuring that name
        self.subwidgetDict = dict() #key: tuple (guiName, name). val: list of subwidget for configuring that name
        self.roleDict = dict() #key: a role (i.e. voltages, pulser, etc.). val: a list of hardware that can fulfill that role
        self.guiTemplateFilename = os.path.join(self.project.mainConfigDir, filename)
        with open(self.guiTemplateFilename, 'r') as f:
            self.guiTemplate = yaml.load(f)
        self.setupUi(self)

    def setupUi(self, parent):
        """setup the dialog box ui"""
        super(ExptConfigUi,self).setupUi(parent)
        self.infoLabel.setText(
            'Experiment configuration for project: <b>{0}</b><br><br>This dialog box overwrites the experiment configuration file:<br>{1}.'.format(
                self.project.name, self.project.exptConfigFilename))
        self.defaultCheckBox.setChecked(not self.exptConfig['showGui'])
        self.hardwareComboBox.addItems(self.guiTemplate['hardware'].keys())
        self.softwareComboBox.addItems(self.guiTemplate['software'].keys())
        self.userEdit.setText(self.exptConfig['databaseConnection'].get('user','python'))
        self.passwordEdit.setText(self.exptConfig['databaseConnection'].get('password',''))
        self.databaseEdit.setText(self.exptConfig['databaseConnection'].get('database','postgres'))
        self.hostEdit.setText(self.exptConfig['databaseConnection'].get('host','localhost'))
        self.portEdit.setValue(self.exptConfig['databaseConnection'].get('port',5432))
        self.echoCheck.setChecked(self.exptConfig['databaseConnection'].get('echo',False))

        self.guiDict = {'hardware': (self.hardwareTabWidget, self.hardwareComboBox, self.hardwareListWidget),
                        'software': (self.softwareTabWidget, self.softwareComboBox, self.softwareListWidget)}
        for guiName in self.guiDict:
            for name in self.exptConfig[guiName]:
                self.addName(guiName, name)

        self.addHardwareButton.clicked.connect( partial(self.onAdd, 'hardware') )
        self.removeHardwareButton.clicked.connect( partial(self.onRemove, 'hardware') )
        self.hardwareListWidget.currentTextChanged.connect( partial(self.onSelect, 'hardware') )
        self.hardwareTabWidget.currentChanged.connect( partial(self.onTabWidgetChanged, 'hardware') )
        self.addSoftwareButton.clicked.connect( partial(self.onAdd, 'software') )
        self.removeSoftwareButton.clicked.connect( partial(self.onRemove, 'software') )
        self.softwareListWidget.currentTextChanged.connect( partial(self.onSelect, 'software') )
        self.softwareTabWidget.currentChanged.connect( partial(self.onTabWidgetChanged, 'software') )

    def onTabWidgetChanged(self, guiName, index):
        """Tab widget is clicked. Change the selection in the list widget."""
        tabWidget,comboBox,listWidget = self.guiDict[guiName]
        name = str(tabWidget.tabText(index))
        item = listWidget.findItems(name, QtCore.Qt.MatchExactly)[0]
        with BlockSignals(listWidget) as w:
            w.setCurrentItem(item)

    def onSelect(self, guiName, name):
        """List widget is clicked. Change the current tab on the tab widget."""
        tabWidget,comboBox,listWidget = self.guiDict[guiName]
        name = str(name)
        widget = self.widgetDict[(guiName,name)]
        index = tabWidget.indexOf(widget)
        with BlockSignals(tabWidget) as w:
            w.setCurrentIndex(index)

    def onAdd(self, guiName):
        """Add is clicked."""
        tabWidget,comboBox,listWidget = self.guiDict[guiName]
        name = str(comboBox.currentText())
        self.addName(guiName, name)

    def addName(self, guiName, name):
        """Add the name to the list widget, remove it from the combo box, and add the appropriate tab to the tab widget."""
        tabWidget,comboBox,listWidget = self.guiDict[guiName]
        if name and name in self.guiTemplate[guiName]:
            templateDict = self.guiTemplate[guiName][name]
            description = templateDict.get('description') if templateDict else None
            with BlockSignals(listWidget) as w:
                item=QtGui.QListWidgetItem(name,w)
                if description:
                    item.setToolTip(description)
                    if self.exptConfig[guiName].has_key(name):
                        if self.exptConfig[guiName][name].has_key('enabled'):
                            checkState = QtCore.Qt.Checked if self.exptConfig[guiName][name]['enabled'] else QtCore.Qt.Unchecked
                        else:
                            checkState = QtCore.Qt.Checked
                    else:
                        checkState = QtCore.Qt.Checked
                    item.setCheckState(checkState)
                w.setCurrentItem(item)
            with BlockSignals(tabWidget) as w:
                widget=self.getWidget(guiName,name)
                w.addTab(widget,name)
                index=w.indexOf(widget)
                if description:
                    w.setTabToolTip(index,description)
                w.setCurrentIndex(index)
            index=comboBox.findText(name,QtCore.Qt.MatchExactly)
            comboBox.removeItem(index)

    def onRemove(self, guiName):
        """Remove is clicked. Remove it from the list widget, remove it from the tab widget, and add it back to the combo box."""
        tabWidget,comboBox,listWidget = self.guiDict[guiName]
        if listWidget.currentItem():
            name = str(listWidget.currentItem().text())
            with BlockSignals(listWidget) as w:
                w.takeItem(w.currentRow())
            with BlockSignals(tabWidget) as w:
                widget = self.widgetDict[(guiName,name)]
                w.removeTab(w.indexOf(widget))
            comboBox.addItem(name)
            templateDict = self.guiTemplate[guiName][name]
            role = templateDict.get('role') if templateDict else None
            if role:
                self.roleDict[role].remove(name)
            self.updateRoles.emit()

    def getWidget(self, guiName, name):
        """Get the widget associated with the given name."""
        templateDict = self.guiTemplate[guiName][name]
        fields = templateDict.get('fields') if templateDict else None
        role = templateDict.get('role') if templateDict else None

        if (guiName,name) not in self.widgetDict:
            self.subwidgetDict[(guiName,name)] = []
            mainwidget = QtGui.QWidget()
            layout = QtGui.QFormLayout(mainwidget)
            if templateDict and fields:
                for fieldname, fieldtype in fields.iteritems():
                    try:
                        oldvalue = self.exptConfig[guiName][name][fieldname]
                    except KeyError:
                        oldvalue = None
                    subwidget=ConfigWidget(self,fieldtype,name,oldvalue,self.subwidgetDict,parent=mainwidget)
                    self.subwidgetDict[(guiName,name)].append((fieldname,subwidget))
                    layout.addRow(fieldname, subwidget.widget)
            else:
                layout.addRow('No configuration data for this selection', None)
            self.widgetDict[(guiName,name)] = mainwidget
        if role:
            if self.roleDict.get(role):
                self.roleDict[role].append(name)
            else:
                self.roleDict[role]=[name]
            self.updateRoles.emit()
        return self.widgetDict[(guiName,name)]

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
            for (guiName,name), subwidgetList in self.subwidgetDict.iteritems():
                if name in self.addedNames(guiName):
                    self.exptConfig[guiName][name]=dict() #'name' is name of piece of equipment or software feature
                    for field,subwidget in subwidgetList: #'field' is the specific config field for 'name'
                        self.exptConfig[guiName][name][field] = subwidget.content
                    listWidget=self.guiDict[guiName][2]
                    item = listWidget.findItems(name, QtCore.Qt.MatchExactly)[0]
                    self.exptConfig[guiName][name]['enabled'] = item.checkState()==QtCore.Qt.Checked
            self.exptConfig['databaseConnection'] = dbSettings
            self.exptConfig['showGui']=not self.defaultCheckBox.isChecked()
            Base.accept(self)

    def reject(self):
        """Cancel or close is clicked. Shut down the program."""
        message = "Experiment must be configured for IonControl program to run"
        logging.getLogger(__name__).error(message)
        sys.exit(message)

    def addedNames(self, guiName):
        """return the names that have been added to the list of hardware or software"""
        tabWidget,comboBox,listWidget = self.guiDict[guiName]
        names = []
        for index in xrange(listWidget.count()):
             names.append(str(listWidget.item(index).text()))
        return names


class ConfigWidget(object):
    """Class for arbitrary config widget"""
    def __init__(self,exptConfigUi,fieldtype,name,oldvalue,subwidgetDict,parent=None):
        """Creates a widget of the specified fieldtype"""
        self.fieldtype = fieldtype

        self.widgetCallLookup = {'bool'   : QtGui.QCheckBox,
                                 'float'  : QtGui.QDoubleSpinBox,
                                 'int'    : QtGui.QSpinBox,
                                 'role'   : partial(RoleWidget,name,exptConfigUi),
                                 'path'   : partial(PathWidget,exptConfigUi.project.baseDir),
                                 'str'    : QtGui.QLineEdit,
                                 'ok_fpga': partial(OK_FPGA_Widget,subwidgetDict,name)}

        widgetCall = self.widgetCallLookup.get(self.fieldtype)
        if not widgetCall:
            self.widget = QtGui.QLabel('error: unknown type',parent=parent)
            self.widget.setStyleSheet("QLabel {color: red;}")
        else:
            self.widget = widgetCall(parent=parent)

        self.widgetSetLookup = {'bool'   : getattr(self.widget, 'setChecked', None),
                                'float'  : getattr(self.widget, 'setValue', None),
                                'int'    : getattr(self.widget, 'setValue', None),
                                'role'   : getattr(self.widget, 'setToText', None),
                                'path'   : getattr(self.widget, 'setText', None),
                                'str'    : getattr(self.widget, 'setText', None),
                                'ok_fpga': getattr(self.widget, 'setToText', None)}

        if oldvalue:
            try:
                self.widgetSetLookup.get(self.fieldtype)(oldvalue)
            except Exception:
                pass

    @property
    def content(self):
        if   self.fieldtype=='bool':    return self.widget.isChecked()
        elif self.fieldtype=='float':   return self.widget.value()
        elif self.fieldtype=='int':     return self.widget.value()
        elif self.fieldtype=='role':    return str(self.widget.currentText())
        elif self.fieldtype=='path':    return str(self.widget.lineEdit.text())
        elif self.fieldtype=='str':     return str(self.widget.text())
        elif self.fieldtype=='ok_fpga': return str(self.widget.identifierComboBox.currentText())


class PathWidget(QtGui.QHBoxLayout):
    """Config widget for selecting files"""
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

    @QtCore.pyqtSlot()
    def onOpen(self):
        filename = str(QtGui.QFileDialog.getOpenFileName(self.parent, 'Select File',self.baseDir,'All files (*.*)'))
        if filename:
            self.lineEdit.setText(filename)

    def setText(self,text):
        self.lineEdit.setText(text)


class RoleWidget(QtGui.QComboBox):
    """Combo box for selecting what hardware to use for a specific software role"""
    def __init__(self,name,exptConfigUi,parent=None):
        super(RoleWidget, self).__init__()
        self.name = name
        self.exptConfigUi = exptConfigUi
        self.onUpdate()
        self.exptConfigUi.updateRoles.connect(self.onUpdate)

    @QtCore.pyqtSlot()
    def onUpdate(self):
        """Update the list of possible hardware to use for this role"""
        currentText=self.currentText()
        self.clear()
        self.addItem('')
        hardwareList = self.exptConfigUi.roleDict.get(self.name)
        if hardwareList:
            self.addItems(hardwareList)
        self.setCurrentIndex( self.findText(currentText,QtCore.Qt.MatchExactly) )

    def setToText(self, text):
        """Set widget to particular text"""
        index=self.findText(text, QtCore.Qt.MatchExactly)
        self.setCurrentIndex(index)


class OK_FPGA_Widget(QtGui.QHBoxLayout):
    """Config widget for selecting an Opal Kelly FPGA"""
    def __init__(self,subwidgetDict,name,parent=None):
        super(OK_FPGA_Widget, self).__init__()
        from pulser.OKBase import OKBase
        self.pulser = OKBase()
        self.subwidgetDict = subwidgetDict
        self.name = name
        self.identifierComboBox = QtGui.QComboBox(parent)
        self.modelLineEdit = QtGui.QLineEdit(parent)
        self.modelLineEdit.setReadOnly(True)
        self.modelLineEdit.setFixedWidth(120)
        self.uploadButton = QtGui.QPushButton('Upload', parent)
        self.uploadButton.setFixedWidth(60)
        self.uploadButton.setToolTip("Upload bitfile to FPGA")
        self.uploadButton.clicked.connect(self.onUpload)
        self.scanButton = QtGui.QPushButton('Scan', parent)
        self.scanButton.setFixedWidth(60)
        self.scanButton.setToolTip("Scan for FPGAs")
        self.scanButton.clicked.connect(self.onScan)
        self.addWidget(self.identifierComboBox)
        self.addWidget(self.modelLineEdit)
        self.addWidget(self.uploadButton)
        self.addWidget(self.scanButton)
        self.OK_FPGA_Dict=dict()
        self.FPGAlistModel=QtGui.QStringListModel()
        self.identifierComboBox.setModel(self.FPGAlistModel)
        self.identifierComboBox.currentIndexChanged[str].connect(self.onChanged)
        self.onScan()

    @QtCore.pyqtSlot()
    def onScan(self):
        """Get list of FPGAs"""
        logger = logging.getLogger(__name__)
        currentText = self.identifierComboBox.currentText()
        self.OK_FPGA_Dict = self.pulser.listBoards()
        logger.info( "Opal Kelly Devices found: {0}".format({k:v.modelName for k,v in self.OK_FPGA_Dict.iteritems()}) )
        self.OK_FPGA_Dict.update({'':'dummy'})
        self.FPGAlistModel.setStringList(self.OK_FPGA_Dict.keys())
        self.setToText(currentText)

    @QtCore.pyqtSlot()
    def onUpload(self):
        """upload bitFile to FPGA"""
        logger = logging.getLogger(__name__)
        subwidgets = self.subwidgetDict[('hardware',self.name)]
        FPGA_name = str(self.identifierComboBox.currentText())
        FPGA = self.OK_FPGA_Dict[FPGA_name]
        bitFileFound=False
        for fieldName,widget in subwidgets:
            if fieldName=='bitFile':
                bitFileFound=True
                bitFile=widget.content
        if not bitFileFound:
            logger.error("No bitfile field found; unable to upload bitfile")
        elif not os.path.exists(bitFile):
            logger.error("Invalid bitfile path")
        elif not FPGA_name:
            logger.error("No FPGA selected")
        else:
            self.pulser.openBySerial(FPGA.serial)
            self.pulser.uploadBitfile(bitFile)
            logger.info("Uploaded file {0} to {1} (model {2})".format(bitFile, FPGA_name, FPGA.modelName))

    @QtCore.pyqtSlot(str)
    def onChanged(self, name):
        """set modelLineEdit to display FPGA model name"""
        name = str(name)
        modelName=self.OK_FPGA_Dict.get(name).modelName if name else ''
        self.modelLineEdit.setText(modelName)

    def setToText(self, text):
        """Set widget to particular device id text"""
        index=self.identifierComboBox.findText(text, QtCore.Qt.MatchExactly)
        self.currentText=text if index >=0 else ''
        self.identifierComboBox.setCurrentIndex(index)