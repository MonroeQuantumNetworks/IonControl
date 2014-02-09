# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 16:57:23 2013

@author: jamizra
"""

from PyQt4 import QtCore, QtGui, uic


WidgetContainerForm, WidgetContainerBase = uic.loadUiType(r'C:\Users\jamizra\Programming\playground\TestTraceTree.ui')

class TraceTreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
    
    def appendChild(self, item):
        return self.childItems.append(item)
    
    def child(self, row):
        return self.childItems[row]
        
    def childCount(self):
        return len(self.childItems)
        
    def columnCount(self):
        return 4
    
    def data(self, column):
        if column < len(self.itemData):
            return self.itemData[column]
        else:
            return None
    
    def parent(self):
        return self.parentItem
    
    def row(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        else:
            return 0
            
    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False
        self.itemData[column] = value
        return True

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False
        for _ in range(count):
            data = [None] * len(columns)
            item = TraceTreeItem(data, parent=self)
            self.childItems.insert(position, item)
        return True

class TraceTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, initialData, parent=None):
        super(TraceTreeModel, self).__init__(parent)
        self.rootItem = TraceTreeItem(['', 'column 1', 'column 2', 'column 3'])
        for element in initialData:
            if element.parent() == None:
                element.parentItem = self.rootItem
                self.rootItem.appendChild(element)
    
    def index(self, row, column, parentIndex):
        if not self.hasIndex(row, column, parentIndex):
            return QtCore.QModelIndex()

        if not parentIndex.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parentIndex.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)

        return QtCore.QModelIndex()
    
    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        
        childItem = index.internalPointer()
        parentItem = childItem.parent()
        
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        else:
            return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parentIndex):
        if parentIndex.column() > 0:
            return 0
        if not parentIndex.isValid():
            parent= self.rootItem
        else:
            parent= parentIndex.internalPointer()
        return parent.childCount()
        
    def columnCount(self, parent):
        return 4
            
    def data(self, index, role):
        if not index.isValid():
            return None
        col = index.column()
        item = index.internalPointer()
        if role == QtCore.Qt.CheckStateRole and col == 0:
            if item.itemData[0] > 0:
                return QtCore.Qt.Checked 
            else:
                return QtCore.Qt.Unchecked
        elif role != QtCore.Qt.DisplayRole:
            return None
        elif col != 0:
            return item.data(col-1)
        else:
            return None

    def flags(self, index):
        col = index.column()
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        elif col == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
            
    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)
        else:
            return None
          
    def setData(self, index, value, role):
        col = index.column()
        item = index.internalPointer()

        if role == QtCore.Qt.EditRole:
            result = item.setData(col-1, value.toFloat()[0])
            if result:
                self.dataChanged.emit(index, index)
            return result

        elif role == QtCore.Qt.CheckStateRole:
            self.layoutAboutToBeChanged.emit()
            if QtCore.Qt.CheckState(str(value.toString())) == QtCore.Qt.Checked:
                result = item.setData(0,10)
            else:
                result = item.setData(0, -5)
            self.layoutChanged.emit()
            if result:
                self.dataChanged.emit(index, index)
            return result

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem
        
    def insertRows(self, position, rows, parentIndex=QtCore.QModelIndex()):
        parentItem = self.getItem(parentIndex)
        self.beginInsertRows(parentIndex, position, position + rows - 1)
        success = parentItem.insertChildren(position, rows, self.rootItem.columnCount())
        self.endInsertRows()
#        if success:
#            self.dataChanged.emit(parentIndex, parentIndex)
        return success

class WidgetContainerUi(WidgetContainerBase,WidgetContainerForm):
    def __init__(self, parent=None):
        WidgetContainerBase.__init__(self,parent)
        WidgetContainerForm.__init__(self)

    def setupUi(self,MainWindow):
        WidgetContainerForm.setupUi(self,MainWindow)
        item1 = TraceTreeItem([1, 2, 3.5])
        item2 = TraceTreeItem([3, 1, 23], item1)
        item1.appendChild(item2)
        item3 = TraceTreeItem([152, 9, 7])
        item4 = TraceTreeItem([55, 19, 69],item3)
        item3.appendChild(item4)
        item5 = TraceTreeItem([99, 9, 1951],item3)
        item3.appendChild(item5)
        item6 = TraceTreeItem([5930285,13519, 1011101],item3)
        item3.appendChild(item6)
        item7 = TraceTreeItem([1,2,311], item6)
        item6.appendChild(item7)
        item8 = TraceTreeItem([999,11,235])
        items = [item1, item2, item3, item4, item5, item6, item7, item8]
        
        self.treeModel = TraceTreeModel(items)
        self.treeView.setModel(self.treeModel)
        
        self.AddElementButton.clicked.connect(self.onAddElement)
        
    def onAddElement(self):
        parentIndex = self.treeView.selectedIndexes()[0]
        parentItem = self.treeModel.getItem(parentIndex)
        self.treeModel.insertRows(len(parentItem.childItems), 1, parentIndex)
#        self.treeModel.
    
if __name__ == '__main__':
    import sys    
    app = QtGui.QApplication(sys.argv)
    ui = WidgetContainerUi()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
    