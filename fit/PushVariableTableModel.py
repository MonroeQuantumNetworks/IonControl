from PyQt4 import QtCore


class PushVariableTableModel(QtCore.QAbstractTableModel):
    
    def __init__(self, config, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.config = config 
        self.dataLookup = { (QtCore.Qt.CheckStateRole,0): lambda row:  QtCore.Qt.Checked if self.fitfunction.pushVariables.at(row).push else QtCore.Qt.Unchecked,
                            (QtCore.Qt.DisplayRole,1): lambda row: str(self.fitfunction.pushVariables.at(row).globalName),
                            (QtCore.Qt.DisplayRole,2): lambda row: str(self.fitfunction.pushVariables.at(row).definition),
                            (QtCore.Qt.DisplayRole,3): lambda row: str(self.fitfunction.pushVariables.at(row).value),                           
                            (QtCore.Qt.DisplayRole,4): lambda row: str(self.fitfunction.pushVariables.at(row).minimum),
                            (QtCore.Qt.DisplayRole,5): lambda row: str(self.fitfunction.pushVariables.at(row).maximum),
                            (QtCore.Qt.EditRole,1): lambda row: self.fitfunction.pushVariables.at(row).globalName,
                            (QtCore.Qt.EditRole,2): lambda row: self.fitfunction.pushVariables.at(row).definition,
                            (QtCore.Qt.EditRole,4): lambda row: self.fitfunction.pushVariables.at(row).minimum,
                            (QtCore.Qt.EditRole,5): lambda row: self.fitfunction.pushVariables.at(row).maximum,
                            }                           
        self.setDataLookup =   { (QtCore.Qt.EditRole,1): self.setDataGlobalName,
                                 (QtCore.Qt.EditRole,2): self.setDataDefinition,
                                 (QtCore.Qt.EditRole,4): self.setDataMinimum,
                                 (QtCore.Qt.EditRole,5): self.setDataMaximum,
                                 (QtCore.Qt.CheckStateRole,0): self.setDataPush }
        self.fitfunction = None
                         
    def setDataPush(self, row, value):
        self.fitfunction.pushVariables.at(row).push = value==QtCore.Qt.Checked
        return True
        
    def setDataGlobalName(self, row, value):
        value =  str(value.toString())
        if value:
            self.fitfunction.pushVariables.at(row).globalName = value
            self.fitfunction.pushVariables.renameAt(row,value)
            return True
        return False

    def setDataDefinition(self, row, value):
        value =  str(value.toString())
        if value:
            self.fitfunction.pushVariables.at(row).definition = value
            self.fitfunction.pushVariables.at(row).evaluate(dict(zip(self.fitfunction.parameterNames,self.fitfunction.parameters)))
            self.dataChanged.emit( self.createIndex(row,3), self.createIndex(row,3))
            return True
        return False
        
    def setDataMinimum(self, row, value):
        self.fitfunction.pushVariables.at(row).minimum = value
        return True
        
    def setDataMaximum(self, row, value):
        self.fitfunction.pushVariables.at(row).maximum = value
        return True
                         
    def addVariable(self, pushVariable ):
        if pushVariable.globalName not in self.fitfunction.pushVariables:
            self.beginInsertRows(QtCore.QModelIndex(), len(self.fitfunction.pushVariables), len(self.fitfunction.pushVariables))
            self.fitfunction.pushVariables[pushVariable.globalName] = pushVariable
            self.endInsertRows()
             
    def removeVariable(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self.fitfunction.pushVariables.popAt(index)
        self.endRemoveRows()
        
                         
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.fitfunction.pushVariables) if self.fitfunction else 0
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 6
 
    def setFitfunction(self, fitfunction):
        self.beginResetModel()
        self.fitfunction = fitfunction
        self.endResetModel()
        
    def allDataChanged(self):
        pass
    
    def fitDataChanged(self):
        self.dataChanged.emit( self.createIndex(0,0), self.createIndex(self.rowCount(),3))
        replacement = dict(zip(self.fitfunction.parameterNames,self.fitfunction.parameters))
        for pushvar in self.fitfunction.pushVariables.values():
            pushvar.evaluate(replacement)
 
    def startDataChanged(self):
        pass
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def setData(self,index, value, role):
        return self.setDataLookup[(role,index.column())](index.row(),value)
    
    def setValue(self, row, value):
        self.fitfunction.startParameters[row] = value

    def flags(self, index ):
        if index.column()==0:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable
        if index.column() in [1,2,4,5]:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    headerDataLookup = ['Push', 'Global', 'Definition', 'Value', 'Min Accept', 'Max Accept']
    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None #QtCore.QVariant()
    
    def saveConfig(self):
        pass
