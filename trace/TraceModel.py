# -*- coding: utf-8 -*-
"""
Created on Wed Jan 02 09:53:48 2013

@author: Jonathan Mizrahi

This is the model used with TraceTreeView to view the list of traces in a tree.
"""

from functools import partial

from PyQt4 import QtCore, QtGui
import sip

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
    def __init__(self, traceList, penicons, graphicsViewDict, parent=None, *args): 
        super(TraceModel, self).__init__(traceList, parent, categoriesAttr='category')
        self.penicons = penicons
        self.graphicsViewDict = graphicsViewDict
        self.numColumns = 4
        self.allowDeletion = True
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 0): 'Name',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 1): 'Plot',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 2): 'Window',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 3): 'Comment',
            })
        self.categoryDataLookup.update({
            (QtCore.Qt.CheckStateRole,0): lambda node: self.isCategoryChecked(node)
        })
        self.dataLookup.update({
            (QtCore.Qt.DisplayRole,0): lambda node: node.content.name,
            (QtCore.Qt.CheckStateRole,0): lambda node: QtCore.Qt.Checked if node.content.curvePen > 0 else QtCore.Qt.Unchecked,
            (QtCore.Qt.DecorationRole,1): lambda node: QtGui.QIcon(self.penicons[node.content.curvePen]) if hasattr(node.content, 'curve') and node.content.curve is not None else None,
            (QtCore.Qt.BackgroundColorRole,1): lambda node: QtGui.QColor(QtCore.Qt.white) if not (hasattr(node.content, 'curve') and node.content.curve is not None) else None,
            (QtCore.Qt.EditRole,1): lambda node: node.content.curvePen,
            (QtCore.Qt.DisplayRole,2): lambda node: node.content.windowName,
            (QtCore.Qt.EditRole,2): lambda node: node.content.windowName,
            (QtCore.Qt.DisplayRole,3): lambda node: node.content.trace.comment,
            (QtCore.Qt.EditRole,3): lambda node: node.content.trace.comment
            })
        self.setDataLookup.update({
            (QtCore.Qt.CheckStateRole,0): lambda index, value: self.modelChange(index, value, 'checkbox'),
            (QtCore.Qt.EditRole,1): lambda index, value: self.modelChange(index, value, 'plot'),
            (QtCore.Qt.EditRole,2): lambda index, value: self.modelChange(index, value, 'window'),
            (QtCore.Qt.EditRole,3): lambda index, value: self.modelChange(index, value, 'comment')
            })
        self.categorySetDataLookup.update({
            (QtCore.Qt.CheckStateRole,0): lambda index, value: self.setCategoryCheckbox(index, value)
        })
        self.flagsLookup = {
            0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
            1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            2: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            3: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
            }
        self.categoryFlagsLookup = {
            0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
            }

    def isCategoryChecked(self, categoryNode):
        """Determine if category node should be checked or not, based on plot status of children"""
        plottedList = [node.content.curvePen>0 for node in categoryNode.children]
        if not plottedList: return QtCore.Qt.Unchecked
        elif all(plottedList): return QtCore.Qt.Checked
        elif any(plottedList): return QtCore.Qt.PartiallyChecked
        else: return QtCore.Qt.Unchecked

    def choice(self, index):
        return self.graphicsViewDict.keys() if index.column()==2 else []

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
        return success

    def checkboxChange(self, trace, value):
        """Plot or unplot the trace at the given index based on the checkbox"""
        if (value == QtCore.Qt.Unchecked) and (trace.curvePen > 0):
            trace.plot(0) #unplot if unchecked
            return True
        elif len(trace.trace.x) != 0: #Make sure the x array isn't empty before trying to plot
            trace.plot(-1)
            return True
        else:
            return False

    def penChange(self, trace, value):
        """plot using the pen specified by value"""
        if len(trace.trace.x) != 0:
            trace.plot(value)
            return True
        else:
            return False

    def commentChange(self, trace, value):
        """resave the trace with the new comment"""
        comment = value if api2 else str(value.toString())
        if not comment == trace.trace.comment:
            trace.trace.comment = comment
            trace.trace.save()
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

    def addTrace(self, trace):
        """add a trace to the model"""
        self.addNode(trace, trace.name)

    def removeNode(self, node):
        """unplots the trace before removing from model"""
        if node.nodeType == nodeTypes.data:
            trace = node.content
            if trace.curvePen!=0:
                trace.plot(0)
            super(TraceModel,self).removeNode(node)
        elif node.nodeType == nodeTypes.category:
            for _ in range(node.childCount()):
                childNode = node.children[0]
                trace = childNode.content
                if trace.curvePen!=0:
                    trace.plot(0)
                super(TraceModel,self).removeNode(childNode)
            super(TraceModel,self).removeNode(node)

    def onSaveUnsavedTrace(self, node):
        """rename the category associated with trace"""
        categoryNode = node.parent
        self.nodeDict.pop(categoryNode.id)
        newName = node.content.trace.fileleaf
        categoryNode.content = newName
        categoryNode.id = newName
        self.nodeDict[newName] = categoryNode
        for node in categoryNode.children:
            node.content.category = node.content.trace.fileleaf


