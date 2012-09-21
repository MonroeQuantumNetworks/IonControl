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
import pango, math
import numpy
import threading,  time
##import matplotlib
##matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
#import matplotlib.pylab as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
import matplotlib.backends.backend_pdf
from numpy import arange, sin, pi
#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.axes import Subplot
from matplotlib.axes import Axes
from pylab import *
import matplotlib.patches as patches
import matplotlib.path as path
import coltree_Qt

from PyQt4 import QtGui, QtCore
import shutil

dirname = 'C:/Data/'



##def main():
##    pass
##
##if __name__ == '__main__':
##    main()


class ExpConGUI_Qt(QtGui.QWidget):
    def __init__(self,driver,file):#):#
        super(ExpConGUI_Qt, self).__init__()
        #self.lock = threading.Lock()
        self.threads = []
        self.ppfile = './prog/'+file
        self.plotdatalength = 21
        self.plotdata=numpy.zeros((self.plotdatalength,2),'Float32')
        self.plotdata[:,0]=numpy.linspace(0, self.plotdatalength-1, self.plotdatalength)
        self.plotdata[:,1]=numpy.zeros(self.plotdatalength)#sin(self.plotdata[:,0]*2*numpy.pi/100)
        self.stateobj = {}
        self.ind = {}
        self.filename = []
        self.timestamp = time.strftime('%Y%m%d_%H%M%S')
##        self.ContPlot = False
        self.run_exp = True
        self.pause = False
        self.n_reps = 100
        self.data_start = 4000 - self.n_reps+1 #changed CWC 09122012
        #self.us_MeasTime = 500
        self.hist_max = 30
##        self.timer = QtCore.QTimer()
##        self.timer.timeout.connect(self.update_plot)
        self.t1 = time.time()
        self.scan_types =['Continuous','Frequency','Time','Voltage']
        self.text_to_write = ''
        #self.index = 0


##        self.PCon = DDSdriver.DDSdriver()
##        self.PCon.register()
##
##        self.PCon.set('PARAMETER','datastart',self.data_start) #set the datastart value to the tree of variable
##        self.PCon.set('PARAMETER','us_MeasTime',self.us_MeasTime) #set the us_MeasTime value to the tree of variable
##        self.PCon.set_setprog('C:\AQUARIUS\prog\APDcounts.pp') # Load and sets teh .pp file at the given location

        self.PCon = driver#DDS_GUI_Sandia_AQC.DDS_gui()

        #self.PCon.parameter_set('us_MeasTime',self.us_MeasTime)
        #self.PCon.parameter_set('addr',0)
        #self.PCon.parameter_set('hist_max',self.hist_max)
        self.PCon.pp_setprog(str(self.ppfile))#DarkHist  Detect DarkHist
        self.PCon.pp_upload()

        self.n_of_data = self.PCon.get_datapoints()

        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        hbox3 = QtGui.QHBoxLayout()
        hbox4 = QtGui.QHBoxLayout()
        #window.set_title(file)
        self.setWindowTitle("AQC Exp. Control")

