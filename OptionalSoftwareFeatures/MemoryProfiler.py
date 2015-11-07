import logging

from PyQt4 import QtGui


class MemoryProfiler(object):
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow
        self.profilingMenu = mainWindow.menuBar.addMenu("Profiling")
        self.showGrowthAction = QtGui.QAction("Show growth", mainWindow)
        self.showGrowthAction.triggered.connect(self.onShowGrowth)
        self.profilingMenu.addAction(self.showGrowthAction)

    def onShowGrowth(self):
        import gc
        import objgraph
        gc.collect()
        logging.getLogger().info("Added objects since last run")
        objgraph.show_growth(limit=100)

        