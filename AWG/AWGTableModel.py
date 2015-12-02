'''
Created on Jul 2, 2015

@author: Geoffrey Ji
'''
from PyQt4 import QtCore, QtGui

from modules.Expression import Expression
from modules.firstNotNone import firstNotNone


class AWGTableModel(QtCore.QAbstractTableModel):
    headerDataLookup = ["Variable", "Value"]
    valueChanged = QtCore.pyqtSignal( object, object )
    
    def __init__(self, waveform, globalDict, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.waveform = waveform
        self.globalDict = globalDict
        self.defaultBG = QtGui.QColor(QtCore.Qt.white)
        self.textBG = QtGui.QColor(QtCore.Qt.green).lighter(175)

        self.defaultFontName = "Segoe UI"
        self.defaultFontSize = 9
        self.normalFont = QtGui.QFont(self.defaultFontName,self.defaultFontSize,QtGui.QFont.Normal)
        self.boldFont = QtGui.QFont(self.defaultFontName,self.defaultFontSize,QtGui.QFont.Bold)

        self.dataLookup = {
            (QtCore.Qt.DisplayRole, 0): lambda row: self.waveform.varDict.keyAt(row),
            (QtCore.Qt.DisplayRole, 1): lambda row: str(self.waveform.varDict.at(row)['value']),
            (QtCore.Qt.FontRole, 0): lambda row: self.boldFont if self.waveform.varDict.keyAt(row)=='Duration' else self.normalFont,
            (QtCore.Qt.FontRole, 1): lambda row: self.boldFont if self.waveform.varDict.keyAt(row)=='Duration' else self.normalFont,
            (QtCore.Qt.EditRole, 1): lambda row: firstNotNone( self.waveform.varDict.at(row)['text'], str(self.waveform.varDict.at(row)['value'])),
            (QtCore.Qt.BackgroundColorRole, 1): lambda row: self.defaultBG if self.waveform.varDict.at(row)['text'] is None else self.textBG
        }
        self.setDataLookup =  { 
            (QtCore.Qt.EditRole,1): self.setValue,
            (QtCore.Qt.UserRole,1): self.setText
        }
        
    def setValue(self, index, value):
        row = index.row()
        name = self.waveform.varDict.keyAt(row)
        var = self.waveform.varDict.at(row)
        var['value'] = value
        self.valueChanged.emit(name, value)
        return True
    
    def setText(self, index, value):
        row = index.row()
        self.waveform.varDict.at(row)['text'] = value
        return True
    
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.waveform.varDict)
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None

    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)
        
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled if index.column()==0 else QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
            elif (orientation == QtCore.Qt.Vertical):
                return str(section)
        return None  # QtCore.QVariant()
    
    def evaluate(self, name):
        for (varName, varValueTextDict) in self.waveform.varDict.iteritems():
            expr = varValueTextDict['text']
            if expr is not None:
                value = Expression().evaluateAsMagnitude(expr, self.globalDict)
                self.waveform.varDict[varName]['value'] = value   # set saved value to make this new value the default
                modelIndex = self.createIndex(self.waveform.varDict.index(varName),1)
                self.dataChanged.emit(modelIndex, modelIndex)
                self.valueChanged.emit(varName, value)