##        window.connect("delete_event", self.on_quit_activate, None)
##        window.connect("destroy", self.on_quit_activate, None)

        Filename_label=QtGui.QLabel("Pulse Sequence File")
        hbox1.addWidget(Filename_label)
        self.Filename_entry=QtGui.QLineEdit()
        self.Filename_entry.setText(self.ppfile)
        hbox1.addWidget(self.Filename_entry)

        scan_label = QtGui.QLabel("Scan type")
        hbox2.addWidget(scan_label)
        self.scan_entry = QtGui.QComboBox()
        for n in range(len(self.scan_types)):
            self.scan_entry.addItem(self.scan_types[n])
        hbox2.addWidget(self.scan_entry)
        self.scan_entry.currentIndexChanged.connect(self.update_scan_type)

        var_label = QtGui.QLabel("Scan variable")
        hbox2.addWidget(var_label)
        self.var_entry = QtGui.QComboBox()
        self.PCon.params.update_defs()
        for key in self.PCon.params.defs:
            self.var_entry.addItem(key)
        #self.var_entry.set_popdown_strings()
        self.var_entry.setDisabled(True)
        hbox2.addWidget(self.var_entry)
        self.var_entry.currentIndexChanged.connect(self.update_var)

        self.Load_SW_label = QtGui.QLabel("Load atom")
        self.Load_SW_cb = QtGui.QCheckBox()
        self.Load_SW_cb.setTristate(False)
        self.Load_SW_cb.setCheckState(True)
        hbox4.addWidget(self.Load_SW_label)
        hbox4.addWidget(self.Load_SW_cb)

        self.Cool_SW_label = QtGui.QLabel("PG cooling")
        self.Cool_SW_cb = QtGui.QCheckBox()
        self.Cool_SW_cb.setTristate(False)
        self.Cool_SW_cb.setCheckState(True)
        hbox4.addWidget(self.Cool_SW_label)
        hbox4.addWidget(self.Cool_SW_cb)

        self.OP_SW_label = QtGui.QLabel("O. Pumping")
        self.OP_SW_cb = QtGui.QCheckBox()
        self.OP_SW_cb.setTristate(False)
        self.OP_SW_cb.setCheckState(True)
        hbox4.addWidget(self.OP_SW_label)
        hbox4.addWidget(self.OP_SW_cb)

        self.Check_SW_label = QtGui.QLabel("Check atom")
        self.Check_SW_cb = QtGui.QCheckBox()
        self.Check_SW_cb.setTristate(False)
        self.Check_SW_cb.setCheckState(True)
        hbox4.addWidget(self.Check_SW_label)
        hbox4.addWidget(self.Check_SW_cb)

        self.range_low_label = QtGui.QLabel("Start")
        self.scan_range_low_sb = QtGui.QDoubleSpinBox()
        self.scan_range_low_sb.setRange(-10, 10)
        self.scan_range_low_sb.setSingleStep(0.1)
        self.scan_range_low_sb.setValue(0)
        hbox3.addWidget(self.range_low_label)
        hbox3.addWidget(self.scan_range_low_sb)

        self.range_high_label = QtGui.QLabel("Stop")
        self.scan_range_high_sb = QtGui.QDoubleSpinBox()
        self.scan_range_high_sb.setRange(-10, 10)
        self.scan_range_high_sb.setSingleStep(0.1)
        self.scan_range_high_sb.setValue(10)
        hbox3.addWidget(self.range_high_label)
        hbox3.addWidget(self.scan_range_high_sb)

        self.n_label = QtGui.QLabel("N. of points")
        self.n_points_sb = QtGui.QSpinBox()
        self.n_points_sb.setRange(1, 1000)
        self.n_points_sb.setSingleStep(1)
        self.n_points_sb.setValue(30)
        hbox3.addWidget(self.n_label)
        hbox3.addWidget(self.n_points_sb)

        self.scan_range_low_sb.setDisabled(True)
        self.scan_range_high_sb.setDisabled(True)
        self.n_points_sb.setDisabled(True)
        self.var_entry.setDisabled(True)

        self.n_index_label = QtGui.QLabel("Current point:")
        self.n_index = QtGui.QLabel("0")
        hbox3.addWidget(self.n_index_label)
        hbox3.addWidget(self.n_index)

        self.shuffle_label = QtGui.QLabel("Shuffle scan")
        self.shuffle_cb = QtGui.QCheckBox()
        self.shuffle_cb.setTristate(False)
        self.shuffle_cb.setCheckState(True)
        self.shuffle_cb.setDisabled(True)
        hbox3.addWidget(self.shuffle_label)
        hbox3.addWidget(self.shuffle_cb)

        self.rep_label = QtGui.QLabel("Rep. per point")
        self.rep_sb = QtGui.QSpinBox()
        self.rep_sb.setRange(1, 1000)
        self.rep_sb.setSingleStep(1)
        self.rep_sb.setValue(self.n_reps)
        hbox3.addWidget(self.rep_label)
        hbox3.addWidget(self.rep_sb)
        self.data_start = 4000 - self.n_reps+1; #Changed CWC 09122012
        self.PCon.parameter_set('datastart',self.data_start)

        self.figure = plt.figure()
        self.trace1 = self.figure.add_subplot(211)
        self.plot = FigureCanvas(self.figure)
        #self.plotdata[:,1] = numpy.random.shuffle(arange(21))
        self.line1, = self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
        self.trace2 = self.figure.add_subplot(212)
        #self.trace2.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
        self.plot.draw()


##        ion()
##        line, = plot(self.plotdata[:,0],self.plotdata[:,1],'r')
##        draw()

