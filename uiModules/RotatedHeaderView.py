from PyQt4 import QtGui, QtCore


class RotatedHeaderView( QtGui.QHeaderView ):
    def __init__(self, orientation, parent=None ):
        super(RotatedHeaderView, self).__init__(orientation, parent)
        self.setMinimumSectionSize(20)
        
    def paintSection(self, painter, rect, logicalIndex ):
        painter.save()
        painter.translate(rect.x()+rect.width(), rect.y())
        painter.rotate(90)
        newrect = QtCore.QRect(0,0,rect.height(),rect.width())
        super(RotatedHeaderView, self).paintSection(painter,newrect,logicalIndex)
        painter.restore()
               
    def sectionSizeHint(self, logicalIndex):
        return 10
    
    def minimumSizeHint(self):
        size = super(RotatedHeaderView, self).minimumSizeHint()
        size.transpose()
        return size

    def sizeHintForColumn(self, logicalIndex):
        return 10
    
    def sectionSizeFromContents(self, logicalIndex):
        size = super(RotatedHeaderView, self).sectionSizeFromContents(logicalIndex)
        size.transpose()
        return size
