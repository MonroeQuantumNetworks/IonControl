from PyQt4 import QtGui, QtCore
from functools import partial

class EvaluationTableModel( QtCore.QAbstractTableModel):
    dataChanged = QtCore.pyqtSignal()
    def __init__(self, plotnames=None, evalList=None, parent=None):
        super(EvaluationTableModel, self).__init__(parent)
        if evalList:
            self.evalList = evalList
        else:
            self.evalList = list()
        self.plotnames = plotnames
        
    def setEvalList(self, evalList):
        self.beginResetModel()
        self.evalList = evalList
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.evalList)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 4
    
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,0): self.evalList[index.row()].counter,
                     (QtCore.Qt.DisplayRole,1): self.evalList[index.row()].evaluation,
                     (QtCore.Qt.DisplayRole,2): self.evalList[index.row()].name,
                     (QtCore.Qt.DisplayRole,3): self.evalList[index.row()].plotname,
                     (QtCore.Qt.EditRole,2): self.evalList[index.row()].name,
                     (QtCore.Qt.EditRole,3): self.evalList[index.row()].plotname,
                     }.get((role,index.column()),None)
        return None
        
    def flags(self, index ):
        if index.column() in [2,3]:
            return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Vertical): 
                return str(section)
            elif (orientation == QtCore.Qt.Horizontal): 
                return { 0: 'Counter',
                         1: 'Evaluation',
                         2: 'Name',
                         3: 'Plot' }[section]
        return None 

    def setData(self, index, value, role):
        return { (QtCore.Qt.EditRole,2): partial( self.setDataName, index, value ),
                 (QtCore.Qt.EditRole,3): partial( self.setPlotName, index, value ),
                }.get((role,index.column()), lambda: False )()
                
    def setDataName(self, index, name):
        self.evalList[index.row()].name = str(name.toString()).strip()
        self.dataChanged.emit()
        return True
    
    def setPlotName(self, index, plotname):
        self.evalList[index.row()].plotname = plotname
        self.dataChanged.emit()
        return True
        
        