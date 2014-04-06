from datetime import timedelta
import time

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from modules.enum import enum


Form, Base = PyQt4.uic.loadUiType(r'ui\ScanProgress.ui')

class ScanProgress(Form,Base):
    OpStates = enum('idle','running','paused','starting','stopping', 'interrupted')
    stateChanged = QtCore.pyqtSignal( object )
    def __init__(self):
        Form.__init__(self)
        Base.__init__(self)
        self.state = self.OpStates.idle
        self.range = 1
        self.startTime = time.time()     # time of last start
        self.previouslyElapsedTime = 0      # time spent on run before last start 
        self.averagingMode = False
        self.expected = 0
        self.timer = None
    
    def setupUi(self):
        super(ScanProgress,self).setupUi(self)
        self.scansAveraged.hide()
        self.statusLabel.setText("Idle")
        self.progressBar.setFormat("%p%")            
        
    def setAveraged(self, num):
        if num is None:
            self.scansAveraged.hide()
            self.averagingMode = False
        else:
            self.scansAveraged.setText("Scans averaged: {0}".format(num))
            self.scansAveraged.show()
            self.averagingMode = True

            
    def startTimer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.setTimeLabel )
        self.timer.start(1000)
        
    def stopTimer(self):
        if self.timer:
            self.timer = None
            
    def setIdle(self):
        self.statusLabel.setText("Idle")    
        self.progressBar.setValue(0)
        self.state = self.OpStates.idle
        self.stateChanged.emit('idle')
        self.previouslyElapsedTime = time.time()-self.startTime
        self.widget.setStyleSheet( "QWidget { background: #ffffff; }")
    
    def setRunning(self,total):
        self.statusLabel.setText("Running")    
        self.range = total
        self.progressBar.setRange(0,total)
        self.progressBar.setValue(0)
        #self.progressBar.setStyleSheet("")
        self.setTimeLabel()
        self.state = self.OpStates.running
        self.stateChanged.emit('running')
        self.startTime = time.time()
        self.previouslyElapsedTime = 0
        self.widget.setStyleSheet( "QWidget { background: #a0ffa0; }")
        self.startTimer()
    
    def resumeRunning(self, index):
        self.statusLabel.setText("Running")    
        self.progressBar.setValue(index)
        self.startTime = time.time()
        self.state = self.OpStates.running
        self.stateChanged.emit('running')
        self.widget.setStyleSheet( "QWidget { background: #a0ffa0; }")
        self.startTimer()
    
    def setPaused(self):
        #self.progressBar.setStyleSheet(StyleSheets.RedProgressBar)
        self.statusLabel.setText("Paused")            
        self.setTimeLabel()
        self.state = self.OpStates.paused
        self.stateChanged.emit('paused')
        self.previouslyElapsedTime = time.time()-self.startTime
        self.widget.setStyleSheet( "QWidget { background: #c0c0ff; }")
        self.stopTimer()
    
    def setStarting(self):
        self.statusLabel.setText("Starting") 
        self.state = self.OpStates.starting
        self.stateChanged.emit('starting')
      
    
    def setStopping(self):
        self.statusLabel.setText("Stopping")    
        self.state = self.OpStates.stopping
        self.stateChanged.emit('stopping')

    
    def setInterrupted(self, reason):
        #self.progressBar.setStyleSheet(StyleSheets.RedProgressBar)
        self.previouslyElapsedTime = time.time()-self.startTime
        self.statusLabel.setText("Interrupted ({0})".format(reason))            
        self.state = self.OpStates.interrupted
        self.stateChanged.emit('interrupted')
        self.setTimeLabel()
        self.widget.setStyleSheet( "QWidget { background: #ffa0a0; }")
        self.stopTimer()
       
    def onData(self, index):
        self.progressBar.setValue(index)
        self.expected =  self.elapsedTime() / (index/float(self.range)) if index>0 else 0
        self.setTimeLabel()
        
    def elapsedTime(self):
        return self.previouslyElapsedTime + ( (time.time() - self.startTime) if self.state==self.OpStates.running else 0 )
 
    def setTimeLabel(self):
        self.timeLabel.setText( "{0} / {1}".format(timedelta(seconds=round(self.elapsedTime())),
                                                   timedelta(seconds=round(self.expected)))) 



if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = ScanProgress()
    ui.setupUi()
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
