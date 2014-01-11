# -*- coding: utf-8 -*-
"""
Created on Sun Jan 06 16:49:47 2013

@author: pmaunz
"""
from PyQt4 import QtGui

class MainWindowWidget(QtGui.QMainWindow):

    def __init__(self, toolBar=None, parent=None):
        QtGui.QMainWindow.__init__(self,parent)
        self.dockWidgetList = list()
        self.actionList = list()
        self.toolBar = toolBar
        
    def activate(self):
        for widget in self.dockWidgetList:
            if widget.isFloating():
                if hasattr(widget,'wasVisible'):
                    widget.setVisible(widget.wasVisible)
        if self.toolBar:
            for action in self.actionList:
                self.toolBar.addAction(action)
        
    def deactivate(self):
        for widget in self.dockWidgetList:
            if widget.isFloating():
                widget.wasVisible = widget.isVisible()
                widget.setVisible(False)
        if self.toolBar:
            self.toolBar.clear()
        
    def onClose(self):
        pass

    def viewActions(self):
        return [ widget.toggleViewAction() for widget in self.dockWidgetList ]    