##        self.line1, = plt.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
##        plt.draw()
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)

        self.button_upParams = QtGui.QPushButton("Update params.",self)
        hbox.addWidget(self.button_upParams)

        self.button_run = QtGui.QPushButton("Run",self)
        hbox.addWidget(self.button_run)

        self.button_pause = QtGui.QPushButton("Pause",self)
        self.button_pause.setDisabled(True)
        hbox.addWidget(self.button_pause)

        self.button_resume = QtGui.QPushButton("Resume",self)
        self.button_resume.setDisabled(True)
        hbox.addWidget(self.button_resume)

        self.button_stop = QtGui.QPushButton("Stop",self)
        self.button_stop.setDisabled(True)
        hbox.addWidget(self.button_stop)

        self.button_upParams.clicked.connect(self.update_params)
        self.button_run.clicked.connect(self.run_scan)
        self.button_pause.clicked.connect(self.pause_scan)
        self.button_resume.clicked.connect(self.resume_scan)
        self.button_stop.clicked.connect(self.stop_scan)

        vbox.addStretch(1)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox4)
        vbox.addLayout(hbox3)
        #vbox.addWidget(self.plot)
        self.setLayout(vbox)
        self.show()

    def update_pp_filename(self):
        self.Filename_entry.setText(self.ppfile)

    def update_params(self):
        self.PCon.params.update_defs()
        self.PCon.pp_upload()

    def update_var(self):
        self.n_index.setText('0')

    def update_scan_type(self):
        self.n_index.setText('0')
        if (self.scan_entry.currentText()=='Continuous'):
            self.PCon.params.update_defs()
            self.shuffle_cb.setDisabled(True)
            self.scan_range_low_sb.setDisabled(True)
            self.scan_range_high_sb.setDisabled(True)
            self.n_points_sb.setDisabled(True)
            self.var_entry.setDisabled(True)
        elif (self.scan_entry.currentText()=='Frequency'):
            self.PCon.params.update_defs()
            self.shuffle_cb.setDisabled(False)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(-30,100)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(-30,100)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            for key in sorted(self.PCon.params.defs.iterkeys()):#self.PCon.params.defs:
                if (key[:2]=='F_' or key[:2]=='f_'):
                    self.var_entry.addItem(key)
            self.var_entry.setEnabled(True)
        elif (self.scan_entry.currentText()=='Time'):
            self.PCon.params.update_defs()
            self.shuffle_cb.setDisabled(False)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(0,100)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(1,1000)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            for key in sorted(self.PCon.params.defs.iterkeys()):
                if (key[:3]=='ns_' or key[:3]=='NS_' or key[:3]=='us_' or key[:3]=='US_' or key[:3]=='ms_' or key[:3]=='MS_'):
                    self.var_entry.addItem(key)
            self.var_entry.setEnabled(True)
        elif (self.scan_entry.currentText()=='Voltage'):
            self.PCon.params.update_defs()
            self.shuffle_cb.setDisabled(False)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(-0.1,5)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(-0.1,5)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            for key in sorted(self.PCon.params.defs.iterkeys()):
                if (key[:2]=='V_' or key[:2]=='v_'):
                    self.var_entry.addItem(key)
            self.var_entry.setEnabled(True)
        else:
            print "Unknow scan type."

    def init_scan(self, plotlength):
        self.plotdatalength = plotlength
        self.plotdata=numpy.zeros((self.plotdatalength,2),'Float32')

    def run_scan(self):
        self.run_exp = True
        self.pause = False
        self.button_run.setDisabled(True)
        self.button_resume.setDisabled(True)
        self.button_pause.setDisabled(False)
        self.button_stop.setDisabled(False)

