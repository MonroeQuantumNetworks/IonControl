"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtCore, QtGui
from GlobalVariableTableModel import GlobalVariableTableModel
from collections import OrderedDict
from MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
       
Form, Base = PyQt4.uic.loadUiType(r'ui\GlobalVariables.ui')


def unique(seq):
    seen = set()
    return [ x for x in seq if x not in seen and not seen.add(x)]


class GlobalVariables(object):
    def __init__(self):
        self.variabledict = OrderedDict()


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

        
    def onAddVariable(self):
        self.model.addVariable( str(self.newNameEdit.text()))
    
    def onDropVariable(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            name = self.model.dropVariableByIndex(index)
        
    def saveConfig(self):
        self.config[self.configname] = self._variables_

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
        