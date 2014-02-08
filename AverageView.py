# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 06:59:54 2013

@author: pmaunz
"""

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from modules.RunningStat import RunningStat
from modules.round import roundToStdDev, roundToNDigits


Form, Base = PyQt4.uic.loadUiType(r'ui\AverageViewUi.ui')



class AverageView(Form, Base ):
    def __init__(self,config,parentname,parent=None,zero=0):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'AverageView.'+parentname
        self.stat = RunningStat(zero)

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        # History and Dictionary
        self.clearButton.clicked.connect( self.onClear )
        self.update()
    
    def update(self):
        """"update the output
        """
        self.countLabel.setText( str(self.stat.count) )
        mean, stderr = self.stat.mean, self.stat.stderr
        self.averageLabel.setText( str(roundToStdDev(mean,stderr)) )
        self.stddevLabel.setText( str(roundToNDigits(stderr,2)) )
    
    def onClear(self):
        self.stat.clear()
        self.update()
        
    def add(self, value):
        """add value to the mean and stddev or stderr
        """
        self.stat.add(value)
        self.update()
        
        

if __name__=="__main__":
    
    import sys
    import random

    def add():
        ui.add( random.gauss(50,5) )
    
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = AverageView(config,"parent")
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    timer = QtCore.QTimer()
    timer.timeout.connect( add )
    timer.start(100)
    sys.exit(app.exec_())