#Determine if a certain step in the pulse sequence Load_cool_exp_check should be skipped CWC 09172012
        if (self.Load_SW_cb.isChecked() == True):
            self.PCon.parameter_set('LOAD_SWITCH', 1)
        else:
            self.PCon.parameter_set('LOAD_SWITCH', 0)

        if (self.Cool_SW_cb.isChecked() == True):
            self.PCon.parameter_set('COOL_SWITCH', 1)
        else:
            self.PCon.parameter_set('COOL_SWITCH', 0)

        if (self.OP_SW_cb.isChecked() == True):
            self.PCon.parameter_set('OP_SWITCH', 1)
        else:
            self.PCon.parameter_set('OP_SWITCH', 0)

        if (self.Check_SW_cb.isChecked() == True):
            self.PCon.parameter_set('CHECK_SWITCH', 1)
        else:
            self.PCon.parameter_set('CHECK_SWITCH', 0)

        self.PCon.params.save_params("Params")
        self.PCon.update_state()
        coltree_Qt.save_state("State", self.PCon.state)

        self.timestamp = time.strftime('%Y%m%d_%H%M%S')
        if not os.path.isdir(dirname + self.timestamp + '/'):
            os.mkdir(dirname + self.timestamp + '/')
        shutil.copy2(str(self.ppfile), dirname + self.timestamp + '/')
        shutil.copy2('config.ddscon', dirname + self.timestamp + '/')
        self.filename = dirname + self.timestamp + '/' + str(self.scan_entry.currentText()) + '_scan'
        if (self.scan_entry.currentText()!='Continuous'):
            self.filename+= '_' + str(self.var_entry.currentText())
        fd = file(self.filename+'.txt', "a")

        rep_per_point = self.rep_sb.value()
        self.PCon.parameter_set('datastart', 4000-rep_per_point+1) #changed CWC 09132012
        #Log the value of the parameters
        self.update_params()

        params_to_write = 'Pulse Programmer (pp) file:'+str(self.ppfile)+'\n'
        params_to_write+= 'Parameters: '
        for key in self.PCon.params.defs:
            params_to_write+= str(key)+': '+ str(self.PCon.params.defs[key])+ '; '
        params_to_write+='\n'

        stateobj_to_write = 'Stateobj: '
        for key in self.PCon.stateobj:
            if (key[:3] == 'DDS' or key[:3] == 'DAC' or key == 'SHUTR'):
                stateobj_to_write+=key+': '+str(self.PCon.stateobj[key][0].value())+'; '
        stateobj_to_write+='\n'

        self.PCon.data = numpy.zeros([rep_per_point,1], 'Int32')
        if (self.scan_entry.currentText()=='Continuous'):
            self.text_to_write = 'Continuous scan.\n'
            self.text_to_write+=params_to_write
            self.text_to_write+=stateobj_to_write
            fd.write(self.text_to_write)
            fd.close()
            self.init_scan(21)
            self.plotdata[:,0]=numpy.linspace(0, self.plotdatalength-1, self.plotdatalength)
##            self.trace1.clear()
##            self.line1, = self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
            #self.cont_plot()

            plot_thread = PlotThread(self)
            self.threads.append(plot_thread)
            exp_thread = ContExpThread(self, plot_thread)
            self.threads.append(exp_thread)
            plot_thread.start()
            exp_thread.start()

        elif (self.scan_entry.currentText()=='Frequency' or self.scan_entry.currentText()=='Time' or self.scan_entry.currentText()=='Voltage'):
            self.init_scan(self.n_points_sb.value())
            self.text_to_write = str(self.scan_entry.currentText()) + ' scan.\n'
            self.text_to_write+=params_to_write
            self.text_to_write+=stateobj_to_write
            scan_vals = numpy.linspace(self.scan_range_low_sb.value(), self.scan_range_high_sb.value(),self.n_points_sb.value())
            scan_vals = map(lambda x: float(round(1000*x)/1000), scan_vals)
            self.plotdata[:,0]=scan_vals
            self.ind = {}
            for n in range(len(scan_vals)):
                self.ind[scan_vals[n]]=n
            #print self.shuffle_cb.isChecked()
            if (self.shuffle_cb.isChecked() == True):
                numpy.random.shuffle(scan_vals)
                #print scan_vals[0]

            self.text_to_write+= 'Scan variable: ' + str(self.var_entry.currentText()) + '\n'
            self.text_to_write+= 'Range:' + str(self.scan_range_low_sb.value()) + ' to ' + str(self.scan_range_high_sb.value()) + '\n'
            self.text_to_write+= 'Number of points: ' + str(self.n_points_sb.value()) +'\n'
            self.text_to_write+= 'Rep. per point: '+ str(self.rep_sb.value()) +'\n'
            self.text_to_write+= 'Scan var. val.'+'\t'+'Meas. Avg.'+'\t'
            for n in range(self.rep_sb.value()):
                self.text_to_write += 'Rep. #'+str(n)+'\t'
            self.text_to_write +='\n'
            fd.write(self.text_to_write)
            fd.close()
##            self.trace1.clear()
##            self.line1, = self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'ro')
            plot_thread = PlotThread(self)
            self.threads.append(plot_thread)
            exp_thread = ExpThread(self, scan_vals, plot_thread)#self) Changed the receiver for the update event from self (GUI) to plot_thread
            self.threads.append(exp_thread)
            plot_thread.start()
            exp_thread.start()
        else:
            print "Unknow scan type."

    def pause_scan(self):
        self.pause = True
        self.button_run.setDisabled(False)
        self.button_resume.setDisabled(False)
        self.button_pause.setDisabled(True)
        self.button_stop.setDisabled(False)

    def resume_scan(self):
        self.pause = False
        self.button_run.setDisabled(True)
        self.button_resume.setDisabled(True)
        self.button_pause.setDisabled(False)
        self.button_stop.setDisabled(False)

    def stop_scan(self):
        self.run_exp = False
        self.pause = False
        self.button_run.setDisabled(False)
        self.button_resume.setDisabled(True)
        self.button_pause.setDisabled(True)
        self.button_stop.setDisabled(True)
        self.PCon.user_stop() #Added for proper stop CWC 09172012

        #pp = matplotlib.backends.backend_pdf.PdfPages(self.filename+'.pdf')
        #pp.savefig(self.figure)
        #self.figure.savefig(pp, format='pdf')
        #pp.close()
        #print 'Saving figure...'

        #self.fit_result()

