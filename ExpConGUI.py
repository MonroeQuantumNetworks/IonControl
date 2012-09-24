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
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.axes import Subplot
from matplotlib.axes import Axes
#import socket, DDSdriver
#import DDS_GUI_Sandia_AQC
from pylab import *
import matplotlib.patches as patches
import matplotlib.path as path

dirname = 'C:/Data'
timestamp = time.strftime('_%m_%d_%Y_%H_%M_%S')
filename =dirname +'APD_counts'+ timestamp + '.txt'

if not os.path.isdir(dirname):
    os.mkdir(dirname)

##def main():
##    pass
##
##if __name__ == '__main__':
##    main()


class ExpConGUI:
    def __init__(self,driver,file):#):#
        self.lock = threading.Lock()
        self.plotdatalength = 21
        self.plotdata=numpy.zeros((self.plotdatalength,2),'Float32')
        self.plotdata[:,0]=numpy.linspace(0, self.plotdatalength-1, self.plotdatalength)
        self.plotdata[:,1]=numpy.zeros(self.plotdatalength)#sin(self.plotdata[:,0]*2*numpy.pi/100)
        self.stateobj = {}
        self.ContPlot = False
        self.data_start = 3900
        self.us_MeasTime = 500
        self.hist_max = 30
        #self.index = 0


##        self.PCon = DDSdriver.DDSdriver()
##        self.PCon.register()
##
##        self.PCon.set('PARAMETER','datastart',self.data_start) #set the datastart value to the tree of variable
##        self.PCon.set('PARAMETER','us_MeasTime',self.us_MeasTime) #set the us_MeasTime value to the tree of variable
##        self.PCon.set_setprog('C:\AQUARIUS\prog\APDcounts.pp') # Load and sets teh .pp file at the given location

        self.PCon = driver#DDS_GUI_Sandia_AQC.DDS_gui()
        self.PCon.parameter_set('datastart',self.data_start)
        self.PCon.parameter_set('us_MeasTime',self.us_MeasTime)
        #self.PCon.parameter_set('addr',0)
        #self.PCon.parameter_set('hist_max',self.hist_max)
        self.PCon.pp_setprog('./prog/'+file)#DarkHist  Detect DarkHist
        self.PCon.pp_upload()

        self.n_of_data = self.PCon.get_datapoints()

        vbox = gtk.VBox(False, 0)
        hbox = gtk.HBox(False, 0)
        hbox1 = gtk.HBox(False, 0)
        hbox2 = gtk.HBox(False, 0)
        window = gtk.Window()
        #window.set_title(file)
        window.set_title("AQC Exp. Control")

##        window.connect("delete_event", self.on_quit_activate, None)
##        window.connect("destroy", self.on_quit_activate, None)

        Filename_label=gtk.Label("Pulse Sequence File")
        hbox1.pack_start(Filename_label,True,True,0)
        self.Filename_entry=gtk.Entry(max=0)
        hbox1.pack_start(self.Filename_entry,True,True,0)

        var_label = gtk.Label("Scan variable")
        hbox2.pack_start(var_label,True,True,0)
        self.var_entry = gtk.Combo()
        self.var_entry.set_value_in_list(False, True)
        #self.var_entry.set_popdown_strings()
        hbox2.pack_start(self.var_entry,True,True,0)


        frame = gtk.Frame("Plot")

        self.figure = plt.figure()
        self.trace1 = self.figure.add_subplot(211)
        self.plot = FigureCanvas(self.figure)
        self.line1, = self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
        self.trace2 = self.figure.add_subplot(212)
        #self.trace2.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
        self.plot.draw()

        frame.add(self.plot)
##        ion()
##        line, = plot(self.plotdata[:,0],self.plotdata[:,1],'r')
##        draw()

##        self.line1, = plt.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
##        plt.draw()

        button_run = gtk.Button("Run")
        hbox.pack_start(button_run, True, True, 0)

        button_stop = gtk.Button("Stop")
        hbox.pack_start(button_stop, True, True, 0)

        button_run.connect("clicked", self.cont_plot)
        button_stop.connect("clicked", self.stop_plot)

        vbox.pack_start(hbox, False, False, 1)
        vbox.pack_start(hbox1, False, False, 1)
        vbox.pack_start(hbox2, False, False, 1)
        vbox.pack_start(frame, True, True, 1)
        window.add(vbox)
        window.show_all()

    def cont_plot(self, widget, data = None):
        self.ContPlot = True
##            self.plotdata[0:99,1]=self.plotdata[1:100,1]
##            self.plotdata[100,1]= 0
        self.update_plot()
