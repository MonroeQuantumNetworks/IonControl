# -*- coding: utf-8 -*-
"""
Created on Wed Jan 02 09:53:48 2013

@author: Jonathan Mizrahi

This is the model used for the list of traces.
"""

from functools import partial

from PyQt4 import QtCore, QtGui
import sip
from modules.enum import enum
from PlottedTrace import PlottedTrace
from uiModules.CategoryTree import CategoryTreeModel, nodeTypes

api2 = sip.getapi("QVariant")==2

class TraceComboDelegate(QtGui.QStyledItemDelegate):
    """
    Class for combo box editor to select what trace color to use

    Args:
        penicons (list[Qicon]): list of icons to select trace color"""
    def __init__(self, penicons):
        QtGui.QStyledItemDelegate.__init__(self)
        self.penicons = penicons        
        
    def createEditor(self,parent, option, index ):
        """Create the combo box editor"""
        editor = QtGui.QComboBox(parent)
        #for icon, string in zip(self.penicons, ["{0}".format(i) for i in range(0,len(self.penicons))] ):
        for icon, string in zip(self.penicons, ['']*len(self.penicons) ):
            editor.addItem( icon, string )
        return editor

    def setEditorData(self,editor, index):
        """Set the data in the editor based on the model"""
        value = index.model().data(index, QtCore.Qt.EditRole) 
        editor.setCurrentIndex(value)
        
    def setModelData(self,editor, model, index):
        """Set the data in the model based on the editor"""
        value = editor.currentIndex()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self,editor, option, index ):
        editor.setGeometry(option.rect)


