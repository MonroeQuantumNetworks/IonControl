from PyQt4 import QtCore


class DataChanged( QtCore.QObject ):
    dataChanged = QtCore.pyqtSignal( object, object )
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)