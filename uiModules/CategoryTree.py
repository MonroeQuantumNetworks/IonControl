__author__ = 'jmizrahi'

from PyQt4 import QtCore, QtGui
from modules.enum import enum
from modules.Utility import indexWithDefault
import functools
from uiModules.KeyboardFilter import KeyListFilter
nodeTypes = enum('category', 'data')

class Node(object):
    """Class for tree nodes"""
    def __init__(self, parent, id, nodeType, content):
        self.parent = parent #parent node
        self.id = id #All nodes need a unique id
        self.content = content #content is the actual data in the tree, it can be anything
        self.children = []
        self.nodeType = nodeType #nodeTypes.category or nodeTypes.data
        self.isBold = False #Determines whether node is shown bold

    def childCount(self):
        return len(self.children)

    def child(self, row):
        if 0 <= row < self.childCount():
            return self.children[row]

    def __eq__(self, other):
        return self.id==other.id

    def __str__(self):
        return "Node: " + str(self.id)

    @property
    def row(self):
        """Return this node's row in its parent's list of children"""
        return self.parent.children.index(self) if (self.parent and self.parent.children) else 0

    @row.setter
    def row(self, newRow):
        if 0 <= newRow < len(self.parent.children):
            self.parent.children.insert( newRow, self.parent.children.pop(self.row) )


