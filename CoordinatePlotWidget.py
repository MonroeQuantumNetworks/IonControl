# -*- coding: utf-8 -*-
"""
Created on Wed Jan 09 21:19:26 2013

@author: pmaunz

This is the main plotting element used in the control program. It adds the
coordinates of the cursor position as a second element also allows one to
copy the coordinates to the clipboard. It uses a custom version of PlotItem
which includes a button to turn the grid on and off, and a button to set the
y range to 0->1.

Buttons added by jmizrahi on 10/15/2013.
"""

import pyqtgraph as pg
from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.ButtonItem import ButtonItem
from pyqtgraph.graphicsItems.PlotItem.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from PyQt4 import QtGui, QtCore
import math
from modules.round import roundToNDigits
import logging

grid_opacity = 0.3
icons_dir = '.\\ui\\icons\\'
range_icon_file = icons_dir + 'unity-range'
holdZero_icon_file = icons_dir + 'hold-zero'

class CustomViewBox(ViewBox):
    
    def __init__(self, *args, **kwds):
        super(CustomViewBox,self).__init__(*args, **kwds)
        self.holdZero = False
    
    def setRange(self, rect=None, xRange=None, yRange=None, *args, **kwds):
        if self.holdZero:
            if not kwds.get('disableAutoRange', True):
                if yRange is not None:
                    yRange[0] = 0
        ViewBox.setRange(self, rect, xRange, yRange, *args, **kwds)

class CustomPlotItem(PlotItem):
    """
    Plot using pyqtgraph.PlotItem, with a few modifications:
    Add a grid button which turns the grid on/off.
    Add a unity range button which sets the y axis range to 1.
    resizeEvent is extended to set the position of the two new buttons correctly.
    """
    def __init__(self, parent=None):
        """
        Create a new CustomPlotItem. In addition to the ordinary PlotItem, add
        a grid button and a unity range button. Also set the default range to
        0 to 1 and the default grid to on.
        """
        cvb = CustomViewBox()
        super(CustomPlotItem,self).__init__(parent, viewBox = cvb)
        pg.setConfigOption('background', 'w') #set background to white
        pg.setConfigOption('foreground', 'k') #set foreground to black
        self.unityRangeBtn = ButtonItem(imageFile=range_icon_file, width=14, parentItem=self)
        self.holdZeroBtn = ButtonItem(imageFile=holdZero_icon_file, width=14, parentItem=self)
        self.unityRangeBtn.clicked.connect(self.onUnityRange)
        self.holdZeroBtn.clicked.connect(self.onHoldZero)
        self.showGrid(x = True, y = True, alpha = grid_opacity) #grid defaults to on
        
    def resizeEvent(self, ev):
        """
        Set the size of gridBtn and unityRangeBtn appropriately. The code is 
        borrowed from the same code applied to autoBtn in the parent method in 
        PlotItem.py.
        """
        PlotItem.resizeEvent(self,ev)
#        gridBtnRect = self.mapRectFromItem(self.gridBtn, self.gridBtn.boundingRect())
        unityRangeBtnRect = self.mapRectFromItem(self.unityRangeBtn, self.unityRangeBtn.boundingRect())
        holdZeroBtnRect= self.mapRectFromItem(self.holdZeroBtn, self.holdZeroBtn.boundingRect())
        yHoldZero = self.size().height() - holdZeroBtnRect.height()
        yUnityRange= self.size().height() - unityRangeBtnRect.height()
        self.unityRangeBtn.setPos(0, yUnityRange-24) #The autoBtn height is 14, add 10 to leave a space
        self.holdZeroBtn.setPos(0, yHoldZero-67)

    def onUnityRange(self):
        """Execute when unityRangeBtn is clicked. Set the yrange to 0 to 1."""
        self.vb.holdZero = False
        self.setYRange(0,1)
        
    def onHoldZero(self):
        self.setYRange(0,1)
        self.vb.holdZero = True
        super(CustomPlotItem,self).autoBtnClicked()
        self.autoBtn.show()

    def autoBtnClicked(self):
        self.setYRange(0,1)
        self.vb.holdZero = False
        super(CustomPlotItem,self).autoBtnClicked()

    def updateButtons(self):
        self.autoBtn.show()

class CoordinatePlotWidget(pg.GraphicsLayoutWidget):
    """This is the main widget for plotting data. It consists of a plot, a
       coordinate display, a button to set the y scale to 0-1, and a button
       to display/hide the grid."""
    def __init__(self,parent=None):
        super(CoordinatePlotWidget,self).__init__(parent)
        self.coordinateLabel = LabelItem(justify='right')
        self.graphicsView = self.addCustomPlot(row=0,col=0,colspan=2)
        self.addItem(self.coordinateLabel,row=1,col=1)
        self.graphicsView.scene().sigMouseMoved.connect(self.onMouseMoved)
        self.template = "<span style='font-size: 10pt'>x={0}, <span style='color: red'>y={1}</span></span>"
        self.mousePoint = None
        self.mousePointList = list()
        self.graphicsView.showGrid(x = True, y = True, alpha = grid_opacity) #grid defaults to on
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
    def autoRange(self):
        """Set the display to autorange."""
        self.graphicsView.vb.enableAutoRange(axis=None, enable=True)
        
    def addCustomPlot(self, row=None, col=None, rowspan=1, colspan=1, **kargs):
        """This is a duplicate of addPlot from GraphicsLayout.py. The only change
        is CustomPlotItem instead of PlotItem."""
        plot = CustomPlotItem(**kargs)
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
        logger = logging.getLogger(__name__)
        logger.debug( "copyPointsToClipboard" )
        if modifiers & QtCore.Qt.ControlModifier:
            if modifiers & QtCore.Qt.ShiftModifier:
                QtGui.QApplication.clipboard().setText(" ".join(["{0}".format(p.x()) for p in self.mousePointList]))
            elif modifiers & QtCore.Qt.AltModifier:
                QtGui.QApplication.clipboard().setText(" ".join(["{0}".format(p.y()) for p in self.mousePointList]))        
            else:
                QtGui.QApplication.clipboard().setText(" ".join(["{0} {1}".format(p.x(),p.y()) for p in self.mousePointList]))
        
    def keyReleaseEvent(self, ev):
        logger = logging.getLogger(__name__)
        logger.debug(  "Key released {0} {1}".format( ev.key(), ev.modifiers() ) )
        { 67: self.copyPointsToClipboard }.get(ev.key(),lambda x:None)(ev.modifiers())
        
    def mouseReleaseEvent(self,ev):
        pg.GraphicsLayoutWidget.mouseReleaseEvent(self,ev)
        if ev.modifiers()&QtCore.Qt.ShiftModifier:
            self.mousePointList.append(self.mousePoint)
        else:
            self.mousePointList = [self.mousePoint]

if __name__ == '__main__':
    import sys    
    app = QtGui.QApplication(sys.argv)
    pg.setConfigOption('background', 'w') #set background to white
    pg.setConfigOption('foreground', 'k') #set foreground to black
    MainWindow = QtGui.QMainWindow()
    myPlotWidget = CoordinatePlotWidget()
    MainWindow.setCentralWidget(myPlotWidget)
    pi = myPlotWidget.getItem(0, 0)
    pi.plot(x = [3,4,5,6], y = [9,16,25,36])

    MainWindow.show()
    sys.exit(app.exec_())
    