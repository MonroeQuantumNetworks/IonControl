# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 16:57:23 2013

@author: jamizra
"""

from PyQt4 import QtCore, QtGui

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
        return len(self.itemData)
    
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
            
class TraceTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, topLevelData, parent=None):
        super(TraceTreeModel, self).__init__(parent)
        self.rootItem = TraceTreeItem(['column 1', 'column 2', 'column 3'])
        for element in topLevelData:
            element.parentItem = self.rootItem
            self.rootItem.appendChild(element)
    
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        
        elif not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
            
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
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
        
    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        return parentItem.childCount()
        
    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()
            
    def data(self, index, role):
        if not index.isValid():
            return None
            
        elif role != QtCore.Qt.DisplayRole:
            return None
        
        item = index.internalPointer()
        
        return item.data(index.column())
        
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            
    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)
        else:
            return None
          

            
if __name__ == "__main__":
    
    import sys    
    
    item1 = TraceTreeItem(['a', 'b', 'c'])
    item2 = TraceTreeItem([3, 'q', 'L'], item1)
    item1.appendChild(item2)
    item3 = TraceTreeItem(['r', 9, 7])
    item4 = TraceTreeItem(['ab', 19, 'z'],item3)
    item3.appendChild(item4)
    item5 = TraceTreeItem(['abga', 9, 'aba'],item3)
    item3.appendChild(item5)
    item6 = TraceTreeItem(['rrr',13519, 1011101],item3)
    item3.appendChild(item6)
    item7 = TraceTreeItem([1,2,311], item6)
    item6.appendChild(item7)
    
    treemodel = TraceTreeModel([item1, item3])
    
    app = QtGui.QApplication(sys.argv)

    view = QtGui.QTreeView()
    view.setModel(treemodel)
    view.setWindowTitle("Simple Tree Model")
    view.show()
    sys.exit(app.exec_())
    
    
    