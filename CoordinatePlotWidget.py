# -*- coding: utf-8 -*-
"""
Created on Wed Jan 09 21:19:26 2013

@author: pmaunz
"""

import pyqtgraph

class CoordinatePlotWidget(pyqtgraph.GraphicsLayoutWidget):

    def __init__(self,parent):
        super(CoordinatePlotWidget,self).__init__(parent)
        self.label = pyqtgraph.LabelItem(justify='right')
        self.graphicsView = self.addPlot(row=0,col=0)
        self.addItem(self.label,row=1,col=0)
        self.graphicsView.scene().sigMouseMoved.connect(self.onMouseMoved)
        self.template = "<span style='font-size: 10pt'>x={0:.2f}, <span style='color: red'>y={1:.2f}</span></span>"
    
    def onMouseMoved(self,pos):
        if self.graphicsView.sceneBoundingRect().contains(pos):
            mousePoint = self.graphicsView.vb.mapSceneToView(pos)
            self.label.setText( self.template.format( mousePoint.x(), mousePoint.y() ) )

