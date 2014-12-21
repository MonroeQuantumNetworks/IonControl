from PyQt4 import QtCore, QtGui
from modules.firstNotNone import firstNotNone
from _functools import partial


class AnalysisTableModel(QtCore.QAbstractTableModel):
    backgroundLookup = {True:QtGui.QColor(QtCore.Qt.green).lighter(175), False:QtGui.QColor(QtCore.Qt.white)}     
    def __init__(self, analysisDefinition, config, globalDict, fitNames, evaluationNames, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.config = config 
        self.dataLookup = { (QtCore.Qt.CheckStateRole,0): lambda row:  QtCore.Qt.Checked if self.analysisDefinition[row].enabled else QtCore.Qt.Unchecked,
                            (QtCore.Qt.DisplayRole,1): lambda row: self.analysisDefinition[row].evaluation,
                            (QtCore.Qt.DisplayRole,2): lambda row: self.analysisDefinition[row].analysis,
                            (QtCore.Qt.EditRole,1): lambda row: self.analysisDefinition[row].evaluation,
                            (QtCore.Qt.EditRole,2): lambda row: self.analysisDefinition[row].analysis,
                            }                           
        self.setDataLookup =   { (QtCore.Qt.EditRole,1): partial( self.setString, 'evaluation' ),
                                 (QtCore.Qt.EditRole,2): partial( self.setString, 'analysis'),
                                 (QtCore.Qt.CheckStateRole,0): self.setEnabled }
        self.analysisDefinition = analysisDefinition
        self.pushDestinations = []
        self.globalDict = globalDict
        self.fitNames = fitNames
        self.evaluationNames = evaluationNames
                  
    def choice(self, index):
        if index.column()==1:
            return sorted(self.evaluationNames())
        elif index.column()==2:
            return sorted(self.fitNames())
        return None
                         
    def setEnabled(self, row, value):
        self.analysisDefinition[row].enabled = value==QtCore.Qt.Checked
        return True
        
    def setString(self, attr, row, value):
        value =  str(value)
        if value:
            setattr( self.analysisDefinition[row], attr, value)
            return True
        return False

    def addAnalysis(self, analysis):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self.analysisDefinition.append( analysis )
        self.endInsertRows()
             
    def removeAnalysis(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self.analysisDefinition.pop(index)
        self.endRemoveRows()       
                         
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.analysisDefinition) if self.analysisDefinition else 0
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 3

    def update(self):
        self.dataChanged.emit( self.createIndex(0,0), self.createIndex(self.rowCount(),7) )
 
    def setAnalysisDefinition(self, analysisDefinition):
        self.beginResetModel()
        self.analysisDefinition = analysisDefinition
        self.endResetModel()
        
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def setData(self,index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda row, value: None)(index.row(),value)
    
    def setValue(self, index, value):
        #self.fitfunction.startParameters[index.row()] = value
        self.setData( index, value, QtCore.Qt.EditRole)

    def flags(self, index ):
        if index.column()==0:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable
        if index.column() in [1,2]:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    headerDataLookup = ['Enable', 'Evaluation', 'Analysis']
    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None #QtCore.QVariant()
    
    def saveConfig(self):
        pass
    