##    def cont_plot(self):
##        self.ContPlot = True
##
##        #self.timer.start(0.001)
##        self.update_plot()

    def update_plot_save_data(self, scan_index, new_mean, new_data):
        if (self.scan_entry.currentText()=='Continuous'):
            self.plotdata[0:self.plotdatalength-1,1] = self.plotdata[1:self.plotdatalength,1]
            self.plotdata[self.plotdatalength-1,1] = new_mean
            self.line1.set_ydata(self.plotdata[:,1])
        elif (self.scan_entry.currentText()=='Frequency'):
            self.plotdata[scan_index,1] = new_mean
            self.line1.set_ydata(self.plotdata[:,1])
        elif (self.scan_entry.currentText()=='Time'):
            self.plotdata[scan_index,1] = new_mean
            self.line1.set_ydata(self.plotdata[:,1])
##            self.trace1.clear()
##            self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')

        #print "%d, %d" %(len(self.plotdata[:,0]),len(self.plotdata[:,1]))
        ymax = numpy.max(self.plotdata[:,1])
        ymin = numpy.min(self.plotdata[:,1])
        self.trace1.set_ylim(ymin-0.1*(ymax-ymin)-0.01, ymax+0.1*(ymax-ymin)+0.01)

        self.trace2.clear()
        #self.trace2.hist(self.PCon.data[:,1],arange(0,self.hist_max+1), normed = 1)
        self.update_hist(new_data)
        self.plot.draw()

        if (self.scan_entry.currentText()=='Continuous'):
            self.text_to_write = str(self.plotdata[scan_index,1])+'\t'
        else:
            self.text_to_write = str(self.plotdata[scan_index,0]) + '\t' + str(self.plotdata[scan_index,1])+'\t'
        for n in range(self.rep_sb.value()):
            self.text_to_write += str(new_data[n])+'\t'
        self.text_to_write += '\n'
        fd = file(self.filename+'.txt', "a")
        fd.seek(0,2)
        fd.write(self.text_to_write)
        fd.close()
        #numpy.savetxt(self.filename,new_data,fmt='%i')

##    def update_plot(self):
##        if(self.ContPlot == True):
##            #print self.PCon.pp_is_running()
##            #t1 = time.time()
##            self.PCon.pp_run_2()
##            readoutOK=self.PCon.update_count()
##            #t2 = time.time()
##            if(readoutOK):
##                #print self.PCon.pp_is_running()
##                #addr = self.PCon.read_memory(13,1)
##                #print "%d repetitions in %.6f seconds." %(addr - self.data_start-1, t2-t1)
####            #self.index = self.index+1 and not self.PCon.pp_is_running()
####            #print self.index
####            self.PCon.set_runprog()                #Runs the loaded .pp file
####
####            #time.sleep(0.1)
####            counts=self.PCon.read_memory()         #Extracts the data from the memory
####            #print counts
####            #counts1=self.PCon.read_memory()         #Extracts the data from the memory
####            #print counts1
##
####            if not (numpy.size(counts)==1):
##
##                #t1 = time.time()
####              pyplot implementation
####                self.trace1.clear()
####                self.trace2.clear()
####                self.plotdata[0:self.plotdatalength-1,1] = self.plotdata[1:self.plotdatalength,1]
####                self.plotdata[self.plotdatalength-1,1] = numpy.mean(self.PCon.data[:,1])
####                self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
####                self.trace2.hist(self.PCon.data[:,1],arange(0,self.hist_max+1), normed = 1)
####                self.plot.draw()
####              animation implementation
##                self.plotdata[0:self.plotdatalength-1,1] = self.plotdata[1:self.plotdatalength,1]
##                self.plotdata[self.plotdatalength-1,1] = numpy.mean(self.PCon.data[:,1])
##                self.line1.set_ydata(self.plotdata[:,1])
##                ymax = numpy.max(self.plotdata[:,1])
##                ymin = numpy.min(self.plotdata[:,1])
##                self.trace1.set_ylim(ymin-0.1*(ymax-ymin)-0.01, ymax+0.1*(ymax-ymin)+0.01)
##
##                self.trace2.clear()
##                #self.trace2.hist(self.PCon.data[:,1],arange(0,self.hist_max+1), normed = 1)
##                self.update_hist(self.PCon.data[:,1])
##                self.plot.draw()
##                t2 = time.time()
##                #print 'Cycle time %.6f seconds' %(t2-self.t1)
##                self.t1 = t2
##                #print 'Plot time %.6f seconds' %(t2-t1)
##                #print "addr = %d" %addr
##            threading.Timer(0.005, self.update_plot,()).start()
##            #self.timer.singleShot(0.005,self.update_plot)
####        else:
####            self.stop_plot()

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

