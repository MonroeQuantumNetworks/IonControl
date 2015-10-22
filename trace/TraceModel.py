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

class TraceComboDelegate(QtGui.QItemDelegate):
    """
    Class for combo box editor to select what trace color to use

    Args:
        penicons (list[Qicon]): list of icons to select trace color"""
    def __init__(self, penicons):
        QtGui.QItemDelegate.__init__(self)
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
        parent (QtCore.QObject): parent QObject
    """
    traceDataChanged = QtCore.pyqtSignal(str, str, str) #string with trace creation date, change type, value
    def __init__(self, traceList, penicons, graphicsViewDict, parent=None, *args): 
        super(TraceModel, self).__init__(traceList, parent, categoriesAttr='category')
        self.traceList = traceList
        self.penicons = penicons
        self.graphicsViewDict = graphicsViewDict
        self.allowDeletion = True
        self.columnNames = ['name','plot','window','comment']
        self.numColumns = len(self.columnNames)
        self.column = enum(*self.columnNames)
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.name): self.columnNames[self.column.name].capitalize(),
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.plot): self.columnNames[self.column.plot].capitalize(),
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.window): self.columnNames[self.column.window].capitalize(),
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.comment): self.columnNames[self.column.comment].capitalize(),
            })
        self.categoryDataLookup.update({
            (QtCore.Qt.CheckStateRole,self.column.name): lambda node: self.isCategoryChecked(node),
            (QtCore.Qt.DisplayRole, self.column.comment): lambda node: node.children[0].content.traceCollection.comment if node.children else None
        })
        self.dataLookup.update({
            (QtCore.Qt.DisplayRole,self.column.name): lambda node: node.content.name,
            (QtCore.Qt.CheckStateRole,self.column.name): lambda node: QtCore.Qt.Checked if node.content.curvePen > 0 else QtCore.Qt.Unchecked,
            (QtCore.Qt.DecorationRole,self.column.plot): lambda node: QtGui.QIcon(self.penicons[node.content.curvePen]) if hasattr(node.content, 'curve') and node.content.curve is not None else None,
            (QtCore.Qt.BackgroundColorRole,self.column.plot): lambda node: QtGui.QColor(QtCore.Qt.white) if not (hasattr(node.content, 'curve') and node.content.curve is not None) else None,
            (QtCore.Qt.EditRole,self.column.plot): lambda node: node.content.curvePen,
            (QtCore.Qt.DisplayRole,self.column.window): lambda node: node.content.windowName,
            (QtCore.Qt.EditRole,self.column.window): lambda node: node.content.windowName,
            (QtCore.Qt.DisplayRole,self.column.comment): lambda node: node.content.traceCollection.comment,
            (QtCore.Qt.EditRole,self.column.comment): lambda node: node.content.traceCollection.comment
            })
        self.setDataLookup.update({
            (QtCore.Qt.CheckStateRole,self.column.name): lambda index, value: self.modelChange(index, value, 'checkbox'),
            (QtCore.Qt.EditRole,self.column.plot): lambda index, value: self.modelChange(index, value, 'plot'),
            (QtCore.Qt.EditRole,self.column.window): lambda index, value: self.modelChange(index, value, 'window'),
            (QtCore.Qt.EditRole,self.column.comment): lambda index, value: self.modelChange(index, value, 'comment')
            })
        self.categorySetDataLookup.update({
            (QtCore.Qt.CheckStateRole,self.column.name): lambda index, value: self.setCategoryCheckbox(index, value),
            (QtCore.Qt.EditRole,self.column.comment): lambda index, value: self.setCategoryComment(index, value)
        })
        self.flagsLookup = {
            self.column.name: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
            self.column.plot: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
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
        return self.graphicsViewDict.keys() if index.column()==self.column.window else []

    def setValue(self, index, value):
        self.setData(index, value, QtCore.Qt.EditRole)

    def modelChange(self, index, value=None, changeType='update'):
        node = self.nodeFromIndex(index)
        trace = node.content
        success = {'checkbox' : self.checkboxChange,
                   'plot'      : self.penChange,
                   'comment'  : self.commentChange,
                   'window'     : self.plotChange,
                   'update'   : lambda trace, value:True
                   }[changeType](trace, value)
        if success:
            leftInd = self.createIndex(node.row, 0, node)
            rightInd = self.createIndex(node.row, self.numColumns-1, node)
            self.dataChanged.emit(leftInd, rightInd)
            if (changeType=='checkbox') or (changeType=='window'):
                self.traceDataChanged.emit(str(trace.traceCollection.traceCreation), 'isPlotted', '')
            elif changeType=='comment':
                self.traceDataChanged.emit( str(trace.traceCollection.traceCreation), 'comment', str(value) if api2 else str( value.toString() ) )
        return success

    def checkboxChange(self, trace, value):
        """Plot or unplot the trace at the given index based on the checkbox"""
        if (value == QtCore.Qt.Unchecked) and (trace.curvePen > 0):
            trace.plot(0) #unplot if unchecked
            return True
        elif len(trace.traceCollection.x) != 0: #Make sure the x array isn't empty before trying to plot
            trace.plot(-1)
            return True
        else:
            return False

    def penChange(self, trace, value):
        """plot using the pen specified by value"""
        if len(trace.traceCollection.x) != 0:
            trace.plot(value)
            return True
        else:
            return False

    def commentChange(self, trace, value):
        """resave the trace with the new comment"""
        comment = value if api2 else str(value.toString())
        traceCollection = trace.traceCollection
        if not comment == traceCollection.comment:
            traceCollection.comment = comment
            alreadySaved = traceCollection.saved
            traceCollection.save()
            if not alreadySaved:
                node = self.nodeFromContent(trace)
                self.onSaveUnsavedTrace(node)
                self.traceDataChanged.emit(str(traceCollection.traceCreation), 'filename', traceCollection.filename)
                parentIndex = self.indexFromNode(node.parent)
                self.modelChange(parentIndex)
            return True
        else:
            return False

    def plotChange(self, trace, value):
        """change the plot on which the trace is displayed"""
        plotname = str(value)
        if plotname in self.graphicsViewDict:
            trace.setGraphicsView( self.graphicsViewDict[plotname]['view'], plotname )
            return True
        else:
            return False

    def setCategoryCheckbox(self, index, value):
        """Check or uncheck the filename category of a set of traces"""
        node = self.nodeFromIndex(index)
        if node.children:
            for childNode in node.children:
                trace=childNode.content
                success=self.checkboxChange(trace, value)
                if success:
                    leftInd = self.createIndex(childNode.row, 0, childNode)
                    rightInd = self.createIndex(childNode.row, self.numColumns-1, childNode)
                    self.dataChanged.emit(leftInd, rightInd)
            leftInd = self.createIndex(node.row, 0, node)
            rightInd = self.createIndex(node.row, self.numColumns-1, node)
            self.dataChanged.emit(leftInd, rightInd)
            return True
        else:
            return False

    def setCategoryComment(self, index, value):
        """Set the comment from the category level"""
        node = self.nodeFromIndex(index)
        if node.children:
            for childNode in node.children:
                trace=childNode.content
                success=self.commentChange(trace, value)
                if success:
                    leftInd = self.createIndex(childNode.row, 0, childNode)
                    rightInd = self.createIndex(childNode.row, self.numColumns-1, childNode)
                    self.dataChanged.emit(leftInd, rightInd)
            leftInd = self.createIndex(node.row, 0, node)
            rightInd = self.createIndex(node.row, self.numColumns-1, node)
            self.dataChanged.emit(leftInd, rightInd)
            return True
        else:
            return False


    def addTrace(self, trace):
        """add a trace to the model"""
        node = self.addNode(trace)
        self.traceList.append(trace)
        trace.id = node.id #Add an id to the trace that matches the node id

    def removeNode(self, node):
        """unplots the trace before removing from model"""
        if node.nodeType == nodeTypes.data:
            trace = node.content
            if trace.curvePen!=0:
                trace.plot(0)
            self.traceList.remove(trace)
            super(TraceModel,self).removeNode(node)
        elif node.nodeType == nodeTypes.category:
            for _ in range(node.childCount()):
                childNode = node.children[0]
                trace = childNode.content
                if trace.curvePen!=0:
                    trace.plot(0)
                self.traceList.remove(trace)
                super(TraceModel,self).removeNode(childNode)
            super(TraceModel,self).removeNode(node)

    def onSaveUnsavedTrace(self, node):
        """rename the category associated with trace"""
        categoryNode = node.parent
        self.nodeDict.pop(categoryNode.id)
        newName = node.content.traceCollection.fileleaf
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