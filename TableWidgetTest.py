# -*- coding: utf-8 -*-
"""
Created on Fri May 31 15:09:52 2013

@author: pmaunz
"""

from PyQt4 import uic, QtGui, QtCore
from MagnitudeSpinBox import MagnitudeSpinBox
from magnitude import mg
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
        self.tableWidget.setRowCount(1)
        for column in range(3):
            spinbox =  MagnitudeSpinBox()
            self.tableWidget.setCellWidget(0,column,spinbox)
            spinbox.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            action = QtGui.QAction("testAction",self)
            action.triggered.connect( functools.partial(self.onTriggered,0,column) )
            spinbox.insertAction( None, action)

            
    def onTriggered(self,row,column):
        print "triggered", row, column
                

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = TableWidgetTest()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())