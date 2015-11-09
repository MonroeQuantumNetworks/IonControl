from PyQt4 import QtCore

from modules.Observable import Observable


class UseTracker(object):
    def __init__(self):
        self.adjustingDevices = set()
        self.doneAdjusting = Observable()

    @property
    def adjusting(self):
        return len(self.adjustingDevices) > 0

    def take(self, device):
        self.adjustingDevices.add(device)

    def release(self, device):
        self.adjustingDevices.discard(device)
        if not self.adjusting:
            self.doneAdjusting.firebare()
            self.doneAdjusting.callbacks = list()

    def callWhenDoneAdjusting(self, callback):
        if self.adjusting:
            self.doneAdjusting.subscribe(callback)
        else:
            QtCore.QTimer.singleShot(0, callback)

