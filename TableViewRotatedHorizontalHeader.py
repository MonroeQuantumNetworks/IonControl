'''
Created on Feb 7, 2014

@author: plmaunz
'''
from PyQt4 import QtGui, QtCore

from uiModules.RotatedHeaderView import RotatedHeaderView


class TableViewRotatedHorizontalHeader(QtGui.QTableView):
    '''
    TableView with rotated Horizontal Header
    '''


    def __init__(self, parent=None ):
        super(TableViewRotatedHorizontalHeader,self).__init__(parent)
        self.setHorizontalHeader( RotatedHeaderView( QtCore.Qt.Horizontal, self) )
        