##    def fit_result(self):
##        if (self.scan_entry.currentText()=='Frequency'):
##            popt, pcov = curve_fit(Sinc, x, yn)

    def Sinc(f,f0,Omega0,a,b,c):
        return np.square(Omega0)/(np.square(Omega0)+2*np.pi*np.square(f-f0))*np.square(np.sin(np.sqrt(np.square(Omega0)+np.square(f-f0))/2*b))+c

    def stop_plot(self, widget, data = None):
        self.ContPlot = False
        self.timer.stop()
        self.PCon.user_stop()


    def KeepPlotting(self):
        return self.ContPlot

    def __del__(self):
        for t in self.threads:
          running = t.running()
          t.stop()
          if not t.finished():
            t.wait()

    def closeEvent(self, event):
        self.PCon.ExpConGUIstarted = False

##class UpdatePlotThread(QtCore.QThread):
##    def __init__(self, GUI):
##        super(UpdatePlotThread, self).__init__()
##
##    def stop(self):
##        self.stopped = 1
##    def run(self):
##
##    def customEvent(self):
##        qApp.lock()
##        GUI.plotdata[0:GUI.plotdatalength-1,1] = GUI.plotdata[1:GUI.plotdatalength,1]
##        GUI.plotdata[self.plotdatalength-1,1] = numpy.mean(self.PCon.data[:,1])
##        GUI.line1.set_ydata(GUI.plotdata[:,1])
##        ymax = numpy.max(self.plotdata[:,1])
##        ymin = numpy.min(self.plotdata[:,1])
##        GUI.trace1.set_ylim(ymin-0.1*(ymax-ymin)-0.01, ymax+0.1*(ymax-ymin)+0.01)
##
##        GUI.trace2.clear()
##        #self.trace2.hist(self.PCon.data[:,1],arange(0,self.hist_max+1), normed = 1)
##        GUI.update_hist(self.PCon.data[:,1])
##        GUI.plot.draw()
##        qApp.unlock()

class ExpThread(QtCore.QThread):
    def __init__(self, GUI, scan_vals, receiver):
        super(ExpThread, self).__init__()
        self.GUI = GUI
        self.receiver = receiver
        self.scan_vals = scan_vals
        temp = self.GUI.PCon.parameter_read(str(self.GUI.var_entry.currentText())).split()
        self.init_val = float(temp[1])
        self.stopped = 0
        self.t1 = time.time()
        self.connect( self, QtCore.SIGNAL("Done_one_point"), receiver.update_plot_save_data )
        self.connect( self, QtCore.SIGNAL("Done_scanning"), receiver.stop )

    def run(self):
        self.GUI.PCon.update_state()
        coltree_Qt.save_state("State", self.GUI.PCon.state)
        n = 0
        while (self.stopped == 0 and self.GUI.run_exp ==True and n<self.GUI.n_points_sb.value()):
            while (self.stopped == 0 and self.GUI.pause == True):
                time.sleep(0.1)
            current_scan_val = self.scan_vals[n]

            self.GUI.PCon.parameter_set(self.GUI.var_entry.currentText(), current_scan_val)

            self.GUI.PCon.pp_run()
            t3=time.time()
            readoutOK = self.GUI.PCon.update_count()
            t4=time.time()

            #print "pp readout time %3f sec" %(t4-t3)
            if (readoutOK and not self.GUI.PCon.pp_is_running()):
                self.emit(QtCore.SIGNAL("Done_one_point"), self.GUI.ind[current_scan_val], numpy.mean(self.GUI.PCon.data[:,1]), self.GUI.PCon.data[:,1])
