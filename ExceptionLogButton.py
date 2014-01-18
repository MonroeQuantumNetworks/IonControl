# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:15:47 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
import sys
import functools
from modules.enum import enum
import logging
import inspect

ExceptionMessageForm, ExceptionMessageBase = PyQt4.uic.loadUiType(r'ui\ExceptionMessage.ui')

class ExceptionMessage( ExceptionMessageForm, ExceptionMessageBase):
    def __init__(self,message,parent=None):
        ExceptionMessageForm.__init__(self,parent)
        ExceptionMessageBase.__init__(self)
        self.message = message
        
    def setupUi(self, parent):
        ExceptionMessageForm.setupUi(self,parent)
        if self.message:
            self.messageLabel.setText(str(self.message))

class ExceptionLogButton( QtGui.QToolButton ):
    def __init__(self,parent=None):
        QtGui.QToolButton.__init__(self,parent)
        self.myMenu = QtGui.QMenu(self)
        self.setMenu( self.myMenu )
        self.setPopupMode(QtGui.QToolButton.InstantPopup)
        sys.excepthook = self.myexcepthook
        self.exceptionsListed = 0
        self.NoExceptionsIcon = QtGui.QIcon(":/openicon/icons/emblem-default.png")
        self.ExceptionsIcon = QtGui.QIcon(":/openicon/icons/emblem-important-4.png")
        self.setIcon( self.NoExceptionsIcon )
        
    def removeAll(self):
        self.myMenu.clear()
        self.setIcon(self.NoExceptionsIcon)
        
    def addClearAllAction(self):
        myMenuItem = ExceptionMessage("Clear All exceptions",self.myMenu)
        myMenuItem.setupUi(myMenuItem)
        action = QtGui.QWidgetAction(self.myMenu)
        action.setDefaultWidget( myMenuItem )
        self.myMenu.addAction(action)
        myMenuItem.deleteButton.clicked.connect( self.removeAll )
                
    def addMessage(self, message):
        myMenuItem = ExceptionMessage(message,self.myMenu)
        myMenuItem.setupUi(myMenuItem)
        action = QtGui.QWidgetAction(self.myMenu)
        action.setDefaultWidget(myMenuItem )
        if self.exceptionsListed==0:
            self.setIcon(self.ExceptionsIcon)
            self.addClearAllAction()
        self.myMenu.addAction(action)
        myMenuItem.deleteButton.clicked.connect( functools.partial(self.removeMessage, action) )
        self.exceptionsListed += 1
        
    def removeMessage(self, action):
        self.myMenu.removeAction(action)
        self.exceptionsListed -= 1
        if self.exceptionsListed==0:
            self.setIcon(self.NoExceptionsIcon)
        
    def myexcepthook(self, type, value, tback):
        logger = logging.getLogger(inspect.getmodule(tback.tb_frame).__name__)
        self.addMessage(value)
        logger.error( str(value), exc_info=(type, value, tback) )
        #sys.__excepthook__(type, value, tback)
        
    
        

