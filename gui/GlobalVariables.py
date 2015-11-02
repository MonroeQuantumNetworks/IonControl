"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic

from GlobalVariableTableModel import GlobalVariableTableModel
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
        super(GlobalVariables, self).__init__(iterable, key=lambda x: x.name, setkey=GlobalVariable.rename)
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
        self.configname = 'GlobalVariables-v2'
        self._variables_ = GlobalVariables(self.config.get(self.configname, []))
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
        self.dropButton.clicked.connect( self.onDropVariable )
        self.model = GlobalVariableTableModel(self.config, self._variables_)
        self.tableView.setModel( self.model )
        self.delegate = MagnitudeSpinBoxDelegate()
        self.tableView.setItemDelegateForColumn(1,self.delegate) 
        self.tableView.setSortingEnabled(True)   # triggers sorting
        self.model.restoreCustomOrder()          # to restore the last custom order
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown], [QtCore.Qt.Key_B] )
        self.filter.keyPressed.connect( self.onReorder )
        self.filter.controlKeyPressed.connect( self.onBold )
        self.tableView.installEventFilter(self.filter)
        self.newNameEdit.returnPressed.connect( self.onAddVariable )
        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.restoreCustomOrderAction = QtGui.QAction( "restore custom order" , self)
        self.restoreCustomOrderAction.triggered.connect( self.model.restoreCustomOrder  )
        self.addAction( self.restoreCustomOrderAction )
        restoreGuiState( self, self.config.get(self.configname+".guiState") )
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
    
    def onDropVariable(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            self.model.dropVariableByIndex(index)
        
    def saveConfig(self):
        self.config[self.configname] = list(self._variables_)
        self.config[self.configname+".guiState"] = saveGuiState( self )
        self.model.saveConfig()

    def onReorder(self, key):
        if key in [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown]:
            indexes = self.tableView.selectedIndexes()
            up = key==QtCore.Qt.Key_PageUp
            delta = -1 if up else 1
            rows = sorted(unique([ i.row() for i in indexes ]),reverse=not up)
            if self.model.moveRow( rows, up=up ):
                selectionModel = self.tableView.selectionModel()
                selectionModel.clearSelection()
                for index in indexes:
                    selectionModel.select( self.model.createIndex(index.row()+delta,index.column()), QtGui.QItemSelectionModel.Select )
                    
    def onBold(self, key):
        indexes = self.tableView.selectedIndexes()
        for index in indexes:
            self.model.toggleBold( index )
                    
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
        