from PyQt4 import QtCore

class KeyFilter(QtCore.QObject):
    keyPressed = QtCore.pyqtSignal()
    
    def __init__(self,key,parent=None):
        QtCore.QObject.__init__(self, parent)
        self.key = key
    
    def eventFilter(self, obj, event):
        if event.type()==QtCore.QEvent.KeyRelease and event.key()==self.key:
            self.keyPressed.emit()
            return True
        return False

class KeyListFilter(QtCore.QObject):
    keyPressed = QtCore.pyqtSignal( object )
    
    def __init__(self,keys,parent=None):
        QtCore.QObject.__init__(self, parent)
        self.keys = keys
    
    def eventFilter(self, obj, event):
        if event.type()==QtCore.QEvent.KeyPress and event.key() in self.keys:
            self.keyPressed.emit(event.key())
            return True
        return False