##                print self.GUI.ind[current_scan_val]
##                print current_scan_val
                if (time.time()-self.t1) < 0.05:
                    time.sleep(0.03)
                t2 = time.time()
                print 'ExpThread cycle time %.6f seconds' %(t2-self.t1)
                self.t1 = t2

                # TODO: make these memory reference relative
                numBins = self.GUI.PCon.read_memory(2999,1)
                atomReuseArray =  self.GUI.PCon.read_memory(3000,100)
                atomReuseArray = numpy.resize(atomReuseArray,numBins)
                print "mean reuse number %.1f" %numpy.mean(atomReuseArray)
                print atomReuseArray
                #print numpy.std(atomReuseArray)

            n+=1
            self.GUI.n_index.setText(str(n))
        self.GUI.PCon.restore_state(self.GUI.PCon.state)
        #self.GUI.stop_scan()
        self.emit(QtCore.SIGNAL("Done_scanning"))
        #self.GUI.fit_result()
        self.GUI.PCon.parameter_set(str(self.GUI.var_entry.currentText()), self.init_val)

    def stop(self):
        self.stopped = 1

    def __del__(self):
        self.stopped = 1
        self.wait()

class ContExpThread(QtCore.QThread):
    def __init__(self, GUI, receiver):
        super(ContExpThread, self).__init__()
        self.GUI = GUI
        self.receiver = receiver
        self.stopped = 0
        self.t1 = time.time()
        self.connect( self, QtCore.SIGNAL("Done_one_point"), self.receiver.update_plot_save_data )
        self.connect( self, QtCore.SIGNAL("Done_scanning"), receiver.stop )

    def run(self):
        self.GUI.PCon.update_state()
        coltree_Qt.save_state("State", self.GUI.PCon.state)
        while (self.stopped == 0 and self.GUI.run_exp ==True):
            while (self.stopped == 0 and self.GUI.pause == True):
                time.sleep(0.1)
            self.GUI.PCon.pp_run_2()
            readoutOK = self.GUI.PCon.update_count()
            if (readoutOK and not self.GUI.PCon.pp_is_running()):
                #print(numpy.mean(self.GUI.PCon.data[:,1]))
                self.emit(QtCore.SIGNAL("Done_one_point"), 0, numpy.mean(self.GUI.PCon.data[:,1]), self.GUI.PCon.data[:,1])
                if (time.time()-self.t1) < 0.05:
                    time.sleep(0.03)
                t2 = time.time()
                print 'ContExpThread cycle time %.6f seconds' %(t2-self.t1)
                self.t1 = t2

                # TODO: make these memory reference relative
                numBins = self.GUI.PCon.read_memory(2999,1)
                atomReuseArray =  self.GUI.PCon.read_memory(3000,100)
                atomReuseArray = numpy.resize(atomReuseArray,numBins)
                print "mean reuse number %.1f" %numpy.mean(atomReuseArray)
                print atomReuseArray
                #print numpy.std(atomReuseArray)

        self.GUI.PCon.restore_state(self.GUI.PCon.state)
        self.emit(QtCore.SIGNAL("Done_scanning"))



#Need to return to the original configuration after scan. CWC 09052012

    def stop(self):
        self.stopped = 1

    def __del__(self):
        self.stopped = 1
        self.wait()

class PlotThread(QtCore.QThread):
    def __init__(self, GUI):
        super(PlotThread, self).__init__()
        #Pop up two new windows for plot and hist with control bars. See http://eli.thegreenplace.net/files/prog_code/qt_mpl_bars.py.txt CWC 09132012
        self.frame1 = PlotWidget(self)
        self.frame2 = QtGui.QWidget()
        self.GUI = GUI
        self.filename = self.GUI.filename
        self.stopped = 0
        self.t1 = time.time()

        self.fig1 = Figure((5.0, 4.0))
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setParent(self.frame1)
        self.trace1 = self.fig1.add_subplot(111)
        self.trace1.set_title(self.filename)
        self.line1, = self.trace1.plot(self.GUI.plotdata[:,0],self.GUI.plotdata[:,1],'r')
        #self.canvas.mpl_connect('pick_event', self.on_pick)
        self.mpl_toolbar1 = NavigationToolbar(self.canvas1, self.frame1)
        self.canvas1.draw()
        vbox1 = QtGui.QVBoxLayout()
        vbox1.addWidget(self.canvas1)
        vbox1.addWidget(self.mpl_toolbar1)
        self.frame1.setLayout(vbox1)


        self.fig2 = Figure((5.0, 4.0))
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas2.setParent(self.frame2)
        self.trace2 = self.fig2.add_subplot(111)
        self.trace2.set_title(self.filename+'_hist')

        #self.canvas.mpl_connect('pick_event', self.on_pick)
        self.mpl_toolbar2 = NavigationToolbar(self.canvas2, self.frame2)
        self.canvas1.draw()
        vbox2 = QtGui.QVBoxLayout()
        vbox2.addWidget(self.canvas2)
        vbox2.addWidget(self.mpl_toolbar2)
        self.frame2.setLayout(vbox2)
        self.frame2.show()
        self.frame1.show()

    def run(self):
        while (self.stopped == 0 and self.GUI.run_exp ==True):
            time.sleep(0.02)

    def update_plot_save_data(self, scan_index, new_mean, new_data):