class CategoryTreeModel(QtCore.QAbstractItemModel):
    """Base class for category trees.

    A category tree is a simplified tree structure in which a flat list of data is broken down by categories. It
    is intended to be an extension of a table model, in which the elements of the table are broken down into different
    categories. The data itself is not hierarchical. For that reasons, the data can be presented to the model as a
    flat list. If a given element of the list has an attribute defined by categoriesAttr, then that element will be displayed
    beneath those categories. categoriesAttr is a list of strings, with the most general category first. If categoriesAttr
    is a string, it is interpreted as a list of strings of length 1.

    Other attributes that are respected are "hasDepedency" and "isBold." If the content has one of those attributes,
    the content is displayed accordingly.
    """
    def __init__(self, contentList=[], parent=None, categoriesAttr='categories', nodeNameAttr='name'):
        super(CategoryTreeModel, self).__init__(parent)
        #attribute that determines how to categorize content
        self.categoriesAttr = categoriesAttr
        #attribute that determines node names
        self.nodeNameAttr = nodeNameAttr

        #styling for different types of content
        #self.normalBgColor = QtGui.QColor(QtCore.Qt.white)
        self.dependencyBgColor = QtGui.QColor(QtCore.Qt.green).lighter(175)
        self.defaultFontName = str(QtGui.QFont().defaultFamily())
        self.normalFont = QtGui.QFont(self.defaultFontName,-1,QtGui.QFont.Normal)
        self.boldFont = QtGui.QFont(self.defaultFontName,-1,QtGui.QFont.Bold)

        #lookups to determine the appearance of the model
        self.fontLookup = {True:self.boldFont, False:self.normalFont}
        self.headerLookup = {} #overwrite to set headers. key: (orientation, role, section) val: str
        self.dataLookup = {
                           (QtCore.Qt.DisplayRole, 0):
                               lambda node: str(node.content) #default, normally overwritten
                           }
        self.backgroundFunction = lambda node: self.dependencyBgColor if getattr(node.content,'hasDependency',None) else None
        self.toolTipFunction = lambda node: getattr(node.content,'string','') if getattr(node.content,'hasDependency',None) else None
        self.dataAllColLookup = { #data lookup that applies to all columns
            QtCore.Qt.FontRole:
                  lambda node: self.fontLookup.get(getattr(node, 'isBold', False))
            }
        self.categoryDataLookup = {(QtCore.Qt.DisplayRole, 0): lambda node: node.content}
        self.categoryDataAllColLookup = {QtCore.Qt.FontRole: lambda node: self.fontLookup.get(getattr(node, 'isBold', False))}
        self.setDataLookup = {} #overwrite to set data. key: (role, col). val: function that takes (index, value)
        self.categorySetDataLookup = {} #overwrite to set data. key: (role, col). val: function that takes (index, value)
        self.flagsLookup = {0: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable} #default, normally overwritten
        self.categoryFlagsLookup = {0: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable}
        self.numColumns = 1 #Overwrite with number of columns
        self.allowReordering = False #If True, nodes can be moved around
        self.allowDeletion = False #If True, nodes can be deleted
        self.root = Node(parent=None, id='', nodeType=nodeTypes.category, content=None)
        self.nodeDict = {'': self.root} #dictionary of all nodes, with string indicating hierarchy to that item
        #contentList is a list of objects. Can be anything. If the objects have a category attribute, a tree will result.
        self.addNodeList(contentList)

    def nodeFromIndex(self, index):
        """Return the node at the given index"""
        return index.internalPointer() if index.isValid() else self.root

    def indexFromNode(self, node, col=0):
        """Return a model index for the given node column"""
        if node == self.root:
            return QtCore.QModelIndex()
        else:
            parentIndex = QtCore.QModelIndex() if node.parent==self.root else self.indexFromNode(node.parent) #recursive
            return self.index(node.row, col, parentIndex)

    def getLocation(self, index):
        """Return the node, column at the given index"""
        node = self.nodeFromIndex(index)
        return node, index.column()

    def index(self, row, column, parentIndex):
        """Return a model index for the node at the given row, column, parentIndex"""
        if not self.hasIndex(row, column, parentIndex):
            ind = QtCore.QModelIndex()
        else:
            parentNode = self.nodeFromIndex(parentIndex)
            node = parentNode.child(row)
            ind = self.createIndex(row, column, node) if node else QtCore.QModelIndex()
        return ind

    def rowCount(self, index):
        node = self.nodeFromIndex(index)
        return node.childCount()

    def columnCount(self, index):
        return self.numColumns

    def data(self, index, role):
        node, col = self.getLocation(index)
        if node.nodeType==nodeTypes.category:
            return self.categoryDataLookup.get( (role, col), self.categoryDataAllColLookup.get(role, lambda node: None))(node)
        else:
            return self.dataLookup.get( (role, col), self.dataAllColLookup.get(role, lambda node: None))(node)

    def setData(self, index, value, role):
        node, col = self.getLocation(index)
        if node.nodeType==nodeTypes.category:
            return self.categorySetDataLookup.get( (role, col), lambda index, value: False)(index, value)
        else:
            return self.setDataLookup.get( (role, col), lambda index, value: False)(index, value)

    def parent(self, index):
        node = self.nodeFromIndex(index)
        parentNode = node.parent
        return QtCore.QModelIndex() if (node == self.root or parentNode == self.root) else self.createIndex(parentNode.row, 0, parentNode)

    def flags(self, index ):
        node, col = self.getLocation(index)
        if node.nodeType==nodeTypes.category:
            return self.categoryFlagsLookup.get(col, QtCore.Qt.NoItemFlags)
        else:
            return self.flagsLookup.get(col, QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def headerData(self, section, orientation, role):
        return self.headerLookup.get((orientation, role, section))

    def addNodeList(self, contentList):
        """Add a list of nodes to the tree"""
        for listIndex, content in enumerate(contentList):
            name = getattr(content, self.nodeNameAttr, str(listIndex))
            self.addNode(content, name)

    def addNode(self, content, name=None):
        """Add a node to the tree containing 'content' with name 'name'"""
        if not name:
            name = getattr(content, self.nodeNameAttr)
        name = str(name)
        categories = getattr(content, self.categoriesAttr, None)
        categories = [categories] if categories.__class__==str else categories # make a list of one if it's a string
        categories = None if categories.__class__!=list else categories #no categories if it's not a list
        categories = map(str, categories) if categories else categories #turn into list of strings
        parent = self.makeCategoryNodes(categories) if categories else self.root
        id, nodeType = parent.id+'_'+name if parent.id else name, nodeTypes.data
        node = Node(parent, id, nodeType, content)
        self.addRow(parent, node)
        self.nodeDict[id] = node

    def removeNode(self, node):
        """Remove the specified node from the tree"""
        if self.allowDeletion and node!=self.root:
            parent = node.parent
            row = node.row
            id = node.id
            parentIndex = self.indexFromNode(parent)
            self.beginRemoveRows(parentIndex, row, row)
            del parent.children[row]
            del self.nodeDict[id]
            del node
            self.endRemoveRows()

    def makeCategoryNodes(self, categories):
        """Recursively creates tree nodes from the provided list of categories"""
        key = '_'.join(categories)
        if key not in self.nodeDict: #the empty key will always be in the dictionary, so the recursion will end
            parent = self.makeCategoryNodes(categories[:-1]) #This is the recursive step
            name = categories[-1]
            node = Node(parent=parent, id=parent.id+'_'+name if parent.id else name, nodeType=nodeTypes.category, content=name)
            self.addRow(parent, node)
            self.nodeDict[key] = node
        return self.nodeDict[key]

    def addRow(self, parent, node):
        """Add 'node' to the table under 'parent'"""
        parentIndex = self.indexFromNode(parent)
        self.beginInsertRows(parentIndex, parent.childCount(), parent.childCount())
        parent.children.append(node)
        self.endInsertRows()

    def nodeFromContent(self, content):
        success=False
        for node in self.nodeDict.itervalues():
            if node.content==content:
                success=True
                break
        return node if success else None

    def nodeFromId(self, id):
        success=False
        for node in self.nodeDict.itervalues():
            if node.id==id:
                success=True
                break
        return node if success else None

    def clear(self):
        self.root.children = []
        self.nodeDict = {'': self.root}

    def moveRow(self, index, up):
        """move modelIndex 'index' up if up is True, else down"""
        node=self.nodeFromIndex(index)
        delta = -1 if up else 1
        parentIndex=self.indexFromNode(node.parent)
        if 0 <= node.row+delta < len(node.parent.children):
            moveValid = self.beginMoveRows(parentIndex, node.row, node.row, parentIndex, node.row-1 if up else node.row+2)
            if moveValid:
                node.row += delta
                self.endMoveRows()

    def contentFromIndex(self, index):
        """Get the content associated with the given index"""
        return self.nodeFromIndex(index).content


class CategoryTreeView(QtGui.QTreeView):
    """Class for viewing category trees"""
    def __init__(self, parent=None):
        super(CategoryTreeView, self).__init__(parent)
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown, QtCore.Qt.Key_Delete], [QtCore.Qt.Key_B] )
        self.filter.keyPressed.connect(self.onKey)
        self.filter.controlKeyPressed.connect(self.onControl)
        self.installEventFilter(self.filter)

    def onKey(self, key):
        if key==QtCore.Qt.Key_Delete:
            self.onDelete()
        elif key in [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown]:
            self.onReorder(key==QtCore.Qt.Key_PageUp)

    def onControl(self, key):
        if key==QtCore.Qt.Key_B:
            self.onBold()

    def onBold(self):
        indexes = self.selectionModel().selectedRows(0)
        model=self.model()
        for leftIndex in indexes:
            node=model.nodeFromIndex(leftIndex)
            node.isBold = not node.isBold if hasattr(node,'isBold') else True
            rightIndex = model.indexFromNode(node, model.numColumns-1)
            model.dataChanged.emit(leftIndex, rightIndex)

    def onDelete(self):
        model=self.model()
        if model.allowDeletion:
            indexes = self.selectionModel().selectedRows(0)
            for leftIndex in indexes:
                node=model.nodeFromIndex(leftIndex)
                if node!=model.root:
                    model.removeNode(node)

    def onReorder(self, up):
        if self.model().allowReordering:
            indexList = self.selectionModel().selectedRows(0)
            indexList.sort(key=lambda index: index.row())
            if not up: indexList.reverse()
            for index in indexList:
                self.model().moveRow(index, up)

    def treeState(self):
        """Returns tree state for saving config"""
        columnWidths = self.header().saveState()
        expandedNodeKeys = []
        boldNodeKeys = []
        idTree = {}
        for key, node in self.model().nodeDict.iteritems():
            index = self.model().indexFromNode(node)
            if self.isExpanded(index):
                expandedNodeKeys.append(key)
            if getattr(node, 'isBold', False):
                boldNodeKeys.append(key)
            if self.model().allowReordering: #Only save this if the model is has reordering enabled
                idTree[node.id] = [child.id for child in node.children]
        return columnWidths, expandedNodeKeys, boldNodeKeys, idTree

    def restoreTreeState(self, state):
        """load in a tree state from the given column widths, expanded nodes, bold nodes, and idTree"""
        columnWidths, expandedNodeKeys, boldNodeKeys, idTree = state
        if self.model().allowReordering:
            self.model().beginResetModel()
            for id, childList in idTree.iteritems():
                node=self.model().nodeFromId(id)
                if node:
                    node.children.sort(key=lambda node: indexWithDefault(childList, node.id))
            self.model().endResetModel()
        if columnWidths:
            self.header().restoreState(columnWidths)
        if expandedNodeKeys:
            for key in expandedNodeKeys:
                if key in self.model().nodeDict:
                    node = self.model().nodeDict[key]
                    index = self.model().indexFromNode(node)
                    self.expand(index)
        if boldNodeKeys:
            for key in boldNodeKeys:
                if key in self.model().nodeDict:
                    node = self.model().nodeDict[key]
                    node.isBold=True


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    class myContent(object):
        def __init__(self, data1, data2, categories=None, hasDependency=False, string='', isBold=False):
            self.data1 = data1
            self.data2 = data2
            self.categories = categories
            self.hasDependency = hasDependency
            self.string = string
            self.isBold = isBold
        def __str__(self):
            return str((str(self.data1), str(self.data2)))
    class myModel(CategoryTreeModel):
        def __init__(self, contentList=[], parent=None, categoriesAttr='categories', nodeNameAttr='name'):
            super(myModel, self).__init__(contentList,parent,categoriesAttr,nodeNameAttr)
            self.numColumns=2
            self.allowReordering=True
            self.allowDeletion=True
            self.headerLookup.update({
                    (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 0): 'Name',
                    (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 1): 'Value'
                    })
            self.dataLookup.update({
                           (QtCore.Qt.DisplayRole, 0):
                               lambda node: str(node.content.data1),
                           (QtCore.Qt.DisplayRole, 1):
                               lambda node: str(node.content.data2),
                           (QtCore.Qt.EditRole, 1):
                               lambda node: str(node.content.data2)
                           })
            self.setDataLookup.update({
                (QtCore.Qt.EditRole, 1): lambda index, value: self.setValue(index, value)
                })
            self.flagsLookup.update({
                0: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable,
                1: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
                })

        def setValue(self, index, value):
            node = self.nodeFromIndex(index)
            node.content.data2 = str(value.toString())
            return True

    model = myModel([myContent('hot dog', 3, ['Foods', 'Red'], True, 'qq',isBold=True),
                     myContent('strawberry', 4, ['Foods', 'Red']),
                     myContent('blueberry', 12, ['Foods', 'Blue'],isBold=True),
                     myContent('golf',2,['Games', 'ball based'],True,'abc'),
                     myContent('baseball',12,['Games', 'ball based']),
                     myContent('hockey', 13, ['Games','puck based']),
                     myContent('People', 12, ['People']),
                     myContent('Huey',225, ['People']),
                     myContent('Dewey', 1251,['People']),
                     myContent('Louie', 12,['People']),
                     myContent('other',125121)
                     ])
    view = CategoryTreeView()
    view.setModel(model)
    view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    window = QtGui.QMainWindow()
    dock = QtGui.QDockWidget("Category Tree View")
    dock.setWidget(view)
    window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
    window.show()
    sys.exit(app.exec_())