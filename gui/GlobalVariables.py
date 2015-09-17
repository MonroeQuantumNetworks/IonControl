"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic

from GlobalVariableTableModel import GlobalVariableTableModel
from modules.SequenceDict import SequenceDict
from modules.Utility import unique 
from uiModules.KeyboardFilter import KeyListFilter
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.Observable import Observable
from modules.GuiAppearance import restoreGuiState, saveGuiState   #@UnresolvedImport
from modules.XmlUtilit import xmlEncodeDictionary, xmlParseDictionary, prettify
import xml.etree.ElementTree as ElementTree
from modules import DataDirectory
from externalParameter.persistence import DBPersist
from externalParameter.decimation import StaticDecimation
from modules import magnitude
from modules.magnitude import is_magnitude
from collections import defaultdict
from functools import partial
import time

Form, Base = PyQt4.uic.loadUiType(r'ui\GlobalVariables.ui')

class GlobalVariables(SequenceDict):
    persistSpace = 'globalVar'
    def __init__(self, *args, **kwds):
        self.customOrder = list()
        self.observables = defaultdict( Observable )
        self.decimation = defaultdict(lambda: StaticDecimation(magnitude.mg(10, 's')))
        self.persistence = DBPersist()
        SequenceDict.__init__(self, *args, **kwds)
        pass
            
    def __reduce__(self):
        data = SequenceDict.__reduce__(self)
        data[2].pop('observables')
        data[2].pop('decimation')
        data[2].pop('persistence')
        return data
    
    def exportXml(self, element):
        xmlEncodeDictionary(self, element, "Variable")
    
    @staticmethod
    def fromXmlElement( element ):
        return GlobalVariables( xmlParseDictionary(element, "Variable") )
    
    def __setitem__(self, key, value):
        super( GlobalVariables, self ).__setitem__(key, value)
        self.observables[key].fire(name=key, value=value)
        self.persistCallback(key, (time.time(), value, None, None))
        
    def setItem(self, key, value):
        """set the item, but only commit to database after wait time"""
        self.decimation[key].decimate(time.time(), value, partial(self.persistCallback, key))

    def persistCallback(self, source, data):
        time, value, minval, maxval = data
        unit = None
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        self.persistence.persist(self.persistSpace, source, time, value, minval, maxval, unit)


class GlobalVariableUi(Form, Base ):
    def __init__(self,config,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'GlobalVariables'
        self._variables_ = self.config.get(self.configname,GlobalVariables())

    @property
    def variables(self):
        return self._variables_
    
    def keys(self):
        return self._variables_.keys()
        
        
    @property
    def valueChanged(self):
        """PyQt Signal fired when a variable value changed"""
        return self.model.valueChanged

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.addButton.clicked.connect( self.onAddVariable )
        self.dropButton.clicked.connect( self.onDropVariable )
        self.model = GlobalVariableTableModel(self.config, self.variables)
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
            
    def onImportXml(self, filename=None, mode="addMissing"):
        filename = filename if filename is not None else QtGui.QFileDialog.getOpenFileName(self, 'Import XML file', filer="*.xml" )
        tree = ElementTree.parse(filename)
        element = tree.getroot()
        self.importXml(element, mode=mode)
            
    def importXml(self, element, mode="addMissing"):   # modes: replace, update, addMissing
        newGlobalDict = GlobalVariables.fromXmlElement(element) 
        if mode=="replace":
            self._variables_.clear()
            self._variables_.update( newGlobalDict )
        elif mode=="update":
            self._variables_.update( newGlobalDict )
        elif mode=="addMissing":
            newGlobalDict.update( self._variables_ )
            self._variables_.clear()
            self._variables_.update( newGlobalDict )
        
    def onAddVariable(self):
        self.model.addVariable( str(self.newNameEdit.text()))
        self.newNameEdit.setText("")
    
    def onDropVariable(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            self.model.dropVariableByIndex(index)
        
    def saveConfig(self):
        self.config[self.configname] = self._variables_
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
        