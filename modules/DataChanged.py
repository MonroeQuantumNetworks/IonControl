from PyQt4 import QtCore

class DataChanged( QtCore.QObject ):
    dataChanged = QtCore.pyqtSignal( object, object )
    def __init__(self):
        pass