##        while (self.stopped == 0 and self.GUI.pause == True):
##            time.sleep(0.02)
        if (self.GUI.scan_entry.currentText()=='Continuous'):
            self.GUI.plotdata[0:self.GUI.plotdatalength-1,1] = self.GUI.plotdata[1:self.GUI.plotdatalength,1]
            self.GUI.plotdata[self.GUI.plotdatalength-1,1] = new_mean
            self.line1.set_ydata(self.GUI.plotdata[:,1])
        else:# (self.GUI.scan_entry.currentText()=='Frequency' ):
            self.GUI.plotdata[scan_index,1] = new_mean
            self.line1.set_ydata(self.GUI.plotdata[:,1])

        #print "%d, %d" %(len(self.GUIplotdata[:,0]),len(self.GUIplotdata[:,1]))
        ymax = numpy.max(self.GUI.plotdata[:,1])
        ymin = numpy.min(self.GUI.plotdata[:,1])
        self.trace1.set_ylim(ymin-0.1*(ymax-ymin)-0.01, ymax+0.1*(ymax-ymin)+0.01)

        self.trace2.clear()
        #self.GUItrace2.hist(self.GUIPCon.data[:,1],arange(0,self.GUIhist_max+1), normed = 1)
        self.update_hist(new_data)
        self.trace2.set_title(self.filename+'_hist')
        self.canvas1.draw()
        self.canvas2.draw()

        if (self.GUI.scan_entry.currentText()=='Continuous'):
            self.text_to_write = str(self.GUI.plotdata[scan_index,1])+'\t'
        else:
            self.text_to_write = str(self.GUI.plotdata[scan_index,0]) + '\t' + str(self.GUI.plotdata[scan_index,1])+'\t'
        for n in range(self.GUI.rep_sb.value()):
            self.text_to_write += str(new_data[n])+'\t'
        self.text_to_write += '\n'
        fd = file(self.filename+'.txt', "a")
        fd.seek(0,2)
        fd.write(self.text_to_write)
        fd.close()
##        if (self.GUI.scan_entry.currentText()=='Continuous'):
##            self.GUI.plotdata[0:self.GUI.plotdatalength-1,1] = self.GUI.plotdata[1:self.GUI.plotdatalength,1]
##            self.GUI.plotdata[self.GUI.plotdatalength-1,1] = new_mean
##            self.line1.set_ydata(self.GUI.plotdata[:,1])
##            self.canvas.draw()

        if (time.time()-self.t1) < 0.05:
            time.sleep(0.03)
        t2 = time.time()
        #print 'PlotThread cycle time %.6f seconds' %(t2-self.t1)
        self.t1 = t2

    def update_hist(self, data):
        #Animating the histogram, see http://matplotlib.sourceforge.net/examples/animation/histogram.html
        n, bins = numpy.histogram(data, arange(0,self.GUI.hist_max+1), normed = True)

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

    def stop(self):
        self.stopped = 1
        self.GUI.stop_scan()
        self.fig1.savefig(self.filename+'.png')
        pp = matplotlib.backends.backend_pdf.PdfPages(self.filename+'.pdf')
        pp.savefig(self.fig1)
        #self.fig1.savefig(pp, format='pdf')
        pp.close()
        print 'Saving figure...'


    def __del__(self):
        self.stopped = 1
        self.GUI.stop_scan()
        self.fig1.savefig(self.filename+'.png')
        pp = matplotlib.backends.backend_pdf.PdfPages(self.filename+'.pdf')
        pp.savefig(self.fig1)
        #self.fig1.savefig(pp, format='pdf')
        pp.close()
        print 'Saving figure...'
        self.wait()

class PlotWidget(QtGui.QWidget):
    def __init__(self, plot_thread):
        super(PlotWidget, self).__init__()
        self.plot_thread = plot_thread

    def closeEvent(self, event):
        self.plot_thread.stop()
        self.plot_thread.frame2.close()
