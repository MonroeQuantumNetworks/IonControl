# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 22:00:58 2013

@author: pmaunz
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic
from modules import configshelve
import logging
from ComboBoxDelegate import ComboBoxDelegate
from functools import partial
from collections import OrderedDict

Form, Base = PyQt4.uic.loadUiType(r'ui\LoggerLevelsUi.ui')

levelNames = OrderedDict([(0,"Not Set"),(10,"Debug"), (20,"Info"), (30,"Warning"), (40,"Error"), (50,"Critical")])
levelNumbers = OrderedDict([(v,k) for k, v in levelNames.items() ])

class LoggerLevelsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, config, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.config = config
        self.levelDict = self.config.get('LoggingLevelDict',dict())
        for name, level in self.levelDict.iteritems():
            logger = logging.getLogger(name)
            logger.setLevel(level)
        self.levelList = list(self.levelDict.iteritems())
        self.update()
        
    def choice(self, index):
        return levelNumbers.keys()

    def update(self):
        self.beginResetModel()
        for name, logger in logging.Logger.manager.loggerDict.iteritems():
            if isinstance(logger,logging.Logger):
                self.levelDict[name] = logger.getEffectiveLevel()
        self.levelList = list(self.levelDict.iteritems())
        self.endResetModel()


    def saveConfig(self):
        self.config['LoggingLevelDict'] = self.levelDict

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.levelList) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,0): self.levelList[index.row()][0],
                     (QtCore.Qt.DisplayRole,1): levelNames[self.levelList[index.row()][1]],
                     (QtCore.Qt.EditRole,1): levelNames[self.levelList[index.row()][1]],
                     #(QtCore.Qt.BackgroundColorRole): functools.partial( self.displayDataColor, index),
                     #(QtCore.Qt.ToolTipRole): functools.partial( self.displayToolTip, index )
                     }.get((role,index.column()),None)
        return None
        
    def setLevel(self, index, value):
        self.levelList[index.row()] = (self.levelList[index.row()][0], levelNumbers[value])
        logger = logging.getLogger(self.levelList[index.row()][0])
        logger.setLevel(levelNumbers[value])
        
    def setData(self, index, value, role):
        return { (QtCore.Qt.EditRole,1): partial( self.setLevel, index, str(value) ),
                }.get((role,index.column()), lambda: False )()
                
    def setValue(self, index, value):
        self.setData( index, value, QtCore.Qt.EditRole)
        
    def flags(self, index ):
        return  [QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
                 QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled][index.column()]

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
        logger = logging.getLogger(__name__)
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
