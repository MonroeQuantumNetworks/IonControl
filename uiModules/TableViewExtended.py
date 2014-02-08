# -*- coding: utf-8 -*-
"""
Created on Sat May 11 11:25:40 2013

@author: pmaunz
"""

import operator

from PyQt4 import QtGui, QtCore


class TableViewExtended(QtGui.QTableView):
    def keyReleaseEvent(self, e):
        if e.key()==QtCore.Qt.Key_C and e.modifiers()&QtCore.Qt.ControlModifier:
            indexes = sorted([(i.row(),i.column()) for i in self.selectedIndexes()])
            indexesbycolumn = sorted(indexes,key=operator.itemgetter(1))
            model = self.model()
            tabledata = list()
            for row in range( indexes[0][0], indexes[-1][0]+1):
                tabledata.append("\t".join([ c if c is not None else '' for c in 
                                                (model.data( model.index(row,column), QtCore.Qt.DisplayRole ) for column in  
                                                         range( indexesbycolumn[0][1], indexesbycolumn[-1][1]+1))]))
            QtGui.QApplication.clipboard().setText("\n".join(tabledata))
        else:
            QtGui.QTableView.keyReleaseEvent(self,e)