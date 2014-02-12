# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
import logging

from PyQt4 import QtCore
import sip

from pulseProgram.VariableDictionary import CyclicDependencyException


api2 = sip.getapi("QVariant")==2

class VariableTableModel(QtCore.QAbstractTableModel):
    flagsLookup = [ QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable |  QtCore.Qt.ItemIsEnabled,
                    QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
                    QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                    QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                    QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled ]
    headerDataLookup = ['use','variable','value','encoding','evaluated']
    def __init__(self, variabledict, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.variabledict = variabledict
        self.dataLookup = {  (QtCore.Qt.CheckStateRole,0): lambda var: QtCore.Qt.Checked if var.enabled else QtCore.Qt.Unchecked,
                             (QtCore.Qt.DisplayRole,1):    lambda var: var.name,
                             (QtCore.Qt.DisplayRole,2):    lambda var: str(var.strvalue if hasattr(var,'strvalue') else var.value),
                             (QtCore.Qt.DisplayRole,3):    lambda var: str(var.encoding),
                             (QtCore.Qt.DisplayRole,4):    lambda var: str(var.value),
                             (QtCore.Qt.EditRole,2):       lambda var: str(var.strvalue if hasattr(var,'strvalue') else var.value),
                             (QtCore.Qt.EditRole,3):       lambda var: str(var.encoding),
                             }
        self.setDataLookup ={    (QtCore.Qt.CheckStateRole,0): self.setVarEnabled,
                                 (QtCore.Qt.EditRole,2):       self.setDataValue,
                                 (QtCore.Qt.EditRole,3):       self.setDataEncoding,
                                }

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variabledict) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 5
 
    def data(self, index, role): 
        if index.isValid():
            var = self.variabledict.at(index.row())
            return self.dataLookup.get((role,index.column()),lambda var: None)(var)
        return None
        
    def setDataValue(self, index, value):
        try:
            strvalue = str(value if api2 else str(value.toString()))
            updatednames = self.variabledict.setStrValueIndex(index.row(),strvalue)
            for name in updatednames:
                index = self.variabledict.index(name)
                self.dataChanged.emit( self.createIndex(index,0), self.createIndex(index,4) )
            return True
        except CyclicDependencyException as e:
            logger = logging.getLogger(__name__)
            logger.error( "Cyclic dependency {0}".format(str(e)) )
            return False           
        except KeyError as e:
            logger = logging.getLogger(__name__)
            logger.error( "Expression '{0}' cannot be evaluated {1}".format(value.toString(),e.message) )
            return False
        except Exception:
            logger = logging.getLogger(__name__)
            logger.error( "No match for {0}".format(value.toString()) )
            return False
        
    def recalculateDependent(self, name):
        updatednames = self.variabledict.recalculateDependent(name)
        for name in updatednames:
            index = self.variabledict.index(name)
            self.dataChanged.emit( self.createIndex(index,0), self.createIndex(index,4) )
        
    def setDataEncoding(self,index, value):
        value = str(value.toString())
        self.variabledict.setEncodingIndex(index.row(), value)
        return True
        
    def setVarEnabled(self,index,value):
        self.variabledict.setEnabledIndex(index.row(), value == QtCore.Qt.Checked)
        return True      

    def setData(self,index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)

    def flags(self, index ):
        return self.flagsLookup[index.column()]

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None #QtCore.QVariant()
        
