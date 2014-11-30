

def updateComboBoxItems( combo, items, selected=None):
    """Update the items in a combo Box,
    if the selected item is still there select it 
    do NOT emit signals during the process"""
    selected = str( combo.currentText() ) if selected is None else selected
    with BlockSignals(combo):
        combo.clear()
        combo.addItems( items )
        if selected in items:
            combo.setCurrentIndex( combo.findText(selected))
    return combo.currentText()


class BlockSignals:
    """Encapsulate blockSignals in __enter__ __exit__ idiom"""
    def __init__(self, widget):
        self.widget = widget
    
    def __enter__(self):
        self.oldstate = self.widget.blockSignals(True)
        return self.widget

    def __exit__(self, exittype, value, traceback):
        self.widget.blockSignals(self.oldstate)

def saveColumnWidth( tableView ):
    return [tableView.columnWidth(i) for i in range(0, tableView.model().columnCount())]

def restoreColumnWidth( tableView, widthData ):
    for column, width in zip( range(0, tableView.model().columnCount()), widthData ):
        tableView.setColumnWidth(column, width)
     
    