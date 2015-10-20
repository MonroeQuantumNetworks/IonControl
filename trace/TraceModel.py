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
from uiModules.CategoryTree import CategoryTreeModel

api2 = sip.getapi("QVariant")==2

class TraceComboDelegate(QtGui.QItemDelegate):
    
    """
    This class is a delegate of the trace tree view, responsible for the combo box editor in the trace tree.
    
    The combo box editor is used to select which pen to use in drawing the
    trace on the plot. The available pen icons to use are in the array penicons,
    which is determined when the delegate is constructed.
    
    methods:
    __init__: constructor for TraceComboDelegate. Construct the parent, and set the penicons array.
    createEditor: create the combo box editor, and add in all the icons.
    
    The following methods are required reimplementations if QItemDelegate methods:
    createEditor(self,parent, option, index): Create the combo box editor used to select the pen icon.
    setEditorData(self,editor, index): Supply data to the editor from the model.
    setModelData(self,editor, model, index): Supply data to the model from the editor.
    updateEditorGeometry(self,editor, option, index): Set the size of the combo box appropriately.
    """    
    
    def __init__(self, penicons):
        """Construct the TraceComboDelegate object, and set the penicons array."""
        QtGui.QItemDelegate.__init__(self)
        self.penicons = penicons        
        
    def createEditor(self,parent, option, index ):
        """Required. Create the combo box editor used to select pen icon.
        
           The for loop adds each pen icon into the combo box."""
        editor = QtGui.QComboBox(parent);
        #for icon, string in zip(self.penicons, ["{0}".format(i) for i in range(0,len(self.penicons))] ):
        for icon, string in zip(self.penicons, ['']*len(self.penicons) ):
            editor.addItem( icon, string )
        return editor

    def setEditorData(self,editor, index):
        """Required. Supply data to the editor from the model."""
        value = index.model().data(index, QtCore.Qt.EditRole) 
        editor.setCurrentIndex(value)
        
    def setModelData(self,editor, model, index):
        """Required. Supply data to the model from the editor."""
        value = editor.currentIndex()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self,editor, option, index ):
        """Required. Set the size of the combo box appropriately."""
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
        super(TraceModel, self).__init__(traceList, parent)
        self.penicons = penicons
        self.traceList = traceList
        self.graphicsViewDict = graphicsViewDict
        self.numColumns = 6
        self.allowDeletion = True
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 1): 'Plot',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 2): 'Name',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 3): 'Comment',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 4): 'Filename',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 5):  'Window'
            })
        self.dataLookup.update({
            (QtCore.Qt.DisplayRole,2): lambda node: ", ".join([str(node.content.trace.name), str(node.content.name)]),
            (QtCore.Qt.DisplayRole,3): lambda node: node.content.trace.comment,
            (QtCore.Qt.DisplayRole,4): lambda node: getattr( node.content.trace, 'fileleaf', None ),
            (QtCore.Qt.DisplayRole,5): lambda node: node.content.windowName,
            (QtCore.Qt.EditRole,5): lambda node: node.content.windowName,
            (QtCore.Qt.CheckStateRole,0): lambda node: QtCore.Qt.Checked if node.content.curvePen > 0 else QtCore.Qt.Unchecked,
            (QtCore.Qt.DecorationRole,1): lambda node: QtGui.QIcon(self.penicons[node.content.curvePen]) if hasattr(node.content, 'curve') and node.content.curve is not None else None,
            (QtCore.Qt.BackgroundColorRole,1): lambda node: QtGui.QColor(QtCore.Qt.white) if not (hasattr(node.content, 'curve') and node.content.curve is not None) else None,
            (QtCore.Qt.EditRole,1): lambda node: node.content.curvePen,
            (QtCore.Qt.EditRole,3): lambda node: node.content.trace.comment
            })
        self.setDataLookup.update({
            (QtCore.Qt.CheckStateRole,0): lambda index, value: self.checkboxChange(index, value, 'checkbox'),
            (QtCore.Qt.EditRole,1): lambda index, value: self.penChange(index, value, 'pen'),
            (QtCore.Qt.EditRole,3): lambda index, value: self.commentChange(index, value, 'comment'),
            (QtCore.Qt.EditRole,5): lambda index, value: self.plotChange(index, value, 'plot')
            })
        self.flagsLookup = {
            0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
            1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            3: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            5: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
            }

    def choice(self, index):
        return self.graphicsViewDict.keys() if index.column()==5 else []

    def modelChange(self, index, value=None, changeType='update'):
        node = self.nodeFromIndex(index)
        trace = node.content
        success = {'checkbox' : self.checkboxChange,
                   'pen'      : self.plotChange,
                   'comment'  : self.commentChange,
                   'plot'     : self.plotChange,
                   'update'   : lambda trace, value:True
                   }[changeType](trace, value)
        if success:
            leftInd = self.createIndex(node.row, 0, trace)
            rightInd = self.createIndex(node.row, self.numColumns-1, trace)
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

    def penChange(self, trace, value):
        """plot using the pen specified by value"""
        if trace.trace.x:
            trace.plot(value)
            return True

    def commentChange(self, trace, value):
        """resave the trace with the new comment"""
        comment = value if api2 else str(value.toString())
        if not comment == trace.trace.comment:
            trace.trace.comment = comment
            trace.trace.save()
            return True

    def plotChange(self, trace, value):
        """change the plot on which the trace is displayed"""
        plotname = str(value)
        if plotname in self.graphicsViewDict:
            trace.setGraphicsView( self.graphicsViewDict[plotname]['view'], plotname )
            return True