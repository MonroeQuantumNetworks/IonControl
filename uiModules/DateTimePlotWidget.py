'''
Created on Sep 6, 2014

@author: pmaunz
'''

from pyqtgraphAddons.DateAxisItem import DateAxisItem
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget


class DateTimePlotWidget(CoordinatePlotWidget):
    """This is the main widget for plotting data. It consists of a plot, a
       coordinate display, and custom buttons."""
    def __init__(self,parent=None):
        self.dateAxisItem = DateAxisItem('bottom')
        super(DateTimePlotWidget,self).__init__(parent, axisItems={'bottom': self.dateAxisItem})



if __name__ == '__main__':
    from PyQt4 import QtGui
    from uiModules import CoordinatePlotWidget as cw
    
    cw.icons_dir = '.\\..\\ui\\icons\\'
    cw.range_icon_file = cw.icons_dir + 'unity-range'
    cw.holdZero_icon_file = cw.icons_dir + 'hold-zero'
    import sys    
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    myPlotWidget = DateTimePlotWidget()
    MainWindow.setCentralWidget(myPlotWidget)
    pi = myPlotWidget.getItem(0, 0)
    pi.plot(x = [0,3600,7200,10800], y = [9,16,25,36])

    MainWindow.show()
    sys.exit(app.exec_())
    
