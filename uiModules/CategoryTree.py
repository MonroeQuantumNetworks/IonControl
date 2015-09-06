__author__ = 'jmizrahi'

from PyQt4 import QtCore, QtGui

class TreeNode(object):
    """Base class for tree nodes"""
    def __init__(self, parent, row):
        self.parent = parent #parent node
        self.row = row #this node's row number in its parent's children
        self.nodeType = 'node'

    def childCount(self):
        return 0

    def child(self, row):
        return None


class CategoryNode(TreeNode):
    """Class for category nodes"""
    def __init__(self, parent, row, name):
        super(CategoryNode, self).__init__(parent, row)
        self.name = name
        self.children = []
        self.nodeType = 'category'

    def childCount(self):
        return len(self.children)

    def child(self, row):
        if 0 <= row < self.childCount():
            return self.children[row]


class DataNode(TreeNode):
    """Class for data nodes"""
    def __init__(self, parent, row, content):
        super(DataNode, self).__init__(parent, row)
        self.content = content #content is the actual data in the tree, it can be anything
        self.nodeType = 'data'


class CategoryTreeModel(QtCore.QAbstractItemModel):
    """Base class for category trees.

    A category tree is a simplified tree structure in which a flat list of data is broken down by categories. It
    is intended to be an extension of a table model, in which the elements of the table are broken down into different
    categories. The data itself is not hierarchical. For that reasons, the data can be presented to the model as a
    flat list. If a given element of the list has an attribute "categories," then that element will be displayed
    beneath those categories. "categories" is a list of strings, with the most general category first.
    """
    def __init__(self, contentList=[], parent=None):
        super(CategoryTreeModel, self).__init__(parent)
        self.contentList = contentList #list of objects. Can be anything. If the objects have a category attribute, a tree will result.
        self.backgroundLookup = {True:QtGui.QColor(QtCore.Qt.green).lighter(175), False:QtGui.QColor(QtCore.Qt.white)}
        self.headerLookup = {} #overwrite to set headers. key: (orientation, role, section) val: str
        self.dataLookup = {
                           ('category', QtCore.Qt.DisplayRole, 0): lambda node: node.name,
                           ('data', QtCore.Qt.DisplayRole, 0): lambda node: str(node.content) #default, normally overwritten
                           }
        self.dataNoColLookup = \
            {
            ('data', QtCore.Qt.BackgroundRole): lambda node: self.backgroundLookup.get(getattr(node.content,'hasDependency',False)),
            ('data', QtCore.Qt.ToolTipRole): lambda node: getattr(node.content,'string','') if getattr(node.content,'hasDependency',False) else None
            }
        self.setDataLookup = {} #overwrite to set data. key: (type, role, col). val: function that takes (node, value)
        self.flagsLookup = {
                            ('category', 0): QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable,
                            ('data', 0): QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable #default, normally overwritten
                            }
        self.numColumns = 1 #Overwrite with number of columns
        self.root = CategoryNode(None, 0, 'root')
        self.categoryNodes = {(): self.root} #dictionary of category nodes, with tuple indicating hierarchy to that item
        self.addNodeList(self.contentList)

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
        t = node.nodeType
        return self.dataLookup.get( (t, role, col), self.dataNoColLookup.get( (t, role), lambda node: None))(node)

    def setData(self, index, value, role):
        node, col = self.getLocation(index)
        t = node.nodeType
        return self.setDataLookup.get( (t, role, col), lambda node, value: False)(node, value)

    def parent(self, index):
        node = self.nodeFromIndex(index)
        parentNode = node.parent
        return QtCore.QModelIndex() if (node == self.root or parentNode == self.root) else self.createIndex(parentNode.row, 0, parentNode)

    def flags(self, index ):
        node, col = self.getLocation(index)
        t = node.nodeType
        return self.flagsLookup.get((t, col), QtCore.Qt.NoItemFlags)

    def headerData(self, section, orientation, role):
        return self.headerLookup.get((orientation, role, section))

    def addNodeList(self, contentList):
        """Add a list of nodes to the tree"""
        for content in contentList:
            self.addNode(content)

    def addNode(self, content):
        """Add a node to the tree containing 'content' """
        categories = getattr(content, 'categories', None)
        parent = self.makeCategoryNodes(map(str, categories)) if categories else self.root
        node = DataNode(parent, parent.childCount(), content)
        self.addRow(parent, node)

    def makeCategoryNodes(self, categories):
        """Recursively creates tree nodes from the provided list of categories"""
        key = tuple(categories)
        if key not in self.categoryNodes: #the empty tuple will always be in the dictionary, so the recursion will end
            parent = self.makeCategoryNodes(categories[:-1]) #This is the recursive step
            node = CategoryNode(parent, parent.childCount(), categories[-1])
            self.addRow(parent, node)
            self.categoryNodes[key] = node
        return self.categoryNodes[key]

    def addRow(self, parent, node):
        """Add 'node' the table under 'parent'"""
        parentIndex = self.indexFromNode(parent)
        self.beginInsertRows(parentIndex, parent.childCount(), parent.childCount())
        parent.children.append(node)
        self.endInsertRows()


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    class myContent(object):
        def __init__(self, data, categories=None, hasDependency=False, string=''):
            self.data = data
            self.categories = categories
            self.hasDependency = hasDependency
            self.string = string
        def __str__(self):
            return str(self.data)
    model = CategoryTreeModel([myContent('hot dog', ['Foods', 'Red'], True, 'qq'),
                               myContent('strawberry', ['Foods', 'Red']),
                               myContent('blueberry', ['Foods', 'Blue']),
                               myContent('golf',['Games', 'ball based'],True,'abc'),
                               myContent('baseball',['Games', 'ball based']),
                               myContent('hockey', ['Games','puck based']),
                               myContent('Huey', ['People']),
                               myContent('Dewey', ['People']),
                               myContent('Louie', ['People'])
                               ])
    view = QtGui.QTreeView()
    view.setModel(model)
    view.show()
    sys.exit(app.exec_())