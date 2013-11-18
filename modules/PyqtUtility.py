

def updateComboBoxItems( combo, items):
    """Update the items in a combo Box,
    if the selected item is still there select it 
    do NOT emit signals during the process"""
    oldState = str( combo.currentText() )
    with BlockSignals(combo):
        combo.clear()
        combo.addItems( items )
        if oldState in items:
            combo.setCurrentIndex( combo.findText(oldState))
    return combo.currentText()


class BlockSignals:
    """Encapsulate blockSignals in __enter__ __exit__ idiom"""
    def __init__(self, widget):
        self.widget = widget
    
    def __enter__(self):
        self.oldstate = self.widget.blockSignals(True)

    def __exit__(self, type, value, traceback):
        self.widget.blockSignals(self.oldstate)
