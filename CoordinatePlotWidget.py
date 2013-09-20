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

class CoordinatePlotWidget(pyqtgraph.GraphicsLayoutWidget):

    def __init__(self,parent):
        super(CoordinatePlotWidget,self).__init__(parent)
        self.label = pyqtgraph.LabelItem(justify='right')
        self.graphicsView = self.addPlot(row=0,col=0)
        self.addItem(self.label,row=1,col=0)
        self.graphicsView.scene().sigMouseMoved.connect(self.onMouseMoved)
        self.template = "<span style='font-size: 10pt'>x={0}, <span style='color: red'>y={1}</span></span>"
        self.mousePoint = None
        self.mousePointList = list()
    
    def onMouseMoved(self,pos):
        if self.graphicsView.sceneBoundingRect().contains(pos):
            self.mousePoint = self.graphicsView.vb.mapSceneToView(pos)
            vR = self.graphicsView.vb.viewRange()
            deltaX, deltaY = vR[0][1]-vR[0][0], vR[1][1]-vR[1][0]
            precx = int( math.ceil( math.log10(abs(self.mousePoint.x()/deltaX)) ) + 3 ) if self.mousePoint.x()>0 else 0
            precy = int( math.ceil( math.log10(abs(self.mousePoint.y()/deltaY)) ) + 3 ) if self.mousePoint.y()>0 else 0
            roundedx, roundedy = roundToNDigits( self.mousePoint.x(),precx), roundToNDigits(self.mousePoint.y(), precy )
            self.label.setText( self.template.format( repr(roundedx), repr(roundedy) ))
            
    def onCopyLocation(self,which):
        text = {'x': ("{0}".format(self.mousePoint.x())),
                'y': ("{0}".format(self.mousePoint.y())) }.get(which,"{0}, {1}".format(self.mousePoint.x(),self.mousePoint.y()))
        QtGui.QApplication.clipboard().setText(text)
        
    def mouseDoubleClickEvent(self, ev):
        pyqtgraph.GraphicsLayoutWidget.mouseDoubleClickEvent(self,ev)
        self.onMouseClicked(ev)
        
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