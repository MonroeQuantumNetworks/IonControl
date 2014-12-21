'''
Created on Dec 20, 2014

@author: pmaunz
'''

from PyQt4 import QtGui
from uiModules.TableViewExtended import TableViewExtended

def saveColumnWidth( tableView ):
    return [tableView.columnWidth(i) for i in range(0, tableView.model().columnCount())]

def restoreColumnWidth( tableView, widthData, autoscaleOnNone=True ):
    if widthData:
        for column, width in zip( range(0, tableView.model().columnCount()), widthData ):
            tableView.setColumnWidth(column, width)
    else:
        tableView.resizeColumnsToContents()
     
     

appearanceHelpers = { QtGui.QSplitter: (QtGui.QSplitter.saveState, QtGui.QSplitter.restoreState),
                      TableViewExtended: (saveColumnWidth, restoreColumnWidth),
                      QtGui.QTableView: (saveColumnWidth, restoreColumnWidth)}

ClassAttributeCache = dict()
     
def saveGuiState( obj ):
    data = dict()
    if obj.__class__ in ClassAttributeCache:
        for name in ClassAttributeCache[obj.__class__]:
            attr = getattr(obj,name)
            data[name] = appearanceHelpers[attr.__class__][0](attr)            
    else:
        attrlist = list()
        for name, attr in obj.__dict__.iteritems():
            if hasattr(attr,'__class__') and attr.__class__ in appearanceHelpers:
                data[name] = appearanceHelpers[attr.__class__][0](attr)
                attrlist.append(name)
        ClassAttributeCache[obj.__class__] = attrlist
    return data
            
def restoreGuiState( obj, data ):
    if data:
        for name, value in data.iteritems():
            if hasattr( obj, name):
                attr = getattr( obj, name)
                if hasattr(attr,'__class__') and attr.__class__ in appearanceHelpers:
                    appearanceHelpers[attr.__class__][1](attr, value)
    
