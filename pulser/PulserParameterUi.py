# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.firstNotNone import firstNotNone
from modules.Expression import Expression
from modules.GuiAppearance import restoreGuiState, saveGuiState
from gui.ExpressionValue import ExpressionValue
from _functools import partial
from _collections import defaultdict
from pulseProgram import PulseProgram

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalParameterUi.ui')

class PulserParameter(ExpressionValue):
    def __init__(self, name=None, address=0, value=None, string=None, onChange=None, bitmask=0xffffffffffffffff, shift=0, encoding=None, globalDict=None):
        super(PulserParameter, self).__init__(name=name, globalDict=globalDict)
        self.address = address
        if onChange is not None:
            self.observable.subscribe(onChange)
        self.value = value
        self.string = string
        self.bitmask = bitmask
        self.shift = shift
        self.encoding = encoding

class PulserParameterTableModel( QtCore.QAbstractTableModel ):
    expression = Expression()
    backgroundLookup = {True:QtGui.QColor(QtCore.Qt.green).lighter(175), False:QtGui.QColor(QtCore.Qt.white)}
    def __init__(self, parameterList, parent=None):
        super(PulserParameterTableModel, self).__init__(parent)
        self.parameterList = parameterList
        self.headerLookup = ['Name', 'Value']
        self.dataLookup =  { (QtCore.Qt.DisplayRole,0): lambda row: self.parameterList[row].name,
                             (QtCore.Qt.DisplayRole,1): lambda row: str(self.parameterList[row].value),
                             (QtCore.Qt.EditRole,1): lambda row: self.parameterList[row].string,
                             (QtCore.Qt.BackgroundRole,1): lambda row: self.backgroundLookup[self.parameterList[row].hasDependency]
                     }
        self.setDataLookup = {
                             (QtCore.Qt.EditRole,1): lambda index, value: self.setValue( index, value ),
                             (QtCore.Qt.UserRole,1): lambda index, value: self.setStrValue( index, value ),
                              }

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.parameterList)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 2
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None

    def setData(self,index, value, role):
        return self.setDataLookup.get( (role,index.column() ), lambda index, value: False)(index, value)
                      
    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable if index.column()==1 else QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole) and (orientation == QtCore.Qt.Horizontal): 
            return self.headerLookup[section]
        return None #QtCore.QVariant()
 
    def setValue(self, index, value):
        param = self.parameterList[index.row()]
        param.value = value
        return True
         
    def setStrValue(self, index, strValue):
        self.parameterList[index.row()].string = strValue
        return True
        

class PulserParameterUi(UiForm,UiBase):
    def __init__(self, pulser, config, globalDict=None, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.isSetup = False
        self.globalDict = firstNotNone( globalDict, dict() )
        self.config = config
        self.pulser = pulser
        oldValues = self.config.get( 'PulserParameterValues', dict() )
        self.parameterList = list()
        pulserconfig = self.pulser.pulserConfiguration()
        self.currentWireValues = defaultdict( lambda: 0 )
        for index, extendedWireIn in enumerate(pulserconfig.extendedWireIns):
            value, string = oldValues.get(extendedWireIn.name,(extendedWireIn.default,None))
            self.parameterList.append( PulserParameter(name=extendedWireIn.name, address=extendedWireIn.address, value=value, string=string,
                                                       bitmask=extendedWireIn.bitmask, shift=extendedWireIn.shift, encoding=extendedWireIn.encoding,
                                                       onChange=partial(self.onChange,extendedWireIn,index), globalDict=self.globalDict))
    
    def setupUi(self):
        UiForm.setupUi(self, self)
        self.tableModel = PulserParameterTableModel(self.parameterList)
        self.tableView.setModel( self.tableModel )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate) 
        restoreGuiState( self, self.config.get('PulserParameterUi.guiState'))
        self.isSetup = True
        
    def saveConfig(self):
        self.config['PulserParameterValues'] = dict( (p.name,(p.value,p.string if p.hasDependency else None)) for p in self.parameterList )
        self.config['PulserParameterUi.guiState'] = saveGuiState(self)
    
    def onChange(self, extendedWireParameter, index, event ):
        encoded = PulseProgram.encode( event.value, extendedWireParameter.encoding )
        self.currentWireValues[extendedWireParameter.address] = ((self.currentWireValues[extendedWireParameter.address] & ~extendedWireParameter.bitmask) | extendedWireParameter.bitmask & (encoded << (extendedWireParameter.shift)) )
        self.pulser.setExtendedWireIn( extendedWireParameter.address, self.currentWireValues[extendedWireParameter.address] )
        if self.isSetup and event.origin!='value':
            self.tableModel.dataChanged.emit( self.tableModel.createIndex(index,1), self.tableModel.createIndex(index,1))
        