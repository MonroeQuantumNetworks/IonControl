"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic

from GlobalVariablesModel import GlobalVariablesModel
from modules.Utility import unique
from uiModules.KeyboardFilter import KeyListFilter
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.GuiAppearance import restoreGuiState, saveGuiState   #@UnresolvedImport
from modules.XmlUtilit import xmlEncodeDictionary, xmlParseDictionary, prettify
import xml.etree.ElementTree as ElementTree
from modules import DataDirectory
from externalParameter.persistence import DBPersist
from externalParameter.decimation import StaticDecimation
from modules import magnitude
from modules.magnitude import is_magnitude
from collections import deque
from modules.ListWithKey import ListWithKey, ListWithKeyLookup
import time
import logging
import os

uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\GlobalVariables.ui')
Form, Base = PyQt4.uic.loadUiType(uipath)

class GlobalVariable(QtCore.QObject):
    valueChanged = QtCore.pyqtSignal(object, object, object)
    persistSpace = 'globalVar'
    persistence = DBPersist()

    def __init__(self, name, value=magnitude.mg(0)):
        super(GlobalVariable, self).__init__()
        self.decimation = StaticDecimation(magnitude.mg(10, 's'))
        self.history = deque(maxlen=10)
        self._value = value
        self.name = name
        self.categories = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newvalue):
        if isinstance(newvalue, tuple):
            v, o = newvalue
        else:
            v, o = newvalue, None
        if self._value != v:
            self._value = v
            self.valueChanged.emit(self.name, v, o)
            self.history.appendleft((v, time.time(), o))
            if o is not None:
                self.persistCallback((time.time(), v, None, None))
            else:
                self.decimation.decimate(time.time(), v, self.persistCallback)

    def rename(self, newname):
        self.name, oldname = newname, self.name
        self.persistence.rename(self.persistSpace, oldname, newname)
        return self

    def __getstate__(self):
        return self.name, self._value, self.categories, self.history

    def __setstate__(self, state):
        super(GlobalVariable, self).__init__()
        self.decimation = StaticDecimation(magnitude.mg(10, 's'))
        self.name, self._value, self.categories, self.history = state

    def persistCallback(self, data):
        time, value, minval, maxval = data
        unit = None
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        self.persistence.persist(self.persistSpace, self.name, time, value, minval, maxval, unit)


class GlobalVariablesLookup(ListWithKeyLookup):
    def __init__(self, listWithKey):
        super(GlobalVariablesLookup, self).__init__(listWithKey)

    def __getitem__(self, item):
        return super(GlobalVariablesLookup, self).__getitem__(item).value

    def __setitem__(self, key, value):
        if key in self.listWithKey.lookup:
            super(GlobalVariablesLookup, self).__getitem__(key).value = value
        else:
            super(GlobalVariablesLookup, self).__setitem__(key, GlobalVariable(key, value))

    def valueChanged(self, key):
        return super(GlobalVariablesLookup, self).__getitem__(key).valueChanged


class GlobalVariables(ListWithKey):

    def __init__(self, iterable=[]):
        data = list(iterable)
        if not data or isinstance(data[0], GlobalVariable):
            super(GlobalVariables, self).__init__(data, key=lambda x: x.name, setkey=GlobalVariable.rename)
        else:  # we have old data that needs to be ported
            super(GlobalVariables, self).__init__((GlobalVariable(name, value) for name, value in data), key=lambda x: x.name, setkey=GlobalVariable.rename)
        self.map = GlobalVariablesLookup(self)
            
    def exportXml(self, element):
        xmlEncodeDictionary(self.map, element, "Variable")
    
    @staticmethod
    def fromXmlElement( element ):
        newglobals = GlobalVariables()
        newglobals.map.update(xmlParseDictionary(element, "Variable"))
        return newglobals

    def keyindex(self, key):
        return self.lookup[key]

class GlobalVariableUi(Form, Base ):
    def __init__(self, config, parent=None):
        Form.__init__(self)
        Base.__init__(self, parent)
        self.config = config
        self.configName = 'GlobalVariables'
        self._variables_ = GlobalVariables(self.config.get(self.configName, []))
        self._map = self._variables_.map

    @property
    def valueChanged(self):
        return self.model.valueChanged

    @property
    def variables(self):
        return self._map
    
    def keys(self):
        return self._map.keys()

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.addButton.clicked.connect( self.onAddVariable )
        self.dropButton.clicked.connect( self.view.onDelete )
        self.model = GlobalVariablesModel(self.config, self._variables_)
        self.view.setModel( self.model )
        self.delegate = MagnitudeSpinBoxDelegate()
        self.newNameEdit.returnPressed.connect( self.onAddVariable )
        self.view.setItemDelegateForColumn(self.model.column.value, self.delegate)
        # self.view.setSortingEnabled(True)   # triggers sorting
        # self.model.restoreCustomOrder()          # to restore the last custom order
        # Context Menu
        # self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        # self.restoreCustomOrderAction = QtGui.QAction( "restore custom order" , self)
        # self.restoreCustomOrderAction.triggered.connect( self.model.restoreCustomOrder  )
        # self.addAction( self.restoreCustomOrderAction )
        restoreGuiState( self, self.config.get(self.configName+".guiState") )
#        try:
        self.view.restoreTreeState(self.config.get(self.configName+'.treeState',tuple([None]*4)))
 #       except Exception as e:
  #          logging.getLogger(__name__).error("unable to restore tree state in {0}: {1}".format(self.configName, e))

        self.exportXmlButton.clicked.connect( self.onExportXml )

    def onExportXml(self, element=None, writeToFile=True):
        root = element if element is not None else ElementTree.Element('GlobalVariables')
        self._variables_.exportXml(root)
        if writeToFile:
            filename = DataDirectory.DataDirectory().sequencefile("GlobalVariables.xml")[0]
            with open(filename,'w') as f:
                f.write(prettify(root))
        return root
            
    def onImportXml(self, filename=None, mode="Add"):
        filename = filename if filename is not None else QtGui.QFileDialog.getOpenFileName(self, 'Import XML file', filer="*.xml" )
        tree = ElementTree.parse(filename)
        element = tree.getroot()
        self.importXml(element, mode=mode)
            
    def importXml(self, element, mode="Add"):   # modes: replace, update, Add
        newGlobalDict = GlobalVariables.fromXmlElement(element)
        self.model.beginResetModel()
        if mode == "Replace":
            self._map.clear()
            self._map.update(newGlobalDict.map)
        elif mode == "Update":
            self._map.update(newGlobalDict.map)
        elif mode == "Add":
            newGlobalDict.map.update(self._map)
            self._map.clear()
            self._map.update(newGlobalDict.map)
        self.model.endResetModel()
        
    def onAddVariable(self):
        self.model.addVariable( str(self.newNameEdit.text()))
        self.newNameEdit.setText("")

    def saveConfig(self):
        self.config[self.configName] = list(self._variables_)
        self.config[self.configName+".guiState"] = saveGuiState( self )
        try:
            self.config[self.configName+'.treeState'] = self.treeState()
        except Exception as e:
            logging.getLogger(__name__).error("unable to save tree state in {0}: {1}".format(self.configName, e))

    def update(self, updlist):
        self.model.update(updlist)
        

if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = GlobalVariableUi(config)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
        