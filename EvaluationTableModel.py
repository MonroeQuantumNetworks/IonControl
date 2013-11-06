from PyQt4 import QtGui, QtCore

class EvaluationTableModel( QtCore.QAbstractTableModel):
    def __init__(self, evalList=None, parent=None):
        super(EvaluationTableModel, self).__init__(parent)
        if evalList:
            self.evalList = evalList
        else:
            self.evalList = list()
        
    def setEvalList(self, evalList):
        self.beginResetModel()
        self.evalList = evalList
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.evalList)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 3
    
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,0): self.evalList[index.row()].counter,
                     (QtCore.Qt.DisplayRole,1): self.evalList[index.row()].evaluation,
                     (QtCore.Qt.DisplayRole,2): self.evalList[index.row()].name,
                     }.get((role,index.column()),None)
        return None
        
    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Vertical): 
                return str(section)
            elif (orientation == QtCore.Qt.Horizontal): 
                return { 0: 'Counter',
                         1: 'Evaluation',
                         2: 'Name' }[section]
        return None 
