from PyQt4 import QtGui, QtCore
import functools

def textSize(text):
    """return the default size of a block of text"""
    defaultFontName = QtGui.QFont().defaultFamily()
    font = QtGui.QFont(defaultFontName,-1,QtGui.QFont.Normal)
    fm = QtGui.QFontMetrics(font)
    width = fm.width(text)
    height = fm.height()
    return QtCore.QSize(width,height)

def updateComboBoxItems( combo, items, selected=None):
    """Update the items in a combo Box,
    if the selected item is still there select it 
    do NOT emit signals during the process"""
    selected = str( combo.currentText() ) if selected is None else selected
    with BlockSignals(combo):
        combo.clear()
        combo.addItems( items )
        index = combo.findText(selected)
        if index >= 0:
            combo.setCurrentIndex( index )
        else:
            combo.setCurrentIndex(0)
    return str(combo.currentText())

def restoreDockWidgetSizes(mainWindow, config, configname):
    """
    Restore the dock widget sizes in a main window.

    This function addresses a bug in Qt. "restoreState" should restore the size of dock widgets, but it doesn't.
    Instead dock widgets are set to their miminum size. To deal with this, this function sets the minimum size to
    the saved size, and then reset the minimum size to zero one second later, after the widget has been drawn.
    """
    dockList = mainWindow.findChildren(QtGui.QDockWidget)
    for dock in dockList: #restore size of each dock
        dockSizeName = configname+"."+str(dock.objectName())+".size"
        if dockSizeName in config:
            width, height = config[dockSizeName]
            dock.setMinimumWidth(width)
            dock.setMinimumHeight(height)
            QtCore.QTimer.singleShot(1000, functools.partial(dock.setMinimumWidth, 0))
            QtCore.QTimer.singleShot(1000, functools.partial(dock.setMinimumHeight, 0))

def saveDockWidgetSizes(mainWindow, config, configname):
    """Save the dock widget sizes of a main window"""
    dockList = mainWindow.findChildren(QtGui.QDockWidget)
    for dock in dockList:
        dockSizeName = configname+"."+str(dock.objectName())+".size"
        if dock.isVisibleTo(mainWindow):
            config[dockSizeName] = dock.width(), dock.height() #save size of each visible dock
        elif dockSizeName in config: #If dock is not visible, don't leave a size in the config dict
            del config[dockSizeName]


class BlockSignals:
    """Encapsulate blockSignals in __enter__ __exit__ idiom"""
    def __init__(self, widget):
        self.widget = widget
    
    def __enter__(self):
        self.oldstate = self.widget.blockSignals(True)
        return self.widget

    def __exit__(self, exittype, value, traceback):
        self.widget.blockSignals(self.oldstate)

    
class Override:
    """Encapulse temporary change of a boolean in __enter__ __exit__ idiom"""
    def __init__(self, obj, attr, overrideValue):
        self.obj = obj
        self.attr = attr
        self.overrideValue = overrideValue
        
    def __enter__(self):
        self.previous = getattr( self.obj, self.attr )
        setattr( self.obj, self.attr, self.overrideValue )
        return self

    def __exit__(self, exittype, value, traceback):
        setattr( self.obj, self.attr, self.previous)

    
    