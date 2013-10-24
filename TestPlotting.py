# -*- coding: utf-8 -*-
"""
Created on Wed Jan 09 21:19:26 2013

@author: pmaunz

PlotWidget that adds the coordinates of the cursor position
as a second element also allows one to copy the coordinates to the clipboard
"""

import pyqtgraph
from PyQt4 import QtGui, QtCore
import math
from modules.round import roundToNDigits

grid_opacity = 0.3

class LabelItem(pyqtgraph.LabelItem):
    """Allows for clicking pyqtgraph labels"""
    clicked = QtCore.pyqtSignal()
        
    def mouseClickEvent(self,ev):
        self.clicked.emit()

class TestModPlotItem(pyqtgraph.PlotItem):
    def __init__(self,parent=None):
        super(TestModPlotItem,self).__init__(parent)
        self.testButton = pyqtgraph.ButtonItem(pyqtgraph.pixmaps.getPixmap('testimg'), 14, self)

class CoordinatePlotWidget(pyqtgraph.GraphicsLayoutWidget):
    """This is the main widget for plotting data. It consists of a plot, a
       coordinate display, a button to set the y scale to 0-1, and a button
       to display/hide the grid."""
    def __init__(self,parent=None):
        super(CoordinatePlotWidget,self).__init__(parent)
        self.coordinateLabel = pyqtgraph.LabelItem(justify='right')
        self.unityRangeButton = LabelItem(justify='left')
        self.unityRangeButton.setText('Unity Range')
        self.unityRangeButton.clicked.connect( self.onUnityRange )
        self.showGridButton = LabelItem(justify='center')
        self.showGridButton.setText('Show Grid')
        self.showGridButton.clicked.connect(self.onShowGrid)
        self.graphicsView = self.addPlot(row=0,col=0,colspan=3)
        self.addItem(self.coordinateLabel,row=1,col=2)
        self.addItem(self.unityRangeButton,row=1,col=0)
        self.addItem(self.showGridButton,row=1,col=1)
        self.graphicsView.scene().sigMouseMoved.connect(self.onMouseMoved)
        self.template = "<span style='font-size: 10pt'>x={0}, <span style='color: red'>y={1}</span></span>"
        self.mousePoint = None
        self.mousePointList = list()
        self.graphicsView.setYRange(0,1) #Range defaults to 0 to 1
        self.graphicsView.showGrid(x = True, y = True, alpha = grid_opacity) #grid defaults to on
        self.gridShown = True #Because we can't query whether the grid is on or off, we just keep track

    def onUnityRange(self):
        """Execute when unityRangeButton is clicked"""
        self.graphicsView.setYRange(0,1)

    def onShowGrid(self):
        """Execute when showGridButton is clicked"""
        if self.gridShown:
            self.graphicsView.showGrid(x = False, y = False)
        else:
            self.graphicsView.showGrid(x = True, y = True, alpha = grid_opacity)
        self.gridShown = not self.gridShown
            
    def onMouseMoved(self,pos):
        """Execute when mouse is moved. If mouse is over plot, show cursor
           coordinates on coordinateLabel."""
        if self.graphicsView.sceneBoundingRect().contains(pos):
            self.mousePoint = self.graphicsView.vb.mapSceneToView(pos)
            vR = self.graphicsView.vb.viewRange()
            deltaX, deltaY = vR[0][1]-vR[0][0], vR[1][1]-vR[1][0] #Calculate x and y display ranges
            precx = int( math.ceil( math.log10(abs(self.mousePoint.x()/deltaX)) ) + 3 ) if self.mousePoint.x()!=0 and deltaX>0 else 1
            precy = int( math.ceil( math.log10(abs(self.mousePoint.y()/deltaY)) ) + 3 ) if self.mousePoint.y()!=0 and deltaY>0 else 1
            roundedx, roundedy = roundToNDigits( self.mousePoint.x(),precx), roundToNDigits(self.mousePoint.y(), precy )
            self.coordinateLabel.setText( self.template.format( repr(roundedx), repr(roundedy) ))
            
    def onCopyLocation(self,which):
        text = {'x': ("{0}".format(self.mousePoint.x())),
                'y': ("{0}".format(self.mousePoint.y())) }.get(which,"{0}, {1}".format(self.mousePoint.x(),self.mousePoint.y()))
        QtGui.QApplication.clipboard().setText(text)
        
#    def mouseDoubleClickEvent(self, ev):
#        pyqtgraph.GraphicsLayoutWidget.mouseDoubleClickEvent(self,ev)
#        print "CoordinatePlotWidget mouseDoubleClicked"
#        #self.onMouseClicked(ev)
        
    def copyPointsToClipboard(self, modifiers):
        print "copyPointsToClipboard"
        if modifiers & QtCore.Qt.ControlModifier:
            if modifiers & QtCore.Qt.ShiftModifier:
                QtGui.QApplication.clipboard().setText(" ".join(["{0}".format(p.x()) for p in self.mousePointList]))
            elif modifiers & QtCore.Qt.AltModifier:
                QtGui.QApplication.clipboard().setText(" ".join(["{0}".format(p.y()) for p in self.mousePointList]))        
            else:
                QtGui.QApplication.clipboard().setText(" ".join(["{0} {1}".format(p.x(),p.y()) for p in self.mousePointList]))
        
    def keyReleaseEvent(self, ev):
        print "Key released", ev.key(), ev.modifiers()
        { 67: self.copyPointsToClipboard }.get(ev.key(),lambda x:None)(ev.modifiers())
        
    def mouseReleaseEvent(self,ev):
        pyqtgraph.GraphicsLayoutWidget.mouseReleaseEvent(self,ev)
        if ev.modifiers()&QtCore.Qt.ShiftModifier:
            self.mousePointList.append(self.mousePoint)
        else:
            self.mousePointList = [self.mousePoint]

if __name__ == '__main__':
    import sys    
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    a = TestModPlotItem()
    b = pyqtgraph.GraphicsView()
    b.setCentralWidget(a)
    MainWindow.setCentralWidget(b)
    MainWindow.show()
    sys.exit(app.exec_())
    