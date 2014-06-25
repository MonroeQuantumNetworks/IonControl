from PyQt4 import QtCore, QtGui
from functools import partial

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
        self.dataLookup = {  (QtCore.Qt.DisplayRole,0): lambda self, column: str(self.scanSegmentList[column].start),
                             (QtCore.Qt.DisplayRole,1): lambda self, column: str(self.scanSegmentList[column].stop),
                             (QtCore.Qt.DisplayRole,2): lambda self, column: str(self.scanSegmentList[column].center),
                             (QtCore.Qt.DisplayRole,3): lambda self, column: str(self.scanSegmentList[column].span),
                             (QtCore.Qt.DisplayRole,4): lambda self, column: str(self.scanSegmentList[column].steps),
                             (QtCore.Qt.DisplayRole,5): lambda self, column: str(self.scanSegmentList[column].stepsize),
                             (QtCore.Qt.EditRole,0):    lambda self, column: str(self.scanSegmentList[column].start),
                             (QtCore.Qt.EditRole,1):    lambda self, column: str(self.scanSegmentList[column].stop),
                             (QtCore.Qt.EditRole,2):    lambda self, column: str(self.scanSegmentList[column].center),
                             (QtCore.Qt.EditRole,3):    lambda self, column: str(self.scanSegmentList[column].span),
                             (QtCore.Qt.EditRole,4):    lambda self, column: str(self.scanSegmentList[column].steps),
                             (QtCore.Qt.EditRole,5):    lambda self, column: str(self.scanSegmentList[column].stepsize),
                             (QtCore.Qt.BackgroundColorRole,0): lambda self, column: QtGui.QColor(QtCore.Qt.white) if not self.scanSegmentList[column].inconsistent else QtGui.QColor(0xff,0xa6,0xa6,0xff),
                             (QtCore.Qt.BackgroundColorRole,1): lambda self, column: QtGui.QColor(QtCore.Qt.white) if not self.scanSegmentList[column].inconsistent else QtGui.QColor(0xff,0xa6,0xa6,0xff),
                             (QtCore.Qt.BackgroundColorRole,2): lambda self, column: QtGui.QColor(QtCore.Qt.white) if not self.scanSegmentList[column].inconsistent else QtGui.QColor(0xff,0xa6,0xa6,0xff),
                             (QtCore.Qt.BackgroundColorRole,3): lambda self, column: QtGui.QColor(QtCore.Qt.white) if not self.scanSegmentList[column].inconsistent else QtGui.QColor(0xff,0xa6,0xa6,0xff),
                             (QtCore.Qt.BackgroundColorRole,4): lambda self, column: (QtGui.QColor(0xff,0xff,0x99) if self.scanSegmentList[column]._stepPreference=='steps' else  QtGui.QColor(QtCore.Qt.white)) if not self.scanSegmentList[column].inconsistent else QtGui.QColor(0xff,0xa6,0xa6,0xff),
                             (QtCore.Qt.BackgroundColorRole,5): lambda self, column: (QtGui.QColor(0xff,0xff,0x99) if self.scanSegmentList[column]._stepPreference=='stepsize' else  QtGui.QColor(QtCore.Qt.white)) if not self.scanSegmentList[column].inconsistent else QtGui.QColor(0xff,0xa6,0xa6,0xff),
                             }

    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.row()), lambda index, value: False )(index, value)

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
        self.dataChanged.emit( self.createIndex(0,index.column()), self.createIndex(5,index.column()) )
        self.updateSaveStatus()
        return True
    
    def setScanList(self, scanlist):
        self.beginResetModel()
        self.scanSegmentList = scanlist
        self.endResetModel()