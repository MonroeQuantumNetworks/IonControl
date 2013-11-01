# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 16:17:51 2012

@author: pmaunz
"""
from pyqtgraph import mkPen, mkBrush
from PyQt4 import QtCore, QtGui
from ui import Experiment_rc

"""
penList is a list of 4-tuples. It is used to define how to plot a trace.
The first element of the tuple is the pen to use for drawing solid curves. The
second element is the symbol to use for plotting datapoints. The third element
is the pen to use for the symbol. The fourth element is the brush to use to
fill in the symbol.

Symbol letters are:
    's': square
    'o': circle
    't': triangle
    'd': diamond
"""

yellow = (180,180,0,255)
orange = (247,153,0)
green = (0,180,0,255)
blue = (0,0,255,255)
red = (255,0,0,255)
cyan = (0,200,200,255)
magenta = (255,0,255,255)
black = (0,0,0,255)
white = (255,255,255,255)
aquamarine = (0,200,145,255)
lightblue = (0,191,255)
purple = (144,0,255)
darkpink = (255,0,157)

blank = QtGui.QColor(0,0,0,0)
penWidth = 2
solid = QtCore.Qt.SolidLine
dashed = QtCore.Qt.DashLine

solidYellowPen = mkPen(yellow, width=penWidth, style=solid)
dashedYellowPen = mkPen(yellow, width=penWidth, style=dashed)
solidOrangePen = mkPen(orange, width=penWidth, style=solid)
solidRedPen = mkPen(red, width=penWidth, style=solid) 
dashedRedPen = mkPen(red, width=penWidth, style=dashed) 
solidGreenPen = mkPen(green, width=penWidth, style=solid)
dashedGreenPen = mkPen(green, width=penWidth, style=dashed)
solidBluePen = mkPen(blue, width=penWidth, style=solid)
dashedBluePen = mkPen(blue, width=penWidth, style=dashed)
solidCyanPen = mkPen(cyan, width=penWidth, style=solid)
dashedCyanPen = mkPen(cyan, width=penWidth, style=dashed)
solidMagentaPen = mkPen(magenta, width=penWidth, style=solid)
dashedMagentaPen = mkPen(magenta, width=penWidth, style=dashed)
solidBlackPen = mkPen(black, width=penWidth, style=solid)
dashedBlackPen = mkPen(black, width=penWidth, style=dashed)
solidAquamarinePen = mkPen(aquamarine, width=penWidth, style=solid)
solidLightBluePen = mkPen(lightblue, width=penWidth, style=solid)
solidPurplePen = mkPen(purple, width=penWidth, style=solid)
solidDarkPinkPen = mkPen(darkpink, width=penWidth, style=solid)

penList = [ (solidYellowPen,),
            (solidOrangePen, 's', solidOrangePen, blank),
            (solidRedPen, 'o', solidRedPen, blank),
            (solidGreenPen, 't', solidGreenPen, blank),
            (solidBluePen, 'd', solidBluePen, blank),
            (solidCyanPen, 's', None, mkBrush(cyan)),
            (solidMagentaPen, 'o', None, mkBrush(magenta)),
            (solidBlackPen,'t',None,mkBrush(black)),
            (solidAquamarinePen, 's', solidAquamarinePen, blank),
            (solidLightBluePen, 'o', solidLightBluePen, blank),
            (solidPurplePen, 't', solidPurplePen, blank),
            (solidDarkPinkPen, 'd', solidDarkPinkPen, blank),
            (dashedYellowPen, 's', dashedYellowPen, blank),
            (dashedRedPen, 'o', solidRedPen, blank),
            (dashedGreenPen, 't', solidGreenPen, blank),
            (dashedBluePen, 'd', solidBluePen, blank),
            (dashedCyanPen, 's', None, mkBrush(cyan)),
            (dashedMagentaPen, 'o', None, mkBrush(magenta)),
            (dashedBlackPen, 't', None, mkBrush(black)) ]

class penicons:
    def penicons(self):
        if not hasattr(self,'icons'):
            self.loadicons()
        return self.icons
        
    def loadicons(self):
          self.icons = [ QtGui.QIcon(), 
            QtGui.QIcon(":/penicon/icons/247-153-0.png"),
            QtGui.QIcon(":/penicon/icons/red.png"),
            QtGui.QIcon(":/penicon/icons/green.png"),
            QtGui.QIcon(":/penicon/icons/blue.png"),
            QtGui.QIcon(":/penicon/icons/cyan.png"),
            QtGui.QIcon(":/penicon/icons/magenta.png"),
            QtGui.QIcon(":/penicon/icons/white.png"),
            QtGui.QIcon(":/penicon/icons/0-255-200.png"),
            QtGui.QIcon(":/penicon/icons/0-191-255.png"),
            QtGui.QIcon(":/penicon/icons/144-0-255.png"),
            QtGui.QIcon(":/penicon/icons/255-0-157.png"),
            QtGui.QIcon(":/penicon/icons/yellow-dash.png"),
            QtGui.QIcon(":/penicon/icons/red-dash.png"),
            QtGui.QIcon(":/penicon/icons/green-dash.png"),
            QtGui.QIcon(":/penicon/icons/blue-dash.png"),
            QtGui.QIcon(":/penicon/icons/cyan-dash.png"),
            QtGui.QIcon(":/penicon/icons/magenta-dash.png"),
            QtGui.QIcon(":/penicon/icons/white-dash.png") ]    
