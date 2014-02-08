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


Form, Base = PyQt4.uic.loadUiType(r'ui\GlobalVariables.ui')

class GlobalVariables(object):
    def __init__(self):
        self.variabledict = SequenceDict()

    def __setstate__(self, state):
        self.__dict__ = state
        if not isinstance(self.variabledict,SequenceDict):
            self.variabledict = SequenceDict(self.variabledict)


class GlobalVariableUi(Form, Base ):
    def __init__(self,config,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'GlobalParameters'
        self._variables_ = self.config.get(self.configname,GlobalVariables())

    @property
    def variables(self):
        return self._variables_.variabledict
        
    @property
    def valueChanged(self):
        """PyQt Signal fired when a variable value changed"""
        return self.model.valueChanged

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.addButton.clicked.connect( self.onAddVariable )
        self.dropButton.clicked.connect( self.onDropVariable )
        self.model = GlobalVariableTableModel(self.variables)
        self.tableView.setModel( self.model )
        self.tableView.setItemDelegateForColumn(1,MagnitudeSpinBoxDelegate()) 
        self.tableView.setSortingEnabled(True)
        self.tableView.clicked.connect(self.onViewClicked)
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown] )
        self.filter.keyPressed.connect( self.onReorder )
        self.tableView.installEventFilter(self.filter)

        
    def onAddVariable(self):
        self.model.addVariable( str(self.newNameEdit.text()))
    
    def onDropVariable(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            self.model.dropVariableByIndex(index)
        
    def saveConfig(self):
        self.config[self.configname] = self._variables_

    def onViewClicked(self,index):
        """If one of the editable columns is clicked, begin to edit it."""
        self.tableView.edit(index)

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
        