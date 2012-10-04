#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      cnchou
#
# Created:     28/07/2012
# Copyright:   (c) cnchou 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
import gtk, gobject, pango, math
import numpy
import threading, socket, time
##import matplotlib
##matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
#import matplotlib.pylab as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from numpy import arange, sin, pi
#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.axes import Subplot
from matplotlib.axes import Axes
#import socket, DDSdriver
#import DDS_GUI_Sandia_AQC
#import embedding_in_qt4
#import Simple_window_Qt4
from pylab import *
import matplotlib.patches as patches
import matplotlib.path as path
from PyQt4 import QtGui

##dirname = 'C:/Data'
##timestamp = time.strftime('_%m_%d_%Y_%H_%M_%S')
##filename =dirname +'APD_counts'+ timestamp + '.txt'
##
##if not os.path.isdir(dirname):
##    os.mkdir(dirname)


class PConGui_Qt4(QtGui.QWidget):
    def __init__(self):
        super(PConGui_Qt4, self).__init__()

        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        self.setWindowTitle("Pulse contnroller")


        self.figure = plt.figure()
        self.trace1 = self.figure.add_subplot(211)
        self.plot = FigureCanvas(self.figure)
        #self.line1, = self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
        self.trace2 = self.figure.add_subplot(212)
        #self.trace2.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
        self.plot.draw()

        hbox.addStretch(1)

        button_run = QtGui.QPushButton("Run",self)
        hbox.addWidget(button_run)

        button_stop = QtGui.QPushButton("Stop",self)
        hbox.addWidget(button_stop)


        vbox.addStretch(1)
        vbox.addWidget(QtGui.QLabel("PConGui_Qt4"))
        vbox.addLayout(hbox)
        vbox.addWidget(self.plot)
        self.setLayout(vbox)
        self.show()

        execfile('c:\AQCv2\Test_GUI.py')


def main():

    app = QtGui.QApplication(sys.argv)
    ex = PConGui_Qt4()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()