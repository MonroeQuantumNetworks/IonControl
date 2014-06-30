'''
Created on Apr 6, 2014

@author: pmaunz
'''
from PyQt4 import QtCore, QtGui
from TodoListEntry import TodoListEntry 
from functools import partial

class TodoListTreeModel(QtCore.QAbstractItemModel):
    valueChanged = QtCore.pyqtSignal( object )
    headerDataLookup = ['Use', 'Scan', 'Measurement','Variable', 'Start','Stop','Center','Span','Steps','Stepsize']
    def __init__(self, config, todolist, scanModules, globalVariables, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractItemModel.__init__(self, parent, *args) 
        self.todolist = todolist
        self.config = config
        self.dataLookup =  { (QtCore.Qt.CheckStateRole,0): lambda item, row: QtCore.Qt.Checked if item.enable else QtCore.Qt.Unchecked,
                             (QtCore.Qt.DisplayRole,1): lambda item, row: item.scan,
                             (QtCore.Qt.DisplayRole,2): lambda item, row: item.measurement,
                             (QtCore.Qt.DisplayRole,3): lambda item, row: item.scanVariable,                             
                             (QtCore.Qt.DisplayRole,4): lambda item, row: str(item.scanSegment.start),
                             (QtCore.Qt.DisplayRole,5): lambda item, row: str(item.scanSegment.stop),
                             (QtCore.Qt.DisplayRole,6): lambda item, row: str(item.scanSegment.center),
                             (QtCore.Qt.DisplayRole,7): lambda item, row: str(item.scanSegment.span),
                             (QtCore.Qt.DisplayRole,8): lambda item, row: str(item.scanSegment.steps),
                             (QtCore.Qt.DisplayRole,9): lambda item, row: str(item.scanSegment.stepsize),
                             (QtCore.Qt.EditRole,1): lambda item, row: item.scan,
                             (QtCore.Qt.EditRole,2): lambda item, row: item.measurement,
                             (QtCore.Qt.EditRole,3): lambda item, row: item.scanVariable,                             
                             (QtCore.Qt.EditRole,4): lambda item, row: item.scanSegment.start,
                             (QtCore.Qt.EditRole,5): lambda item, row: item.scanSegment.stop,
                             (QtCore.Qt.EditRole,6): lambda item, row: item.scanSegment.center,
                             (QtCore.Qt.EditRole,7): lambda item, row: item.scanSegment.span,
                             (QtCore.Qt.EditRole,8): lambda item, row: item.scanSegment.steps,
                             (QtCore.Qt.EditRole,9): lambda item, row: item.scanSegment.stepsize,
                             (QtCore.Qt.BackgroundColorRole,0): lambda item, index: self.colorLookup[self.running] if self.activeRow==index else QtCore.Qt.white
                             }
        self.setDataLookup = {
                             (QtCore.Qt.EditRole,1): partial( self.setItemData, 'scan' ),
                             (QtCore.Qt.EditRole,2): partial( self.setItemData, 'measurement' ),
                             (QtCore.Qt.EditRole,3): partial( self.setItemData, 'scanVariable' ),
                             (QtCore.Qt.EditRole,4): partial( self.setScanSegmentData, 'start' ),
                             (QtCore.Qt.EditRole,5): partial( self.setScanSegmentData, 'stop' ),
                             (QtCore.Qt.EditRole,6): partial( self.setScanSegmentData, 'center' ),
                             (QtCore.Qt.EditRole,7): partial( self.setScanSegmentData, 'span' ),
                             (QtCore.Qt.EditRole,8): partial( self.setScanSegmentData, 'steps' ),
                             (QtCore.Qt.EditRole,9): partial( self.setScanSegmentData, 'stepsize' ),
                              }
        self.colorLookup = { True: QtGui.QColor(0xd0, 0xff, 0xd0), False: QtGui.QColor(0xff, 0xd0, 0xd0) }
        self.activeRow = None
        self.rootNode = self.config.get('TodolistRoot', TodoListEntry() )
        self.scanModules = scanModules
        self.scanModuleMeasurements = dict()
        self.globalVariables = globalVariables

    def setItemData(self, field, item, value):
        setattr( item,  field, str(value) )
        return True
    
    def setScanSegmentData(self, field, item, value ):
        setattr( item.scanSegment, field, value)
        return True
        
    def item(self, index):
        if isinstance(index, QtCore.QPersistentModelIndex ):
            index = QtCore.QModelIndex(index)
        if index and index.isValid():
            return index.internalPointer()
        return self.rootNode
        
        
    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex();

        childItem = self.item(index)
        parentItem = childItem.parent() 
        if parentItem == self.rootNode:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.childNumber(), 0, parentItem )
        
    def index(self, row, column, parent):
        if parent.isValid() and parent.column()!=0:
            return QtCore.QModelIndex()
        
        parentItem = self.item(parent)
        childItem = parentItem.child(row)
        
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()
        
    def next(self, index, recurse=True):
        entry = self.item(index)
        if recurse and entry.childCount()>0:
            return self.createIndex(0, 0, index)
        _next = index.sibling( index.row()+1, 0 )
        if not _next.isValid() and index.parent().isValid():
            return self.next( index.parent(), recurse=False)
        return _next
            
    def setActiveRow(self, index, running=True):
        oldactive = self.activeRow
        self.activeRow = index
        self.running = running
        if index is not None and index.isValid():
            self.dataChanged.emit( index.sibling(index.row(),0), index.sibling(index.row(),9) )
        if oldactive is not None and oldactive!=index:
            self.dataChanged.emit( index.sibling(index.row(),0), index.sibling(index.row(),9) )

    def rowCount(self, index=QtCore.QModelIndex()): 
        parentItem = self.item(index)
        return parentItem.childCount()
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 10
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()),lambda item, row: None)(index.internalPointer(), index)
        return None
        
    def setData(self, index, value, role):
        if index.isValid():
            return self.setDataLookup.get((role, index.column()),lambda item, value: False )(index.internalPointer(), value)
        
    def flags(self, index ):
        if index.column()==0:
            return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None #QtCore.QVariant()
                        
    def setValue(self, index, value ):
        self.setData(index, value,  QtCore.Qt.EditRole)
                        
    def choice(self, index ):
        if index.column()==1:
            return ["None"] + sorted(self.scanModuleMeasurements.keys())
        elif index.column()==2:
            return sorted( self.scanModuleMeasurements.get( index.internalPointer().scan, [] ) )
        else:
            return ["None"] + sorted( self.globalVariables.keys() )
                        
    def populateMeasurements(self):
        self.scanModuleMeasurements = dict()
        for name, widget in self.scanModules.iteritems():
            if hasattr(widget, 'scanControlWidget' ):
                self.populateMeasurementsItem( name, widget.scanControlWidget.settingsDict )
                
    def populateMeasurementsItem(self, name, settingsDict ):
        self.scanModuleMeasurements[name] = sorted(settingsDict.keys())

    def moveRow(self, rows, up=True):
        if up:
            if len(rows)>0 and rows[0]>0:
                for row in rows:
                    self.todolist[row], self.todolist[row-1] = self.todolist[row-1], self.todolist[row]
                    self.dataChanged.emit( self.createIndex(row-1,0), self.createIndex(row,3) )
                return True
        else:
            if len(rows)>0 and rows[0]<len(self.todolist)-1:
                for row in rows:
                    self.todolist[row], self.todolist[row+1] = self.todolist[row+1], self.todolist[row]
                    self.dataChanged.emit( self.createIndex(row,0), self.createIndex(row+1,3) )
                return True
        return False

    def addMeasurement(self, index):
        parent = self.item( index )
        parentindex = index if index is not None else QtCore.QModelIndex()
        position = parent.childCount()
        self.beginInsertRows(parentindex, position, position)
        parent.addChild(TodoListEntry(parent=parent))
        self.endInsertRows()
        
    def dropMeasurement (self, index):
        if index.isValid():
            self.beginRemoveRows(index, index.row(), index.row() )
            self.item(index).drop()
            self.endRemoveRows()
    
    def saveConfig(self):
        self.config['TodolistRoot'] = self.rootNode
            
