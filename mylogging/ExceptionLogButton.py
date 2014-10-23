# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:15:47 2013

@author: pmaunz
"""

import functools
import inspect
import logging
import sys
import weakref

from PyQt4 import QtGui
import PyQt4.uic

ExceptionMessageForm, ExceptionMessageBase = PyQt4.uic.loadUiType(r'ui\ExceptionMessage.ui')

class ExceptionMessage( ExceptionMessageForm, ExceptionMessageBase):
    def __init__(self,message,parent=None):
        ExceptionMessageForm.__init__(self,parent)
        ExceptionMessageBase.__init__(self)
        self.message = message
        self.count = 1
        
    def setupUi(self, parent):
        ExceptionMessageForm.setupUi(self,parent)
        if self.message:
            self.messageLabel.setText(str(self.message))

    def increaseCount(self):
        self.count += 1
        self.messageLabel.setText( "({0}) {1}".format(self.count, str(self.message)))


GlobalExceptionLogButtonSlot =  None

class ExceptionLogButton( QtGui.QToolButton ):
    def __init__(self,parent=None):
        QtGui.QToolButton.__init__(self,parent)
        self.myMenu = QtGui.QMenu(self)
        self.setMenu( self.myMenu )
        self.setPopupMode(QtGui.QToolButton.InstantPopup)
        sys.excepthook = self.myexcepthook
        self.exceptionsListed = 0
        self.NoExceptionsIcon = QtGui.QIcon(":/petersIcons/icons/Success-01.png")
        self.ExceptionsIcon = QtGui.QIcon(":/petersIcons/icons/Error-01.png")
        self.setIcon( self.NoExceptionsIcon )
        global GlobalExceptionLogButtonSlot
        GlobalExceptionLogButtonSlot = self.excepthookSlot
        self.menuItemDict = dict()
        
    def removeAll(self):
        self.myMenu.clear()
        self.setIcon(self.NoExceptionsIcon)
        self.exceptionsListed =0
        self.menuItemDict.clear()
         
    def addClearAllAction(self):
        myMenuItem = ExceptionMessage("Clear All exceptions",self.myMenu)
        myMenuItem.setupUi(myMenuItem)
        action = QtGui.QWidgetAction(self.myMenu)
        action.setDefaultWidget( myMenuItem )
        self.myMenu.addAction(action)
        myMenuItem.deleteButton.clicked.connect( self.removeAll )
                
    def addMessage(self, message):
        oldMenuItem  = self.menuItemDict.get( str(message) )
        if oldMenuItem is not None:
            oldMenuItem.increaseCount()
        else:
            myMenuItem = ExceptionMessage(message,self.myMenu)
            myMenuItem.setupUi(myMenuItem)
            action = QtGui.QWidgetAction(self.myMenu)
            action.setDefaultWidget(myMenuItem)
            myMenuItem.deleteButton.clicked.connect( functools.partial(self.removeMessage, weakref.ref(action) ) )
            self.menuItemDict[str(message)] = myMenuItem
            if self.exceptionsListed==0:
                self.setIcon(self.ExceptionsIcon)
                self.addClearAllAction()          
            self.exceptionsListed += 1
            self.myMenu.addAction(action)
        
    def removeMessage(self, action):
        self.menuItemDict.pop(str(action().defaultWidget().message))
        self.myMenu.removeAction(action())
        self.exceptionsListed -= 1
        if self.exceptionsListed==0:
            self.removeAll()
            
    def excepthookSlot(self, exceptinfo ):
        self.myexcepthook( *exceptinfo )
        
    def myexcepthook(self, excepttype, value, tback):
        logger = logging.getLogger(inspect.getmodule(tback.tb_frame).__name__ if tback is not None else "unknown")
        self.addMessage(value)
        logger.error( str(value), exc_info=(excepttype, value, tback) )
        #sys.__excepthook__(excepttype, value, tback)
        
    
        

