'''
Created on Dec 22, 2014

@author: pmaunz
'''

import PyQt4.uic
from PyQt4 import QtGui, QtCore
from modules.SequenceDict import SequenceDict
from networkx import DiGraph
from _collections import defaultdict

ControlForm, ControlBase = PyQt4.uic.loadUiType(r'..\..\ui\TreeViewTest.ui')


class Structure(object):
    def __init__(self):
        self.children = defaultdict( list )
        self.parent = dict()
        
    def addEdge(self, parent, child):
        self.children[parent].append(child)
        self.parent[child] = parent
        
    def insertEdge(self, parent, child, index ):
        self.children[parent].insert(index,child)
        self.parent[child] = parent
        
    def removeEdge(self, parent, child):
        children = self.children[parent]
        children.pop( children.index(child) )
        self.parent.pop(child)
        
        

class TreeViewModelAdapter( QtCore.QAbstractItemModel ):
    def __init__(self, data, structure, rootNode, parent=None ):
        super(TreeViewModelAdapter, self).__init__(parent)
        self.data = data
        self.structure = structure
        self.rootNode = rootNode
        self.dataLookup = { (QtCore.Qt.DisplayRole,0): lambda child: child,
                            (QtCore.Qt.DisplayRole,1): lambda child: self.data[child] }
        
    def data(self, index, role):
        nodeName = self.getItem(index)
        return self.dataLookup.get( (role,index.column()), lambda child: None )(nodeName)

    def flags(self, index):
        if index.column()==0:
            return (QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled) 
        return (QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsSelectable)

    headerLookup = ['Key','Value']
    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerLookup[section]

    def index(self, row, column, parent):
        if (parent.isValid() and parent.column() != 0):
            return QtCore.QModelIndex()
        parentName = self.getItem(parent)
        childName =  self.structure.out_edges(parentName)[row][1]
        if childName:
            return self.createIndex(row, column, childName)
    
    def getItem(self, index):
        if index.isValid():
            return index.internalPointer()
        return self.rootNode    

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        childName = self.getItem(index)
        parentName = self.structure.in_edges(childName)[0][0]
        if parentName == self.rootNode:
            return QtCore.QModelIndex()
        return self.createIndex(self.structure.out_edges(parentName).index((parentName,childName)), 0, parentName)
        
    def rowCount(self, parent):
        parentName = self.getItem(parent)
        return len(self.structure.out_edges(parentName)) 
    
    def columnCount(self, parent):
        return len(self.headerLookup)
    
    def supportedDragActions(self):
        return QtCore.Qt.MoveAction
    
    def supportedDropActions(self):
        return QtCore.Qt.MoveAction
    
    def mimeTypes(self):
        return ["text.list"]
    
    def mimeData(self, indices):
        mimedata = QtCore.QMimeData()
        mimedata.setData('text.list', '\n'.join((self.getItem(index) for index in indices)) )
        return mimedata
        
    def dropMimeData(self, mimedata, action, row, column, parentIndex ):
        if not mimedata.hasFormat("text.list"):
            return False
        items = str(mimedata.data("text.list")).splitlines()
        self.insertItems(row, items, parentIndex)
        return True
    
    def insertItems(self, row, items, parentIndex):
        parentName = self.getItem(parentIndex)
        self.beginInsertRows( parentIndex, row, row+len(items)-1 )
        for item in items:
            self.structure.add_edge( parentName, item )
        self.endInsertRows()
        return True 

class TreeViewTest( ControlForm, ControlBase ):
    def __init__(self, parent=None):
        ControlForm.__init__(self)
        ControlBase.__init__(self,parent)
        self.data = { 'alpha': 'a', 'beta':'b', 'gamma':'c' }
        self.structure = DiGraph()
        self.structure.add_edges_from([('root','alpha'),('gamma','beta'),('alpha','gamma')])
       
    def setupUi(self, parent):
        ControlForm.setupUi(self,parent)
        self.model = TreeViewModelAdapter(self.data, self.structure, 'root')
        self.treeView.setModel( self.model )
        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.setDropIndicatorShown(True)
        # History and Dictionary

if __name__=="__main__":
    import sys
    from PyQt4 import QtGui
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    
    
    data = SequenceDict( {})
    
    ui = TreeViewTest()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
