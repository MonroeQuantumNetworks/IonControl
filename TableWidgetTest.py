# -*- coding: utf-8 -*-
"""
Created on Fri May 31 15:09:52 2013

@author: pmaunz
"""

from PyQt4 import uic, QtGui, QtCore
from MagnitudeSpinBox import MagnitudeSpinBox
from modules.magnitude import mg
import functools

Form, Base = uic.loadUiType(r'ui\TableWidgetTest.ui')


class TableWidgetTest(Form, Base):
    def __init__(self,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        
    def setupUi(self, parent):
        Form.setupUi(self,parent)
        spinbox = MagnitudeSpinBox() 
        spinbox.setValue( mg(12,'kHz'))
        self.tableWidget.setRowCount(3)
        action = QtGui.QAction("testAction",self)
        action.triggered.connect( self.onTriggered )
        self.tableWidget.verticalHeader().insertAction( None, action)   
        for row in range(3):
            for column in range(3):
                spinbox =  MagnitudeSpinBox()
                spinbox.setValue( mg(12,'kHz'))
                self.tableWidget.setCellWidget(row,column,spinbox)
                spinbox.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.mycustomContextMenuRequested)
        
        self.menu = QtGui.QMenu()
        self.menu.addAction( action )

    def mycustomContextMenuRequested(self, point ):
        index =  self.tableWidget.indexAt(point)
        self.menu.popup(self.mapToGlobal( point) )
            
    def onTriggered(self):
        pass
                

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = TableWidgetTest()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())