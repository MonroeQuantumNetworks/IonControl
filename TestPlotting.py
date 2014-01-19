# -*- coding: utf-8 -*-
"""
Created on Wed Jan 09 21:19:26 2013

@author: pmaunz

PlotWidget that adds the coordinates of the cursor position
as a second element also allows one to copy the coordinates to the clipboard
"""

from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ButtonItem import ButtonItem
from pyqtgraph.graphicsItems.LabelItem import LabelItem
from PyQt4 import QtGui, QtCore
import math
from modules.round import roundToNDigits
import pyqtgraph

grid_opacity = 0.3
grid_icon_file = 'C:\\Users\\jamizra\\Programming\\aaAQC_FPGA\\ui\\icons\\grid2'
range_icon_file = 'C:\\Users\\jamizra\\Programming\\aaAQC_FPGA\\ui\\icons\\unityrange2'

class PlotItemWithButtons(PlotItem):
    def __init__(self,parent=None):
        super(PlotItemWithButtons,self).__init__(parent)
        self.gridBtn = ButtonItem(imageFile=grid_icon_file, width=15, parentItem=self)
        self.unityRangeBtn = ButtonItem(imageFile=range_icon_file, width=15, parentItem=self)
        self.unityRangeBtn.clicked.connect(self.onUnityRange)
        self.gridBtn.clicked.connect(self.onGrid)
        self.setYRange(0,1) #Range defaults to 0 to 1
        self.showGrid(x = True, y = True, alpha = grid_opacity) #grid defaults to on
        
    def resizeEvent(self, ev):
        PlotItem.resizeEvent(self,ev)
        gridBtnRect = self.mapRectFromItem(self.gridBtn, self.gridBtn.boundingRect())
        unityRangeBtnRect = self.mapRectFromItem(self.unityRangeBtn, self.unityRangeBtn.boundingRect())
        yGrid = self.size().height() - gridBtnRect.height()
        yRange= self.size().height() - unityRangeBtnRect.height()
        self.gridBtn.setPos(0, yGrid-24)
        self.unityRangeBtn.setPos(0, yRange-49)
    
    def onUnityRange(self):
        """Execute when unityRangeBtn is clicked"""
        self.setYRange(0,1)

    def onGrid(self):
        """Execute when gridBtn is clicked"""
        xChecked = self.ctrl.xGridCheck.isChecked()
        yChecked = self.ctrl.yGridCheck.isChecked()
        self.showGrid(x = not xChecked, y = not yChecked)

class CoordinatePlotWidget(pyqtgraph.GraphicsLayoutWidget):
    """This is the main widget for plotting data. It consists of a plot, a
       coordinate display, a button to set the y scale to 0-1, and a button
       to display/hide the grid."""
    def __init__(self,parent=None):
        super(CoordinatePlotWidget,self).__init__(parent)
        self.coordinateLabel = LabelItem(justify='right')
        self.graphicsView = self.addPlotWithButtons(row=0,col=0,colspan=2)
        self.addItem(self.coordinateLabel,row=1,col=1)
        self.graphicsView.scene().sigMouseMoved.connect(self.onMouseMoved)
        self.template = "<span style='font-size: 10pt'>x={0}, <span style='color: red'>y={1}</span></span>"
        self.mousePoint = None
        self.mousePointList = list()
        self.graphicsView.setYRange(0,1) #Range defaults to 0 to 1
        self.graphicsView.showGrid(x = True, y = True, alpha = grid_opacity) #grid defaults to on
        self.gridShown = True #Because we can't query whether the grid is on or off, we just keep track

    def addPlotWithButtons(self, row=None, col=None, rowspan=1, colspan=1, **kargs):
        plot = PlotItemWithButtons(**kargs)
        self.addItem(plot, row, col, rowspan, colspan)
        return plot
            
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
#        pg.GraphicsLayoutWidget.mouseDoubleClickEvent(self,ev)
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
    pyqtgraph.setConfigOption('background', 'w')
    pyqtgraph.setConfigOption('foreground', 'k')
    MainWindow.setCentralWidget(CoordinatePlotWidget())
    MainWindow.show()
    sys.exit(app.exec_())
    