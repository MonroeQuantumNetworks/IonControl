# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 16:17:51 2012

@author: pmaunz
"""
import pyqtgraph
from PyQt4 import QtCore, QtGui
from ui import Experiment_rc

penList = [ (pyqtgraph.mkPen('y', width=2, style=QtCore.Qt.SolidLine),),
            (pyqtgraph.mkPen((247,153,0), width=2, style=QtCore.Qt.SolidLine),'s',pyqtgraph.mkPen((247,153,0), width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('r', width=2, style=QtCore.Qt.SolidLine),'o',pyqtgraph.mkPen('r', width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('g', width=2, style=QtCore.Qt.SolidLine),'t',pyqtgraph.mkPen('g', width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('b', width=2, style=QtCore.Qt.SolidLine),'d',pyqtgraph.mkPen('b', width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('c', width=2, style=QtCore.Qt.SolidLine),'s',None,pyqtgraph.mkBrush('c')),
            (pyqtgraph.mkPen('m', width=2, style=QtCore.Qt.SolidLine),'o',None,pyqtgraph.mkBrush('m')),
            (pyqtgraph.mkPen('k', width=2, style=QtCore.Qt.SolidLine),'t',None,pyqtgraph.mkBrush('k')),
            (pyqtgraph.mkPen((0,255,200), width=2, style=QtCore.Qt.SolidLine),'s',pyqtgraph.mkPen((0,255,200), width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen((0,191,255), width=2, style=QtCore.Qt.SolidLine),'o',pyqtgraph.mkPen((0,191,255), width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen((144,0,255), width=2, style=QtCore.Qt.SolidLine),'t',pyqtgraph.mkPen((144,0,255), width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen((255,0,157), width=2, style=QtCore.Qt.SolidLine),'d',pyqtgraph.mkPen((255,0,157), width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen((247,153,0), width=2, style=QtCore.Qt.SolidLine),'s',pyqtgraph.mkPen((247,153,0), width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('r', width=2, style=QtCore.Qt.DashLine),'o',pyqtgraph.mkPen('r', width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('g', width=2, style=QtCore.Qt.DashLine),'t',pyqtgraph.mkPen('g', width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('b', width=2, style=QtCore.Qt.DashLine),'d',pyqtgraph.mkPen('b', width=2, style=QtCore.Qt.SolidLine),QtGui.QColor(0,0,0,0)),
            (pyqtgraph.mkPen('c', width=2, style=QtCore.Qt.DashLine),'s',None,pyqtgraph.mkBrush('c')),
            (pyqtgraph.mkPen('m', width=2, style=QtCore.Qt.DashLine),'o',None,pyqtgraph.mkBrush('m')),
            (pyqtgraph.mkPen('w', width=2, style=QtCore.Qt.DashLine),'t',None,pyqtgraph.mkBrush('k')) ]

class penicons:
    def penicons(self):
        if not hasattr(self,'icons'):
            self.loadicons()
        return self.icons
        
    def loadicons(self):
          self.icons = [ QtGui.QIcon(), QtGui.QIcon(":/penicon/icons/yellow.png"),
            QtGui.QIcon(":/penicon/icons/red.png"),
            QtGui.QIcon(":/penicon/icons/green.png"),
            QtGui.QIcon(":/penicon/icons/blue.png"),
            QtGui.QIcon(":/penicon/icons/cyan.png"),
            QtGui.QIcon(":/penicon/icons/magenta.png"),
            QtGui.QIcon(":/penicon/icons/white.png"),
            QtGui.QIcon(":/penicon/icons/yellow.png"),
            QtGui.QIcon(":/penicon/icons/yellow.png"),
            QtGui.QIcon(":/penicon/icons/yellow.png"),
            QtGui.QIcon(":/penicon/icons/yellow.png"),
            QtGui.QIcon(":/penicon/icons/yellow-dash.png"),
            QtGui.QIcon(":/penicon/icons/red-dash.png"),
            QtGui.QIcon(":/penicon/icons/green-dash.png"),
            QtGui.QIcon(":/penicon/icons/blue-dash.png"),
            QtGui.QIcon(":/penicon/icons/cyan-dash.png"),
            QtGui.QIcon(":/penicon/icons/magenta-dash.png"),
            QtGui.QIcon(":/penicon/icons/white-dash.png") ]    
