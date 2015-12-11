from PyQt4 import QtGui, QtCore
import functools

def textSize(text):
    """return the size of a block of text"""
    defaultFontName = "Segoe UI"
    defaultFontSize = 9
    font = QtGui.QFont(defaultFontName,defaultFontSize,QtGui.QFont.Normal)
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
        if items:
            combo.addItems( items )
        index = combo.findText(selected)
        if index >= 0:
            combo.setCurrentIndex( index )
        else:
            combo.setCurrentIndex(0)
    return str(combo.currentText())


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

    
    