##            self.trace1.clear()

##            self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
    def update_plot(self):
        if(self.ContPlot == True):
            #print self.PCon.pp_is_running()
            t1 = time.time()
            self.PCon.pp_run_2()
            readoutOK=self.PCon.update_count()
            t2 = time.time()
            if(readoutOK):
                #print self.PCon.pp_is_running()
                #addr = self.PCon.read_memory(72,1)
                #print "%d repetitions in %.6f seconds." %(addr - self.data_start-1, t2-t1)
##            #self.index = self.index+1 and not self.PCon.pp_is_running()
##            #print self.index
##            self.PCon.set_runprog()                #Runs the loaded .pp file
##
##            #time.sleep(0.1)
##            counts=self.PCon.read_memory()         #Extracts the data from the memory
##            #print counts
##            #counts1=self.PCon.read_memory()         #Extracts the data from the memory
##            #print counts1

##            if not (numpy.size(counts)==1):

                t1 = time.time()
##              pyplot implementation
##                self.trace1.clear()
##                self.trace2.clear()
##                self.plotdata[0:self.plotdatalength-1,1] = self.plotdata[1:self.plotdatalength,1]
##                self.plotdata[self.plotdatalength-1,1] = numpy.mean(self.PCon.data[:,1])
##                self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
##                self.trace2.hist(self.PCon.data[:,1],arange(0,self.hist_max+1), normed = 1)
##                self.plot.draw()
##              animation implementation
                self.plotdata[0:self.plotdatalength-1,1] = self.plotdata[1:self.plotdatalength,1]
                self.plotdata[self.plotdatalength-1,1] = numpy.mean(self.PCon.data[:,1])
                self.line1.set_ydata(self.plotdata[:,1])
                ymax = numpy.max(self.plotdata[:,1])
                ymin = numpy.min(self.plotdata[:,1])
                self.trace1.set_ylim(ymin-0.1*(ymax-ymin)-0.01, ymax+0.1*(ymax-ymin)+0.01)

                self.trace2.clear()
                #self.trace2.hist(self.PCon.data[:,1],arange(0,self.hist_max+1), normed = 1)
                self.update_hist(self.PCon.data[:,1])
                self.plot.draw()
                t2 = time.time()
                print 'Plot time %.6f seconds' %(t2-t1)
                #print "addr = %d" %addr
            threading.Timer(0.005, self.update_plot,()).start()
##        else:
##            self.stop_plot()

    def update_hist(self, data):
        #Animating the histogram, see http://matplotlib.sourceforge.net/examples/animation/histogram.html
        n, bins = numpy.histogram(data, arange(0,self.hist_max+1), normed = True)

        # get the corners of the rectangles for the histogram
        left = np.array(bins[:-1])
        right = np.array(bins[1:])
        bottom = np.zeros(len(left))
        top = bottom + n
        nrects = len(left)

        nverts = nrects*(1+3+1)
        verts = np.zeros((nverts, 2))
        codes = np.ones(nverts, int) * path.Path.LINETO
        codes[0::5] = path.Path.MOVETO
        codes[4::5] = path.Path.CLOSEPOLY
        verts[0::5,0] = left
        verts[0::5,1] = bottom
        verts[1::5,0] = left
        verts[1::5,1] = top
        verts[2::5,0] = right
        verts[2::5,1] = top
        verts[3::5,0] = right
        verts[3::5,1] = bottom

        barpath = path.Path(verts, codes)
        patch = patches.PathPatch(barpath, facecolor='red', edgecolor='yellow', alpha=0.5)
        self.trace2.add_patch(patch)

        self.trace2.set_xlim(left[0], right[-1])
        self.trace2.set_ylim(bottom.min(), top.max())



    def stop_plot(self, widget, data = None):
        self.ContPlot = False
        self.PCon.user_stop()
##        self.plotdata[:,0]=numpy.linspace(0, 100, 101)
##        self.plotdata[:,1]=numpy.sin(self.plotdata[:,0]*2*numpy.pi/100)
##        return

    def KeepPlotting(self):
        return self.ContPlot

##    def on_quit_activate(self, widget, event, data = None):
##        #self.params.save_state("Params")
##        #self.plug.close()
##        gtk.main_quit()
##        return True

##app = ExpConGUI()
##gtk.gdk.threads_init()
##gtk.gdk.threads_enter()
##
##try:
##    pass
##    gtk.main()
##finally:
##    print "Closing..."
##gtk.gdk.threads_leave()