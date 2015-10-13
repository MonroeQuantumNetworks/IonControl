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
from datetime import datetime

from PyQt4 import QtGui
import PyQt4.uic
from modules.firstNotNone import firstNotNone

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\ExceptionMessage.ui')
ExceptionMessageForm, ExceptionMessageBase = PyQt4.uic.loadUiType(uipath)

class ExceptionMessage( ExceptionMessageForm, ExceptionMessageBase):
    def __init__(self,message,parent=None,showTime=True):
        ExceptionMessageForm.__init__(self,parent)
        ExceptionMessageBase.__init__(self)
        self.message = str(message)
        self.count = 1
        self.time = datetime.now()
        self.showTime = showTime
        
    def messageText(self):
        text = ""
        if self.message:
            if self.count==1:
                if self.time is not None and self.showTime:
                    text = "{0} {1}".format(self.time.strftime('%H:%M:%S'),self.message)
                else:
                    text = self.message
            else:
                if self.time is not None and self.showTime:
                    text = "({0}) {1} {2}".format(self.count,self.time.strftime('%H:%M:%S'),self.message)
                else:
                    text = "({0}) {1}".format(self.count, self.message)
        return text
        
    def setupUi(self, parent):
        ExceptionMessageForm.setupUi(self,parent)
        self.messageLabel.setText(self.messageText())

    def increaseCount(self):
        self.count += 1
        self.time = datetime.now() 
        self.messageLabel.setText( self.messageText())


GlobalExceptionLogButtonSlot =  None


class LogButton( QtGui.QToolButton  ):
    def __init__(self,parent=None, noMessageIcon=None, messageIcon=None, maxMessages=None, messageName=None ):
        QtGui.QToolButton.__init__(self,parent)
        self.myMenu = QtGui.QMenu(self)
        self.setMenu( self.myMenu )
        self.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.exceptionsListed = 0
        self.NoExceptionsIcon = QtGui.QIcon( firstNotNone(noMessageIcon, ":/petersIcons/icons/Success-01.png") )
        self.ExceptionsIcon = QtGui.QIcon( firstNotNone(messageIcon, ":/petersIcons/icons/Error-01.png") )
        self.setIcon( self.NoExceptionsIcon )
        self.menuItemDict = dict()
        self.maxMessages = maxMessages
        self.clearAllMessage = "Clear All {0}".format( firstNotNone(messageName, "exceptions") )
        
    def removeAll(self):
        self.myMenu.clear()
        self.setIcon(self.NoExceptionsIcon)
        self.exceptionsListed =0
        self.menuItemDict.clear()
         
    def addClearAllAction(self):
        myMenuItem = ExceptionMessage(self.clearAllMessage ,self.myMenu, showTime=False)
        myMenuItem.setupUi(myMenuItem)
        action = QtGui.QWidgetAction(self.myMenu)
        action.setDefaultWidget( myMenuItem )
        self.myMenu.addAction(action)
        myMenuItem.deleteButton.clicked.connect( self.removeAll )
                
    def addMessage(self, message):
        message = str(message)
        oldMenuItem  = self.menuItemDict.get( message )
        if oldMenuItem is not None:
            oldMenuItem.increaseCount()
        else:
            myMenuItem = ExceptionMessage(message,self.myMenu)
            myMenuItem.setupUi(myMenuItem)
            action = QtGui.QWidgetAction(self.myMenu)
            action.setDefaultWidget(myMenuItem)
            myMenuItem.deleteButton.clicked.connect( functools.partial(self.removeMessage, weakref.ref(action) ) )
            self.menuItemDict[message] = myMenuItem
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
            
class ExceptionLogButton( LogButton ):
    def __init__(self,parent=None):
        super(ExceptionLogButton, self).__init__(parent)
        sys.excepthook = self.myexcepthook
        global GlobalExceptionLogButtonSlot
        GlobalExceptionLogButtonSlot = self.excepthookSlot
        
    def excepthookSlot(self, exceptinfo ):
        self.myexcepthook( *exceptinfo )
        
    def myexcepthook(self, excepttype, value, tback):
        logger = logging.getLogger(inspect.getmodule(tback.tb_frame).__name__ if tback is not None else "unknown")
        self.addMessage(value)
        logger.error( str(value), exc_info=(excepttype, value, tback) )
        #sys.__excepthook__(excepttype, value, tback)
        
    
        

