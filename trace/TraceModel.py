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
        self.columnNames = ['name','pen','window','comment']
        self.numColumns = len(self.columnNames)
        self.column = enum(*self.columnNames)
        unsavedBG =  QtGui.QColor(255, 220, 220)
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.name): "Name",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.pen): "Pen    ",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.window): "Window",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.comment): "Comment",
            })
        self.categoryDataLookup.update({
            (QtCore.Qt.CheckStateRole,self.column.name): lambda node: self.isCategoryChecked(node),
            (QtCore.Qt.DisplayRole, self.column.comment): lambda node: node.children[0].content.traceCollection.comment if node.children else None,
            (QtCore.Qt.BackgroundRole, self.column.name): lambda node: None if not node.children else (None if node.children[0].content.traceCollection.saved else unsavedBG),
            (QtCore.Qt.BackgroundRole, self.column.pen): lambda node: None if not node.children else (None if node.children[0].content.traceCollection.saved else unsavedBG),
            (QtCore.Qt.BackgroundRole, self.column.window): lambda node: None if not node.children else (None if node.children[0].content.traceCollection.saved else unsavedBG),
            (QtCore.Qt.BackgroundRole, self.column.comment): lambda node: None if not node.children else (None if node.children[0].content.traceCollection.saved else unsavedBG),
        })
        self.dataLookup.update({
            (QtCore.Qt.DisplayRole,self.column.name): lambda node: node.content.name,
            (QtCore.Qt.CheckStateRole,self.column.name): lambda node: QtCore.Qt.Checked if node.content.curvePen > 0 else QtCore.Qt.Unchecked,
            (QtCore.Qt.DecorationRole,self.column.pen): lambda node: QtGui.QIcon(self.penicons[node.content.curvePen]) if hasattr(node.content, 'curve') and node.content.curve is not None else None,
            (QtCore.Qt.EditRole,self.column.pen): lambda node: node.content.curvePen,
            (QtCore.Qt.DisplayRole,self.column.window): lambda node: node.content.windowName,
            (QtCore.Qt.EditRole,self.column.window): lambda node: node.content.windowName,
            (QtCore.Qt.DisplayRole,self.column.comment): lambda node: node.content.traceCollection.comment,
            (QtCore.Qt.EditRole,self.column.comment): lambda node: node.content.traceCollection.comment,
            (QtCore.Qt.BackgroundRole, self.column.name): lambda node: None if node.content.traceCollection.saved else unsavedBG,
            (QtCore.Qt.BackgroundRole, self.column.pen): lambda node: None if node.content.traceCollection.saved else unsavedBG,
            (QtCore.Qt.BackgroundRole, self.column.window): lambda node: None if node.content.traceCollection.saved else unsavedBG,
            (QtCore.Qt.BackgroundRole, self.column.comment): lambda node: None if node.content.traceCollection.saved else unsavedBG

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
            self.column.comment: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
            }
        self.categoryFlagsLookup = {
            self.column.name: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
            self.column.comment: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
            }

    def isCategoryChecked(self, categoryNode):
        """Determine if category node should be checked or not, based on plot status of children"""
        plottedList = [node.content.curvePen>0 for node in categoryNode.children]
        if not plottedList: return QtCore.Qt.Unchecked
        elif all(plottedList): return QtCore.Qt.Checked
        elif any(plottedList): return QtCore.Qt.PartiallyChecked
        else: return QtCore.Qt.Unchecked

    def choice(self, index):
        """return available plot windows"""
        return self.graphicsViewDict.keys() if index.column()==self.column.window else []

    def setValue(self, index, value):
        """set index EditRole to value"""
        self.setData(index, value, QtCore.Qt.EditRole)

    def windowChange(self, index, value):
        """change the plot window on which the trace is displayed"""
        node = self.nodeFromIndex(index)
        trace = node.content
        plotname = str(value)
        if plotname in self.graphicsViewDict:
            trace.setGraphicsView(self.graphicsViewDict[plotname]['view'], plotname)
            leftInd = self.indexFromNode(node, col=self.column.name)
            rightInd = self.indexFromNode(node, col=self.column.window)
            self.dataChanged.emit(leftInd, rightInd)
            self.traceModelDataChanged.emit(str(trace.traceCollection.traceCreation), 'isPlotted', '')
        else:
            return False

    def penChange(self, index, value):
        """plot using the pen specified by value"""
        node = self.nodeFromIndex(index)
        trace = node.content
        if len(trace.traceCollection.x) != 0:
            trace.plot(value)
            leftInd  = self.indexFromNode(node, col=self.column.name)
            rightInd = self.indexFromNode(node, col=self.column.pen)
            self.dataChanged.emit(leftInd, rightInd)
            self.traceModelDataChanged.emit(str(trace.traceCollection.traceCreation), 'isPlotted', '')
            return True
        else:
            return False

    def checkboxChange(self, index, value):
        """Plot or unplot the trace at the given index based on the checkbox"""
        node = self.nodeFromIndex(index)
        trace = node.content
        success = False
        if (value == QtCore.Qt.Unchecked) and (trace.curvePen > 0):
            trace.plot(0) #unplot if unchecked
            success=True
        elif len(trace.traceCollection.x) != 0: #Make sure the x array isn't empty before trying to plot
            trace.plot(-1)
            success=True
        if success:
            leftInd = self.indexFromNode(node, col=self.column.name)
            rightInd = self.indexFromNode(node, col=self.column.pen)
            self.dataChanged.emit(leftInd, rightInd)
            parentInd = self.indexFromNode(node.parent, col=self.column.name)
            self.dataChanged.emit(parentInd, parentInd)
            self.traceModelDataChanged.emit(str(trace.traceCollection.traceCreation), 'isPlotted', '')
        return success

    def commentChange(self, index, value):
        """change the comment and resave the trace"""
        node = self.nodeFromIndex(index)
        if node.nodeType==nodeTypes.data:
            traceCollection = node.content.traceCollection
            categoryNode = node.parent
        else:
            traceCollection = node.children[0].content.traceCollection if node.children else None
            categoryNode = node
        if traceCollection:
            if isinstance(value, QtCore.QVariant):
                comment = str(value) if api2 else str(value.toString())
            else:
                comment = str(value)
            if not comment == traceCollection.comment:
                traceCollection.comment = comment
                alreadySaved = traceCollection.saved
                traceCollection.save()
                self.traceModelDataChanged.emit(str(traceCollection.traceCreation), 'comment', comment)
                if not alreadySaved:
                    self.onSaveUnsavedTrace(node)
                    self.traceModelDataChanged.emit(str(traceCollection.traceCreation), 'filename', traceCollection.filename)
                    topLeftInd = self.indexFromNode(categoryNode.children[0], col=0)
                    bottomRightInd = self.indexFromNode(categoryNode.children[-1], col=self.numColumns-1)
                    categoryLeftInd = self.indexFromNode(categoryNode, col=0)
                    categoryRightInd = self.indexFromNode(categoryNode, col=self.numColumns-1)
                else:
                    topLeftInd = self.indexFromNode(categoryNode.children[0], col=self.column.comment)
                    bottomRightInd = self.indexFromNode(categoryNode.children[-1], col=self.column.comment)
                    categoryLeftInd = self.indexFromNode(categoryNode, col=self.column.comment)
                    categoryRightInd = self.indexFromNode(categoryNode, col=self.column.comment)
                self.dataChanged.emit(topLeftInd,bottomRightInd)
                self.dataChanged.emit(categoryLeftInd, categoryRightInd)
                return True
        return False

    def categoryCheckboxChange(self, index, value):
        """Check or uncheck the filename category of a set of traces"""
        node = self.nodeFromIndex(index)
        if node.children:
            for childNode in node.children:
                childIndex = self.indexFromNode(childNode)
                self.checkboxChange(childIndex, value)
            ind = self.indexFromNode(node, col=self.column.name)
            self.dataChanged.emit(ind, ind)
            self.traceModelDataChanged.emit(str(node.children[0].content.traceCollection.traceCreation), 'isPlotted', '')
            return True
        else:
            return False

    def addTrace(self, trace):
        """add a trace to the model"""
        node=self.addNode(trace)
        key = str(trace.traceCollection.traceCreation)
        if key not in self.traceDict:
            self.traceDict[key] = node.parent

    def nodeFromContent(self, trace):
        """Use traceDict to efficiently find node from trace"""
        key = str(trace.traceCollection.traceCreation)
        if key in self.traceDict:
            parentNode=self.traceDict[key]
            for childNode in parentNode.children:
                if childNode.content is trace:
                    return childNode
        return None


    def removeNode(self, node):
        """unplots the trace before removing from model"""
        if node.nodeType == nodeTypes.data:
            trace = node.content
            if trace.curvePen!=0:
                trace.plot(0)
            super(TraceModel,self).removeNode(node)
        elif node.nodeType == nodeTypes.category:
            if node.children:
                key = str(node.children[0].content.traceCollection.traceCreation)
                self.traceRemoved.emit(key)
                if key in self.traceDict:
                    del self.traceDict[key]
            for _ in range(node.childCount()):
                childNode = node.children[0]
                trace = childNode.content
                if trace.curvePen!=0:
                    trace.plot(0)
                super(TraceModel,self).removeNode(childNode)
            super(TraceModel,self).removeNode(node)

    def onSaveUnsavedTrace(self, node):
        """rename the category associated with trace"""
        categoryNode = node.parent if node.nodeType==nodeTypes.data else node
        if categoryNode.children:
            self.nodeDict.pop(categoryNode.id)
            newName = categoryNode.children[0].content.traceCollection.fileleaf #new name is the base filename
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
