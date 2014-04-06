'''
Created on Apr 6, 2014

@author: pmaunz
'''
from PyQt4 import QtCore

class TodoListTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal( object )
    headerDataLookup = ['Scan', 'Measurement']
    def __init__(self, todolist, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.todolist = todolist
        self.dataLookup =  { (QtCore.Qt.DisplayRole,0): lambda row: self.todolist[row].scan,
                             (QtCore.Qt.DisplayRole,1): lambda row: self.todolist[row].measurement,
                             }

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.todolist) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def flags(self, index ):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None #QtCore.QVariant()
                        
    def moveRow(self, rows, up=True):
        if up:
            if len(rows)>0 and rows[0]>0:
                for row in rows:
                    self.todolist[row], self.todolist[row-1] = self.todolist[row-1], self.todolist[row]
                    self.dataChanged.emit( self.createIndex(row-1,0), self.createIndex(row,3) )
                return True
        else:
            if len(rows)>0 and rows[0]<len(self.todolist)-1:
                for row in rows:
                    self.todolist[row], self.todolist[row+1] = self.todolist[row+1], self.todolist[row]
                    self.dataChanged.emit( self.createIndex(row,0), self.createIndex(row+1,3) )
                return True
        return False

    def addMeasurement(self,todoListElement):
        self.beginInsertRows(QtCore.QModelIndex(),len(self.todolist),len(self.todolist))
        self.todolist.append( todoListElement )
        self.endInsertRows()
        return len(self.todolist)-1
        
    def dropMeasurement (self,row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row )
        self.todolist.pop(row)
        self.endRemoveRows()
    
    
            