class TraceModel(CategoryTreeModel):
    """
    Construct the TraceModel.

    Args:
        traceList (list[PlottedTrace]): The initial list of traces
        penicons (list[QtGui.QIcon]): Icons for showing available plot colors
        graphicsViewDict (dict): dictionary of the available plot windows
    """
    traceModelDataChanged = QtCore.pyqtSignal(str, str, str) #string with trace creation date, change type, new value
    traceRemoved = QtCore.pyqtSignal(str) #string with trace creation date
    def __init__(self, traceList, penicons, graphicsViewDict, parent=None, *args): 
        super(TraceModel, self).__init__(traceList, parent, categoriesAttr='category')
        #traceDict is a mapping between trace collection creation times and trace collection top level nodes
        self.traceDict = {node.children[0].content.traceCollection.traceCreation : node for node in self.root.children if node.children}
        self.penicons = penicons
        self.graphicsViewDict = graphicsViewDict
        self.allowDeletion = True
        self.allowReordering = True
        self.columnNames = ['name','pen','window','comment', 'filename']
        self.numColumns = len(self.columnNames)
        self.column = enum(*self.columnNames)
        unsavedBG =  QtGui.QColor(255, 220, 220)
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.name): "Name",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.pen): "Pen    ",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.window): "Window",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.comment): "Comment",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.filename): "Filename"
            })
        self.categoryDataLookup.update({
            (QtCore.Qt.CheckStateRole,self.column.name): self.isCategoryChecked,
            (QtCore.Qt.DisplayRole, self.column.comment): self.comment,
            (QtCore.Qt.EditRole, self.column.comment): self.comment
        })
        self.categoryDataAllColLookup.update({
            QtCore.Qt.BackgroundRole: lambda node: None if self.isCategorySaved(node) else unsavedBG,
        })
        self.dataLookup.update({
            (QtCore.Qt.DisplayRole,self.column.name): lambda node: node.content.name,
            (QtCore.Qt.CheckStateRole,self.column.name): lambda node: QtCore.Qt.Checked if node.content.curvePen > 0 else QtCore.Qt.Unchecked,
            (QtCore.Qt.DecorationRole,self.column.pen): lambda node: QtGui.QIcon(self.penicons[node.content.curvePen]) if hasattr(node.content, 'curve') and node.content.curve is not None else None,
            (QtCore.Qt.EditRole,self.column.pen): lambda node: node.content.curvePen,
            (QtCore.Qt.DisplayRole,self.column.window): lambda node: node.content.windowName,
            (QtCore.Qt.EditRole,self.column.window): lambda node: node.content.windowName,
            (QtCore.Qt.DisplayRole,self.column.comment): self.comment,
            (QtCore.Qt.EditRole,self.column.comment): self.comment,
            (QtCore.Qt.DisplayRole,self.column.filename): lambda node: getattr(node.content.traceCollection, 'fileleaf', None)
            })
        self.dataAllColLookup.update({
            QtCore.Qt.BackgroundRole: lambda node: None if node.content.traceCollection.saved else unsavedBG
        })
        self.setDataLookup.update({
            (QtCore.Qt.CheckStateRole,self.column.name): self.checkboxChange,
            (QtCore.Qt.EditRole,self.column.pen): self.penChange,
            (QtCore.Qt.EditRole,self.column.window): self.windowChange,
            (QtCore.Qt.EditRole,self.column.comment): self.commentChange
            })
        self.categorySetDataLookup.update({
            (QtCore.Qt.CheckStateRole,self.column.name): self.categoryCheckboxChange,
            (QtCore.Qt.EditRole,self.column.comment): self.commentChange
        })
        self.flagsLookup = {
            self.column.name: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
            self.column.pen: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            self.column.window: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            self.column.comment: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            self.column.filename: QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
            }
        self.categoryFlagsLookup = {
            self.column.name: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
            self.column.pen: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
            self.column.window: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
            self.column.comment: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            self.column.filename: QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
            }

    def isCategoryChecked(self, categoryNode):
        """Determine if category node should be checked or not, based on plot status of children"""
        childNodes = self.getDataNodes(categoryNode)
        plottedList = [node.content.curvePen>0 for node in childNodes]
        if not plottedList: return QtCore.Qt.Unchecked
        elif all(plottedList): return QtCore.Qt.Checked
        elif any(plottedList): return QtCore.Qt.PartiallyChecked
        else: return QtCore.Qt.Unchecked

    def isCategorySaved(self, categoryNode):
        """Determine if category node has been saved or not"""
        dataNode = self.getFirstDataNode(categoryNode)
        plottedTrace = getattr(dataNode, 'content', None)
        traceCollection = getattr(plottedTrace, 'traceCollection', None)
        saved = getattr(traceCollection, 'saved', None)
        return saved

    def comment(self, node):
        """return comment associated with node"""
        dataNode = self.getFirstDataNode(node)
        plottedTrace = getattr(dataNode, 'content', None)
        traceCollection = getattr(plottedTrace, 'traceCollection', None)
        comment = getattr(traceCollection, 'comment', None)
        return comment

    def choice(self, index):
        """return available plot windows"""
        return self.graphicsViewDict.keys() if index.column()==self.column.window else []

    def setValue(self, index, value):
        """set index EditRole to value"""
        self.setData(index, value, QtCore.Qt.EditRole)

    def windowChange(self, index, value):
        """change the plot window on which the plottedTrace is displayed"""
        node = self.nodeFromIndex(index)
        plottedTrace = node.content
        plotname = str(value)
        if plotname in self.graphicsViewDict:
            plottedTrace.setGraphicsView(self.graphicsViewDict[plotname]['view'], plotname)
            leftInd = self.indexFromNode(node, col=self.column.name)
            rightInd = self.indexFromNode(node, col=self.column.window)
            self.dataChanged.emit(leftInd, rightInd)
            self.traceModelDataChanged.emit(str(plottedTrace.traceCollection.traceCreation), 'isPlotted', '')
        else:
            return False

    def penChange(self, index, value):
        """plot using the pen specified by value"""
        node = self.nodeFromIndex(index)
        plottedTrace = node.content
        if len(plottedTrace.traceCollection.x) != 0:
            plottedTrace.plot(value)
            leftInd  = self.indexFromNode(node, col=self.column.name)
            rightInd = self.indexFromNode(node, col=self.column.pen)
            self.dataChanged.emit(leftInd, rightInd)
            self.traceModelDataChanged.emit(str(plottedTrace.traceCollection.traceCreation), 'isPlotted', '')
            return True
        else:
            return False

    def checkboxChange(self, index, value):
        """Plot or unplot the plottedTrace at the given index based on the checkbox"""
        node = self.nodeFromIndex(index)
        plottedTrace = node.content
        success = False
        if (value == QtCore.Qt.Unchecked) and (plottedTrace.curvePen > 0):
            plottedTrace.plot(0) #unplot if unchecked
            success=True
        elif len(plottedTrace.traceCollection.x) != 0: #Make sure the x array isn't empty before trying to plot
            plottedTrace.plot(-1)
            success=True
        if success:
            leftInd = self.indexFromNode(node, col=self.column.name)
            rightInd = self.indexFromNode(node, col=self.column.pen)
            self.dataChanged.emit(leftInd, rightInd)
            self.emitParentDataChanged(node, leftCol=self.column.name, rightCol=self.column.name)
            self.traceModelDataChanged.emit(str(plottedTrace.traceCollection.traceCreation), 'isPlotted', '')
        return success

    def emitParentDataChanged(self, node, leftCol, rightCol):
        """Recursively tell parent nodes to update data from leftCol to rightCol"""
        if node is self.root or node.parent is self.root:
            return None
        leftInd = self.indexFromNode(node.parent, col=leftCol)
        rightInd = self.indexFromNode(node.parent, col=rightCol)
        self.dataChanged.emit(leftInd, rightInd)
        self.emitParentDataChanged(node.parent, leftCol, rightCol)

    def commentChange(self, index, value):
        """change the comment and resave the trace"""
        node = self.nodeFromIndex(index)
        dataNode = self.getFirstDataNode(node)
        if dataNode:
            traceCollection = dataNode.content.traceCollection
            comment = (value if api2 else value.toString()) if isinstance(value, QtCore.QVariant) else value
            comment = str(comment)

            if not comment == traceCollection.comment: #only update if comment has changed
                traceCollection.comment = comment
                alreadySaved = traceCollection.saved
                traceCollection.save()
                self.traceModelDataChanged.emit(str(traceCollection.traceCreation), 'comment', comment)
                leftCol=self.column.comment
                rightCol=self.column.comment

                if not alreadySaved: #if this is the first time the trace is saved, update entire collection and emit filename change signal
                    self.onSaveUnsavedTrace(dataNode)
                    self.traceModelDataChanged.emit(str(traceCollection.traceCreation), 'filename', traceCollection.filename)
                    leftCol=0
                    rightCol=self.numColumns-1

                #entire collection is updated if the data node is not a top level node
                topLeftInd = self.indexFromNode(dataNode if dataNode.parent is self.root else dataNode.parent.children[0], col=leftCol)
                bottomRightInd = self.indexFromNode(dataNode if dataNode.parent is self.root else dataNode.parent.children[-1], col=rightCol)
                self.dataChanged.emit(topLeftInd, bottomRightInd)
                self.emitParentDataChanged(dataNode, leftCol, rightCol)
                return True
            return False

    def categoryCheckboxChange(self, index, value):
        """Check or uncheck the filename category of a set of traces"""
        categoryNode = self.nodeFromIndex(index)
        dataNodes = self.getDataNodes(categoryNode)
        if not dataNodes:
            return False
        for dataNode in dataNodes:
            dataIndex = self.indexFromNode(dataNode)
            self.checkboxChange(dataIndex, value) #change each data node checkbox
        ind = self.indexFromNode(categoryNode, col=self.column.name)
        self.dataChanged.emit(ind, ind)
        self.traceModelDataChanged.emit(str(dataNode.content.traceCollection.traceCreation), 'isPlotted', '')
        return True

    def addTrace(self, trace):
        """add a trace to the model"""
        node=self.addNode(trace)
        key = str(trace.traceCollection.traceCreation)
        if key not in self.traceDict:
            self.traceDict[key] = self.getTopNode(node)

    def nodeFromContent(self, trace):
        """Use traceDict to efficiently find node from trace"""
        key = str(trace.traceCollection.traceCreation)
        if key in self.traceDict:
            node=self.traceDict[key]
            for dataNode in self.getDataNodes(node):
                if dataNode.content is trace:
                    return dataNode
        return None

    def removeNode(self, node):
        """Recursively remove the node from the model, unplotting all connected traces"""
        if node.nodeType == nodeTypes.data:
            trace = node.content
            if trace.curvePen!=0:
                trace.plot(0)
            super(TraceModel,self).removeNode(node)
            key = str(node.content.traceCollection.traceCreation)
            self.traceRemoved.emit(key)
            if key in self.traceDict:
                del self.traceDict[key]
        elif node.nodeType == nodeTypes.category:
            for childNode in node.children:
                self.removeNode(childNode) #recursive
            super(TraceModel,self).removeNode(node)

    def onSaveUnsavedTrace(self, dataNode):
        """rename the category associated with dataNode, if any"""
        categoryNode = dataNode.parent
        if categoryNode != self.root:
            self.nodeDict.pop(categoryNode.id)
            newName = dataNode.content.traceCollection.fileleaf #new name is the base filename
            categoryNode.content = newName
            categoryNode.id = newName
            self.nodeDict[newName] = categoryNode
            for node in categoryNode.children:
                trace = node.content
                trace.category = newName #rename node category
                self.nodeDict.pop(node.id)
                node.id = newName + '_' + trace.name #rename the node id
                self.nodeDict[node.id] = node

    def isDataNode(self, index):
        """check if index refers to a data node"""
        return self.nodeFromIndex(index).nodeType==nodeTypes.data

    @QtCore.pyqtSlot(str, str, str)
    def onMeasurementModelDataChanged(self, traceCreation, changeType, data):
        """Trace data changed via MeasurementTableModel. Update model."""
        traceCreation = str(traceCreation)
        changeType = str(changeType)
        data=str(data)
        node = self.traceDict.get(traceCreation)
        if node:
            if changeType=='comment':
                comment = data
                if node.children and node.children[0].content.traceCollection.comment != comment:
                    self.commentChange(self.indexFromNode(node.children[0]), comment)
            elif changeType=='isPlotted':
                topLeftInd = self.indexFromNode(node.parent.children[0], col=self.column.name)
                bottomRightInd = self.indexFromNode(node.parent.children[-1], col=self.column.name)
                self.dataChanged.emit(topLeftInd,bottomRightInd)
                parentInd = self.indexFromNode(node.parent, col=self.column.name)
                self.dataChanged.emit(parentInd, parentInd)
