# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 22:00:58 2013

@author: pmaunz
"""
from collections import OrderedDict
from functools import partial
from logging import Logger
import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from modules.SequenceDict import SequenceDict
from uiModules.ComboBoxDelegate import ComboBoxDelegate


Form, Base = PyQt4.uic.loadUiType(r'ui\LoggerLevelsUi.ui')

levelNames = OrderedDict([(0,"Not Set"),(10,"Debug"), (20,"Info"), (30,"Warning"), (40,"Error"), (50,"Critical")])
levelNumbers = OrderedDict([(v,k) for k, v in levelNames.items() ])

class LoggerLevelsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, config, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.config = config
        self.levelDict = self.config.get('LoggingLevels',SequenceDict())
        for name, level in self.levelDict.iteritems():
            logger = logging.getLogger(name)
            logger.setLevel(level)
        self.update()
        self.dataLookup =  { (QtCore.Qt.DisplayRole,0): lambda row: self.levelDict.keyAt(row),
                             (QtCore.Qt.DisplayRole,1): lambda row: levelNames[self.levelDict.at(row)],
                             (QtCore.Qt.EditRole,1):    lambda row: levelNames[self.levelDict.at(row)],
                             #(QtCore.Qt.BackgroundColorRole): functools.partial( self.displayDataColor, index),
                             #(QtCore.Qt.ToolTipRole): functools.partial( self.displayToolTip, index )   
                             }
        
    def choice(self, index):
        return levelNumbers.keys()

    def update(self):
        self.beginResetModel()
        for name, logger in Logger.manager.loggerDict.iteritems():  #@UndefinedVariable
            if isinstance(logger,Logger):
                self.levelDict[name] = logger.getEffectiveLevel()
        self.endResetModel()


    def saveConfig(self):
        self.config['LoggingLevels'] = self.levelDict

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.levelDict) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()), lambda row: None)(index.row())
        return None
        
    def setLevel(self, index, value):
        self.levelDict.setAt(index.row(), levelNumbers[value])
        logger = logging.getLogger(self.levelDict.keyAt(index.row()))
        logger.setLevel(levelNumbers[value])
        
    def setData(self, index, value, role):
        return { (QtCore.Qt.EditRole,1): partial( self.setLevel, index, str(value) ),
                }.get((role,index.column()), lambda: False )()
                
    def setValue(self, index, value):
        self.setData( index, value, QtCore.Qt.EditRole)
        
    flagsLookup = [QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
                 QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled]
    def flags(self, index ):
        return  self.flagsLookup[index.column()]

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return ["Logger","Level"][section]
        return None #QtCore.QVariant()

        

class LoggerLevelsUi(Form, Base):
    def __init__(self,config,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.config = config
        self.configname = 'LoggerLevelsUi'
        self.levelsDict = self.config.get( self.configname + '.levels', dict() )
        
    def setupUi(self,parent,dynupdate=False):
        Form.setupUi(self,parent)
        self.tableModel = LoggerLevelsTableModel(self.config)
        self.tableView.setModel(self.tableModel)
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.tableView.setItemDelegateForColumn(1, ComboBoxDelegate() )
        self.tableView.clicked.connect(self.edit )
        self.updateButton.clicked.connect( self.tableModel.update )
        
    def saveConfig(self):
        self.tableModel.saveConfig()
        
    def edit(self, index):
        if index.column() in [1]:
            self.tableView.edit(index)
 
if __name__ == "__main__":
    import sys
    logging.getLogger()
    logging.getLogger("Peter")
    app = QtGui.QApplication(sys.argv)
    config = dict()
    ui = LoggerLevelsUi(config)
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
