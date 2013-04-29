# -*- coding: utf-8 -*-
"""
Created on Wed Jan 09 21:19:26 2013

@author: pmaunz
"""

import pyqtgraph
from PyQt4 import QtGui, QtCore

class CoordinatePlotWidget(pyqtgraph.GraphicsLayoutWidget):

    def __init__(self,parent):
        super(CoordinatePlotWidget,self).__init__(parent)
        self.label = pyqtgraph.LabelItem(justify='right')
        self.graphicsView = self.addPlot(row=0,col=0)
        self.addItem(self.label,row=1,col=0)
        self.graphicsView.scene().sigMouseMoved.connect(self.onMouseMoved)
        self.graphicsView.scene().sigMouseClicked.connect(self.onMouseClicked)
        self.template = "<span style='font-size: 10pt'>x={0:.4f}, <span style='color: red'>y={1:.4f}</span></span>"
        self.mousePoint = None
    
    def onMouseMoved(self,pos):
        if self.graphicsView.sceneBoundingRect().contains(pos):
            self.mousePoint = self.graphicsView.vb.mapSceneToView(pos)
            self.label.setText( self.template.format( self.mousePoint.x(), self.mousePoint.y() ) )
            
    def onMouseClicked(self,ev):
        """ does not work because pyqtgraph does not send the click event if it is accepted by anything else"""
        print "onMouseClicked" 
        #if self.graphicsView.sceneBoundingRect().contains(ev.scenePos()):
            #mousePoint = self.graphicsView.vb.mapSceneToView(ev.scenePos())
        print "onMouseClicked", self.mousePoint
        if ev.modifiers()&QtCore.Qt.ShiftModifier:
            text = "{0}".format(self.mousePoint.x())
        elif ev.modifiers()&QtCore.Qt.ControlModifier:
            text = ("{0}".format(self.mousePoint.y()))
        else:
            text = "{0}, {1}".format(self.mousePoint.x(),self.mousePoint.y())
#        text = {QtCore.Qt.ShiftModifier: ("{0}".format(self.mousePoint.x())),
#                QtCore.Qt.ControlModifier: ("{0}".format(self.mousePoint.y())),
#                QtCore.Qt.NoModifier: ("{0}".format(self.mousePoint.x()))}.get(ev.modifiers(),"{0}, {1}".format(self.mousePoint.x(),self.mousePoint.y()))
        QtGui.QApplication.clipboard().setText(text)

    def onCopyLocation(self,which):
        text = {'x': ("{0}".format(self.mousePoint.x())),
                'y': ("{0}".format(self.mousePoint.y())) }.get(which,"{0}, {1}".format(self.mousePoint.x(),self.mousePoint.y()))
        QtGui.QApplication.clipboard().setText(text)
        
    def mouseDoubleClickEvent(self, ev):
        pyqtgraph.GraphicsLayoutWidget.mouseDoubleClickEvent(self,ev)
        self.onMouseClicked(ev)