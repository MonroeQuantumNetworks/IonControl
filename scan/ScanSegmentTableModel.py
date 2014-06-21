from PyQt4 import QtCore
from functools import partial

from scan.CountEvaluation import EvaluationAlgorithms


class ScanSegmentTableModel( QtCore.QAbstractTableModel):
    dataChanged = QtCore.pyqtSignal( object, object )
    headerDataLookup = ['Start','Stop','Center','Span', 'steps', 'stepsize' ]
    def __init__(self, updateSaveStatus, scanSegments=None, parent=None):
        super(ScanSegmentTableModel, self).__init__(parent)
        self.scanSegmentList = scanSegments if scanSegments is not None else list()
        self.updateSaveStatus = updateSaveStatus
        self.setDataLookup =  {  (QtCore.Qt.EditRole,0): partial( self.setField, 'start'),
                                 (QtCore.Qt.EditRole,1): partial( self.setField, 'stop'),
                                 (QtCore.Qt.EditRole,2): partial( self.setField, 'center'),
                                 (QtCore.Qt.EditRole,3): partial( self.setField, 'span'),
                                 (QtCore.Qt.EditRole,4): partial( self.setField, 'steps'),
                                 (QtCore.Qt.EditRole,5): partial( self.setField, 'stepsize'),
                                }
        self.dataLookup = {  (QtCore.Qt.DisplayRole,0): lambda self, column: self.scanSegmentList[column].start,
                             (QtCore.Qt.DisplayRole,1): lambda self, column: self.scanSegmentList[column].stop,
                             (QtCore.Qt.DisplayRole,2): lambda self, column: self.scanSegmentList[column].center,
                             (QtCore.Qt.DisplayRole,3): lambda self, column: self.scanSegmentList[column].span,
                             (QtCore.Qt.DisplayRole,4): lambda self, column: self.scanSegmentList[column].steps,
                             (QtCore.Qt.DisplayRole,5): lambda self, column: self.scanSegmentList[column].stepsize,
                             (QtCore.Qt.EditRole,0):    lambda self, column: self.scanSegmentList[column].start,
                             (QtCore.Qt.EditRole,1):    lambda self, column: self.scanSegmentList[column].stop,
                             (QtCore.Qt.EditRole,2):    lambda self, column: self.scanSegmentList[column].center,
                             (QtCore.Qt.EditRole,3):    lambda self, column: self.scanSegmentList[column].span,
                             (QtCore.Qt.EditRole,4):    lambda self, column: self.scanSegmentList[column].steps,
                             (QtCore.Qt.EditRole,5):    lambda self, column: self.scanSegmentList[column].stepsize,
                             }

    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 6
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return len(self.scanSegmentList)
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.row()),lambda self, row: None)(self,index.column())
        return None
        
    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return str(section)
            elif (orientation == QtCore.Qt.Vertical): 
                return self.headerDataLookup[section]
        return None 
           
    def setValue(self, index, value):
        self.setData( index, value, QtCore.Qt.EditRole)
                
    def setField(self, fieldname, index, value):
        setattr( self.scanSegmentList[index.column()], fieldname, value )
        self.dataChanged.emit( index, index )
        return True
    
    def setScanList(self, scanlist):
        self.beginResetModel()
        self.scanSegmentList = scanlist
        self.endResetModel()