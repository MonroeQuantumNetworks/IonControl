# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
import functools

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParameterUi.ui')

from MagnitudeSpinBox import MagnitudeSpinBox

class MagnitudeSpinBoxDelegate(QtGui.QItemDelegate):
  
    """
    This class is responsible for the combo box editor in the trace table,
    which is used to select which pen to use in drawing the trace on the plot.
    The pen icons are in the array penicons, which is determined when the delegate
    is constructed.
    """    
    
    def __init__(self):
        """Construct the TraceComboDelegate object, and set the penicons array."""
        QtGui.QItemDelegate.__init__(self)
        
    def createEditor(self, parent, option, index ):
        """Create the combo box editor used to select which pen icon to use.
           The for loop adds each pen icon into the combo box."""
        editor = MagnitudeSpinBox(parent)
        return editor
        
    def setEditorData(self, editor, index):
        print "setEditorData"
        value = index.model().data(index, QtCore.Qt.EditRole) 
        editor.setValue(value)
        editor.valueChanged.connect( functools.partial( index.model().setValue, index.row() ))
        
    def setModelData(self, editor, model, index):
        value = editor.value()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self, editor, option, index ):
        editor.setGeometry(option.rect)


class ExternalParameterControlTableModel( QtCore.QAbstractTableModel ):
    valueChanged = QtCore.pyqtSignal(str, object)
    def __init__(self, controlUi, parameterList=None, parent=None):
        super(ExternalParameterControlTableModel, self).__init__(parent)
        self.parameterList = list()
        self.names = list()
        self.controlUi = controlUi
        
    def setParameterList(self, parameterList):
        self.beginResetModel()
        self.parameterList = parameterList.values()
        self.names = parameterList.keys()
        self.targetValues = [inst.currentValue() for inst in self.parameterList]
        self.externalValues = self.targetValues[:]
        self.toolTips = [None]*len(self.externalValues )
        for index,inst in enumerate(self.parameterList):
            inst.displayValueCallback = functools.partial( self.showValue, index )
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.parameterList)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 3
    
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,0): self.names[index.row()],
                     (QtCore.Qt.DisplayRole,1): str(self.targetValues[index.row()]),
                     (QtCore.Qt.EditRole,1): str(self.targetValues[index.row()]),
                     (QtCore.Qt.DisplayRole,2): str(self.externalValues[index.row()]),
                     (QtCore.Qt.ToolTipRole,2): str(self.toolTips[index.row()]),
                     }.get((role,index.column()),None)
        return None

    def setData(self,index, value, role):
        return { (QtCore.Qt.EditRole,1): functools.partial( self.setValue, index.row(), value ),
                }.get((role,index.column()), lambda: False )() 
                      
    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable if index.column()==1 else QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole) and (orientation == QtCore.Qt.Horizontal): 
            return {
                0: 'Name',
                1: 'Control',
                2: 'External',
                }.get(section)
        return None #QtCore.QVariant()
 
    def showValue(self, index, value, tooltip=None):
        self.externalValues[index] = value
        self.toolTips[index] = tooltip
        leftInd = self.createIndex(index, 2)
        rightInd = self.createIndex(index, 2)
        self.dataChanged.emit(leftInd, rightInd) #Update all 5 columns
            
    def setValue(self, index, value):
        print "setValue", value
        self.targetValues[index] = value
        self.setValueFollowup(index)
        
    def setValueFollowup(self, index):
        print "setValueFollowup", self.parameterList[index].currentValue()
        delay = int( self.parameterList[index].settings.delay.toval('ms') )
        if not self.parameterList[index].setValue( self.targetValues[index] ):
            QtCore.QTimer.singleShot(delay,functools.partial(self.setValueFollowup,index) )


class ControlUi(UiForm,UiBase):
    
    def __init__(self, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.spacerItem = None
        self.myLabelList = list()
        self.myBoxList = list()
        self.myDisplayList = list()
        self.targetValue = dict()
        self.currentValue = dict()
        self.displayWidget = dict()
        self.tagetValue = dict()
    
    def setupUi(self,EnabledParameters,MainWindow):
        UiForm.setupUi(self,MainWindow)
        self.tableModel = ExternalParameterControlTableModel(self)
        self.tableView.setModel( self.tableModel )
        self.tableView.setItemDelegateForColumn(1,MagnitudeSpinBoxDelegate()) 
        self.setupParameters(EnabledParameters)
        
    def setupParameters(self,EnabledParameters):
        print "ControlUi.setupParameters", EnabledParameters
        self.enabledParameters = EnabledParameters
        self.tableModel.setParameterList( self.enabledParameters )
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)        
        

    
