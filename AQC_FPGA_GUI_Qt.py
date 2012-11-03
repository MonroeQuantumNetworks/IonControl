#!/usr/bin/python2.7
# GaTech PP Gui (a modification of MIT PP Gui with collaboration
#                from Sandia National Labs).
# Craig R. Clark
# March 3-23-2012
# C. Spencer Nichols
# 5-31-2012
#------------------------------------------------------------------------------
# Install Requirments

#WINDOWS

#python2.7  windows  32 bit becuase some of the packages only have 32 bit
# download numpy at http://sourceforge.net/projects/numpy/files/NumPy/1.5.1/
#   (file--numpy-1.5.1-win32-superpack-python2.7.exe)
# download gtk-all-in-one at
# http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/
#   (file--pygtk-all-in-one-2.24.1.win32-py2.7.msi)
# download scipy at
# http://sourceforge.net/projects/scipy/files/scipy/0.9.0/
#   (file--scipy-0.9.0-win32-superpack-python2.7.exe)
# download matplotlib at
# http://sourceforge.net/projects/matplotlib/files/matplotlib/matplotlib-1.1.0/
#   (file--matplotlib-1.1.0.win32-py2.7.exe) 
# need to instal Opal Kelly Software # to have appropriate python API

#Other Requirments --- #Make sure the FPGA id is correct on line 719, 721 and
#722.  This can be changed via the Front Panel Softwarw provided by Opal Kelly

#UBUNTU 10.04
# - ubuntu comes with python 2.6 with the following packages: - os, gobject,
# pango, math, threading, socket, and time - if your version of ubuntu does not
# have these packages, they must be installed - extra packages to install: -
# numpy and scipy - sudo apt-get install python-numpy python-scipy - gtk2.0 -
# sudo apt-get install python-gtk2 - matplotlib - sudo apt-get install
# python-matplotlib

#UBUNTU 12.04
# - ubuntu comes with python 2.7 with the following packages: - os, gobject,
# pango, math, threading, socket, and time - if your version of ubuntu does not
# have these packages, they must be installed - to install the extra packages,
# follow the ubuntu 10.04 instructions

#------------------------------------------------------------------------------
import sys
import os
import platform
sys.path.append('./include')  #for various systems? CWC 0711201

# Import ok driver for correct os
operatingSystem = platform.system()
if (operatingSystem == 'Windows'):
    ok_path = 'Drivers/Windows/'
elif (operatingSystem == 'Linux'):
    ok_path = 'Drivers/Linux/'
elif (operatingSystem == 'Darwin'):
    ok_path = 'Drivers/Darwin/'
sys.path.append(ok_path)
import ok

#import gtk, gobject, pango, math
import numpy
import threading, socket, time
import coltree_Qt, etherplug
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from numpy import arange, sin, pi
#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as \
        FigureCanvas
from matplotlib.axes import Subplot
from matplotlib.axes import Axes

from ppcomp import *
from adBoard import *
from fpgaInit import * #new modules  CWC 07112012

from adDAC import * #new module for DACs CWC 08132012
import ExpConGUI_Qt#09132012

from PyQt4 import *

NETPORT = 11120

#modification from DDScon2 fo xc3s1500 xilinx board on OK XEM 1050-1500
#####################################################################
# class gui
#
# The user interface
#####################################################################
class gui(QtGui.QWidget):
    #################################################################
    # DDS Configuration Data
    #
    # user definable DDS properties - ONLY EDIT THESE VARIABLES
    #################################################################
    #New user definable properties
#    _FPGA_name = 'Opal Kelly XEM3010' #'1725_Test_FPGA'
    _FPGA_name = '1725_Test_FPGA'
    _boards = ['ad9959']#,'ad9958', 'ad9958')# Modified for 1 DDS CWC 07122012
    _dacs = ['ad5390'] # Adding 1 DAC CWC 08132012

    # TODO: Move to fpga front panel class 
    #'fpgafirmware_DAC_busy_bypassed.bit'  #place bitfile in ./FPGA
    _FPGA_bitFile ='fpgafirmware.bit' #'fpgafirmware_DAC_busy_bypassed.bit'
    _checkOutputs = False #True
    
    #################################################################
    # __init__
    #
    # Create all the labels, menus, boxes etc.
    #################################################################
    def __init__(self):
        super(gui, self).__init__()
        #initialize FPGA
        self.xem = ok.FrontPanel()

        #New CWC 07112012
        self.xem = fpgaInit(self._FPGA_name, 0, self._FPGA_bitFile)
        worked = self.xem.ConfigureFPGA('./FPGA/'+self._FPGA_bitFile)
        print worked
        self.boards = []
        self.boardChannelIndex = [];
        for i in range(len(self._boards)):
            print 'Initializing board ' + self._boards[i]
            b = adBoard(self.xem, self._boards[i], i)
            b.initialize(self._checkOutputs)
            self.boards.append(b)
            for j in range(b.channelLimit):
                self.boardChannelIndex.append((i, j))

        #initialize AD DAC Boards New CWC 08132012
        self.dacs = []
        self.dacChannelIndex = [];
        for i in range(len(self._dacs)):
            print 'Initializing DAC ' + self._dacs[i]
            d = adDAC(self.xem, self._dacs[i], i)
            d.initialize(self._checkOutputs)
            self.dacs.append(d)
            for j in range(d.channelLimit):
                self.dacChannelIndex.append((i, j))


        #initialize GUI
        self.lock = threading.Lock()
        self.data = numpy.zeros([100,1], 'Int32')
        self.plotdata = numpy.zeros([100,3], 'Float32')
        self.stateobj = {}
        self.state = {}
        self.ExpConGUIstarted = False
# removed DDS base freq. def. CWC 07112012
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        self.setWindowTitle(self._FPGA_name+"contnroller")


        box = self.make_state_view()
        #stateframe.addWidget(box)
        progdef = self.make_progdef_view()
        (controlbox1,controlbox2,controlbox3) = self.make_control_view()  #,controlbox4,controlbox5

        self.figure = plt.figure() # define the Figure
        self.axis1 = self.figure.add_subplot(111)  # Add Plot to the figure
        self.axis2 = self.axis1.twinx() # Add Second plot to figure which uses other yaxis
        self.plot = FigureCanvas(self.figure)  # a gtk.DrawingArea


        # Add frames
        vbox.addLayout(box)#stateframe)
        vbox.addLayout(controlbox3)
        vbox.addWidget(self.plot)
        vbox.addLayout(controlbox1)
        vbox.addLayout(controlbox2)
        hbox.addLayout(vbox)
        hbox.addLayout(progdef)

        self.setLayout(hbox)

        # Done, show it
        self.show()
        self.ExpCon()

        return

    def __del__(self):
        self.on_quit_activate()
        return

    def closeEvent(self, event):
        self.ExpConGUI.close()
        self.on_quit_activate()
        return
        


    def make_state_view(self):
        hbox = QtGui.QHBoxLayout()
        box = QtGui.QVBoxLayout()

        ddsLabels = [' (MOT test sys)', ' (uWave)', ' (D1)', ' (MOT)']
        dacLabels = [' (Quad Coils, /2?)', ' (Bz)', ' (broken)', ' (MOT)', ' (broken)',
                      ' (Repump)', ' (Bx)', ' (By)', ' (N/A)', 
                      ' (N/A)',' (Dipole)', ' (N/A)', ' (N/A)', ' (N/A)', ' (N/A)', ' (N/A)']
        table_aom = QtGui.QGridLayout()
        table_aom.addWidget(QtGui.QLabel('Frequency'),0,1)
        table_aom.addWidget(QtGui.QLabel('Amplitude'),0,2)
        table_aom.addWidget(QtGui.QLabel('Phase'),0,3)
        s = 0
        for i in range(len(self.boardChannelIndex)):

            table_aom.addWidget(QtGui.QLabel('DDS%i'%i +ddsLabels[i]),i+1,0)
                       
            # Create a freq spinbutton
            spin = indexed_spin_button(self,.2, 3, 0,
                    self.boards[self.boardChannelIndex[i][0]].freqLimit, .1,
                    False, 0, self.freq_changed, i)
            hid = spin.hid
            self.stateobj['DDS%i_FRQ'%i] = (spin, hid)
            table_aom.addLayout(spin.box, i+1, 1)
            # Create an amp spinbutton (DDS1)
            spin = indexed_spin_button(self, .2, 0, 0,
                    self.boards[self.boardChannelIndex[i][0]].ampLimit, 1,
                    False, 0, self.amp_changed, i)
            hid = spin.hid
            self.stateobj['DDS%i_AMP'%i] = (spin, hid)
            table_aom.addLayout(spin.box, i+1, 2)
            # Create a phase spinbutton (DDS1)
            spin = indexed_spin_button(self,.2, 0, 0,
                    self.boards[self.boardChannelIndex[i][0]].phaseLimit, 100,
                    False, 0, self.phase_changed, i)
            hid = spin.hid
            self.stateobj['DDS%i_PHS'%i] = (spin, hid)
            table_aom.addLayout(spin.box, i+1, 3)
            s = i + 2
        table_aom.addWidget(QtGui.QLabel('SHUTR'),s,0)
        table_aom.addWidget(QtGui.QLabel('THRES0'),s+1,0)
        table_aom.addWidget(QtGui.QLabel('THRES1'),s+1,2)

        self.spinShutr, hid = self.make_spin_button(1, 0, 0, 2**12-1, 1, False, 0,
                self.shutter_changed, 0)
        self.stateobj['SHUTR'] = (self.spinShutr, hid)
        self.spinShutr.setDisabled(True)
        table_aom.addWidget(self.spinShutr, s, 1)

        spin, hid = self.make_spin_button(.2, 1, 0, 100, 1, False, 3.5, None,
                0)
        self.stateobj['THRES0'] = (spin, hid)
        table_aom.addWidget(spin, s+1, 1)

        spin, hid = self.make_spin_button(.2, 1, 0, 100, 1, False, 50, None, 0)
        self.stateobj['THRES1'] = (spin, hid)
        table_aom.addWidget(spin, s+1, 3)

        
        table_pp = QtGui.QGridLayout()
        table_pp.addWidget(QtGui.QLabel('CMD '),0,0)
        table_pp.addWidget(QtGui.QLabel('DATA'),0,2)
        table_pp.addWidget(QtGui.QLabel('PC  '),1,0)
        table_pp.addWidget(QtGui.QLabel('W   '),1,2)

        # Create a threshold spinbutton
        self.stateobj['CMD'] = QtGui.QLabel('-----')
        table_pp.addWidget(self.stateobj['CMD'], 0, 1)
        self.stateobj['DATA'] = QtGui.QLabel('-----')
        table_pp.addWidget(self.stateobj['DATA'], 0, 3)
        self.stateobj['PC'] = QtGui.QLabel('-----')
        table_pp.addWidget(self.stateobj['PC'], 1, 1)
        self.stateobj['W'] = QtGui.QLabel('-----')
        table_pp.addWidget(self.stateobj['W'], 1, 3)

        table_dac = QtGui.QGridLayout()
        for i in range(len(self.dacChannelIndex)):
            table_dac.addWidget(QtGui.QLabel('DAC%i'%i + dacLabels[i]),int(i/4),(2*i)%8)
            spin = indexed_spin_button(self, .2, 3, 0,
                    self.dacs[self.dacChannelIndex[0][0]].VoutLimit*2.5/2**13,
                    .1, False, 0, self.Vout_changed, i) #4.99969482422
            hid = spin.hid
            self.stateobj['DAC%i_Vout'%i] = (spin, hid)
            table_dac.addLayout(spin.box, int(i/4), (2*i)%8+1)

        box.addLayout(table_aom)
        box.addLayout(table_dac)
        box.addLayout(table_pp)
        
        #layout for shutter control
        shutrLayout = QtGui.QGridLayout()  
        self.shutrIndexLabels = ['SHUTR_MOT_', 'SHUTR_Repump_', 'SHUTR_uWave_', 'SHUTR_D1_', 'SHUTR_Dipole_', 'SHUTR_MOT_Servo_', 'SHUTR_MOTradial_', 'SHUTR_459_', 'SHUTR_1038_', 'SHUTR_Raman_']

        self.shutrLabels = ['MOT (TTL0)','Repump (TTL1)','uWave (TTL7)', 'D1 (TTL5)', 'Dipole (TTL3)', 'MOT Servo (TTL4)', 'MOT Radial (TTL2)', '459 (TTL6)', '1038 (TTL8)','Raman (TTL9)']
        self.SHUTR_CHAN = {'SHUTR_MOT_': 0, 'SHUTR_Repump_': 1,'SHUTR_uWave_':
                7, 'SHUTR_D1_': 5, 'SHUTR_Dipole_': 3, 'SHUTR_MOT_Servo_':
                4, 'SHUTR_MOTradial_': 2, 'SHUTR_459_': 6, 'SHUTR_1038_': 8, 'SHUTR_Raman_':9} #Define the TTL channels
        self.shutrButton = []
        #for i in range(len(self.shutrLabels)):
            #shutrLayout.addWidget(QtGui.QLabel(self.shutrLabels[i]),i,0)
        
        for i in range(len(self.shutrLabels)):
            aShutrButton = QtGui.QPushButton(self.shutrLabels[i],self)
            aShutrButton.setCheckable(True)
            QtCore.QObject.connect(aShutrButton, QtCore.SIGNAL("clicked()"),self.shutrButtonToggled)
            #aShutrButton.connect(self.shutrButtonToggled)
            

            self.shutrButton.append(aShutrButton)
            shutrLayout.addWidget(aShutrButton,i,1)
            
        
        
        
        #shutrLayout.addWidget(shutrLabels[0],0,1)
        hbox.addLayout(shutrLayout)
        hbox.addLayout(box)

        state = coltree_Qt.read_state_from_config('State')
        self.restore_state(state)
        return hbox
        


    def shutrButtonToggled(self):
        SHUTR_value = 0
        SW = []

        for i in range(len(self.shutrIndexLabels)):
            SW.append(0)
            if self.shutrButton[i].isChecked(): SW[i] = 1

        for i in range(len(self.shutrIndexLabels)):
            SHUTR_value += SW[i]<<self.SHUTR_CHAN[self.shutrIndexLabels[i]]
        
        self.spinShutr.setValue(SHUTR_value)

            
    def make_progdef_view(self):
        box = QtGui.QVBoxLayout()
        # coltree.typical_ncol_tree([(gobject.TYPE_STRING, 'Parameter Name',
        #   1),(gobject.TYPE_DOUBLE, 'Parameter Value', 1)])
        self.params = coltree_Qt.typical_table_Qt(self)
        defs = coltree_Qt.read_defs_from_config('Params:tree')

        for key in sorted(defs.iterkeys()):#defs:
            self.params.add_row(key, defs[key])
        for i in range(len(defs), 200):
            self.params.add_row('<PARAM%d>'%(i), 0)

        box.addWidget(self.params.table)
        return box

    def make_control_view(self):
        box1 = QtGui.QHBoxLayout()
        box2 = QtGui.QHBoxLayout()
        box3 = QtGui.QHBoxLayout()
        box4 = QtGui.QHBoxLayout()
        box5 = QtGui.QHBoxLayout()
        # buttons to run pulse sequencer

        button_plot_reset = QtGui.QPushButton("Reset Plot", self)
        box1.addWidget(button_plot_reset)

        button_save = QtGui.QPushButton("Save",self)
        box1.addWidget(button_save)

        button_load = QtGui.QPushButton("Load PP",self)
        box2.addWidget(button_load)

        button_run = QtGui.QPushButton("Run PP", self)
        box2.addWidget(button_run)

        button_stop = QtGui.QPushButton("Stop PP", self)
        box2.addWidget(button_stop)

        button_read = QtGui.QPushButton("Readout PP", self)
        box2.addWidget(button_read)

        button_reset = QtGui.QPushButton("Reset PP", self)
        box2.addWidget(button_reset)

        button_lauch_panel = QtGui.QPushButton("Exp. control", self)
        box3.addWidget(button_lauch_panel)

        Filename_label=QtGui.QLabel("Filename")
        box3.addWidget(Filename_label)

        self.Filename_entry=QtGui.QLineEdit()
        self.Filename_entry.setText("Load_cool_exp_check_by_parts_table_GUI.pp")
        box3.addWidget(self.Filename_entry)

        button_quit= QtGui.QPushButton("Quit", self)
        box3.addWidget(button_quit)

        button_run.clicked.connect(self.pp_run)
        button_stop.clicked.connect(self.pp_stop)
        button_load.clicked.connect(self.pp_load)
        button_save.clicked.connect(self.pp_save)
        button_read.clicked.connect(self.pp_readout)
        button_reset.clicked.connect(self.pp_reset)
        button_plot_reset.clicked.connect(self.pp_plot_reset)
        button_lauch_panel.clicked.connect(self.ExpCon)
        button_quit.clicked.connect(self.on_quit_activate)
        return box1,box2,box3#,box4,box5

    def restore_state(self,state):
        for key in sorted(state.iterkeys()):
            self.SetOutput(key,state[key])
            if key == 'SHUTR':
                for i in range(len(self.SHUTR_CHAN )):
                    if (int(float(self.stateobj['SHUTR'][0].value())) & 1<<self.SHUTR_CHAN[self.shutrIndexLabels[i]]):
                        self.shutrButton[i].setChecked(True) 
        return True

    def ExpCon(self):
        self.ExpConGUI = ExpConGUI_Qt.ExpConGUI_Qt(self, self.Filename_entry.text())#09132012
        self.ExpConGUIstarted = True
        return
    ################################################################
    # on_quit_activate
    #
    # Run when window is closed
    ################################################################
    def on_quit_activate(self):#, widget, event, data = None):
        self.params.save_params("Params")
        self.update_state()
        coltree_Qt.save_state("State", self.state)
        #self.plug.close()
        #gtk.main_quit()
        self.close()
        return True

    def make_spin_button(self, climb_rate, digits, range_low, range_high, increments, wrap, value, callback, key):
        sb = QtGui.QDoubleSpinBox()
        sb.setRange(range_low, range_high)
        sb.setDecimals(digits)
        sb.setSingleStep(increments)
        sb.setKeyboardTracking(False)
        #sb.set_wrap(wrap)
        if (value == None):
            value = mcxem.get_state(key)
        sb.setValue(value)
        if callback:
            hid = sb.valueChanged.connect(callback)
        else:
            hid = None
        return sb, hid

    def service_netcomm(self, f, arg):
        if (self.pp_is_running() and (f != self.pp_run)):
            return "Wait\n"

        gtk.gdk.threads_enter()
        try:
            rv = f(*arg)
        finally:
            gtk.gdk.threads_leave()
        return rv

#    def update_state(self):
#        self.lock.acquire()
#        try:
#			#Commented CWC 04032012
#            data = '\x00'*32
#            self.xem.ReadFromPipeOut(0xA1, data)
#
#            if ((data[:2] != '\xED\xFE') or (data[-2:] != '\xED\x0F')):
#                print "Bad data string: ", map(ord, data)
#                return True
#
#            data = map(ord, data[2:-2])
#
#            #Decode
#            active =  bool(data[1] & 0x80)
#            self.state['pp_PC'] = ((data[1] & 0xF)<<8) + data[0]
#            self.state['pp_W'] = (data[3]<<8) + data[2]
#            self.state['pp_DATA'] = (data[6]<<16) + (data[5]<<8) + data[4]
#            self.state['pp_CMD'] = data[7]
#            for i in range(len(self.boardChannelIndex)):
#                self.state['DDS%i_FRQ'%i] = self.boards(i).freqLimit*((data[11]<<24) + (data[10]<<16) + (data[9]<<8) + data[8])
                #self.state['DDS1_FRQ'] = self.dds_base_freq*((data[15]<<24) + (data[14]<<16) + (data[13]<<8) + data[12])
                #self.state['DDS2_FRQ'] = self.dds_base_freq*((data[19]<<24) + (data[18]<<16) + (data[17]<<8) + data[16])
#            self.state['DDS0_AMP'] = data[20]&0x3F
#            self.state['DDS1_AMP'] = ((data[21]&0xF)<<2) + (data[20]>>6)
#            self.state['DDS2_AMP'] = ((data[22]&0x3)<<4) + (data[21]>>4)
#            self.state['DDS0_PHS'] = (data[23]<<6) + (data[22]>>2)
#            self.state['DDS1_PHS'] = ((data[25]&0x3F)<<8) + (data[24])
#            self.state['DDS2_PHS'] = ((data[27]&0xF)<<10) + (data[26]<<6) + (data[25]>>6)
#            self.state['SHUTR'] = data[27]>>4
#
#            # Display
#            self.stateobj['PC'].set_label('%d'%self.state['pp_PC'])
#            self.stateobj['CMD'].set_label('%d'%self.state['pp_CMD'])
#            self.stateobj['DATA'].set_label('%d'%self.state['pp_DATA'])
#            self.stateobj['W'].set_label('%d'%self.state['pp_W'])
#
#            for key in self.state:
#                if not self.stateobj.has_key(key):
#                    continue
#
#                if ((self.state.has_key('pp_active') and self.state['pp_active']) or active):
#                    self.stateobj[key][0].handler_block(self.stateobj[key][1])
#                    self.stateobj[key][0].set_sensitive(False)
#                    self.stateobj[key][0].set_value(self.state[key])
#                    self.stateobj[key][0].handler_unblock(self.stateobj[key][1])
#                else:
#                    self.stateobj[key][0].set_sensitive(True)
#
#                    if (abs(self.stateobj[key][0].get_value() - self.state[key]) > 1e-6): #modified? 04042012
#                        print "Inconsistent state of %s, actual value:"%(key), self.state[key], self.stateobj[key][0].get_value()
#
#            self.state['pp_active'] =  bool(data[1] & 0x80)
#        finally:
#            self.lock.release()
#
#        return True

    def update_state(self): #Only updating the state shown on the panel to self.state CWC 09012012
        for key in self.stateobj:
                if (key[:3] == 'DDS' or key[:3] == 'DAC' or key == 'SHUTR'):
                    self.state[key]=str(self.stateobj[key][0].value())

    ################################################################
    # Static DDS and DAC commands

    def freq_changed(self, data = None):#, widget):
        widget = self.sender()
        freq = widget.value()	# frequency in MHz
        #data = widget.index
        board = self.boardChannelIndex[int(data)][0]
        chan = self.boardChannelIndex[int(data)][1]
        #print 'board ' + str(board) + ', channel ' + str(chan)
        self.boards[board].setFrequency(freq, chan, self._checkOutputs)
        return True

    def amp_changed(self,data = None):#, widget, data= None):
        widget = self.sender()
        amp = int(max(0, round(widget.value())))
        board = self.boardChannelIndex[int(data)][0]
        chan = self.boardChannelIndex[int(data)][1]
        #print 'board ' + str(board) + ', channel ' + str(chan)
        self.boards[board].setAmplitude(amp, chan, self._checkOutputs)
        return True

    def phase_changed(self, data = None):#, widget, data= None):
        widget = self.sender()
        phase = int(max(0, round(widget.value())))
        board = self.boardChannelIndex[int(data)][0]
        chan = self.boardChannelIndex[int(data)][1]
        #print 'board ' + str(board) + ', channel ' + str(chan)
        self.boards[board].setPhase(phase, chan, self._checkOutputs)
        return True

    def shutter_changed(self):#, widget, data=None):
        widget = self.sender()
        shutter = int(max(0, widget.value()))
        self.xem.SetWireInValue(0x00, shutter<<12, 0xF000)    # address, value, mask
        self.xem.SetWireInValue(0x04, shutter>>4, 0x00FF)
        self.xem.UpdateWireIns()
        #self.xem.ActivateTriggerIn(0x40, 1) #Added by CWC 07132012
        #print "Setting shutter to %d"%(shutter)

        return True

    def Vout_changed(self, data = None):#, widget, data = None):
        widget = self.sender()
        Vout = widget.value()	# frequency in MHz
        dac = self.dacChannelIndex[data][0]
        chan = self.dacChannelIndex[data][1]
        #print 'dac ' + str(dac) + ', channel ' + str(chan)
        #VoutData = int(Vout/2.5*2**13-1)
        self.dacs[dac].setVout(Vout, int(chan), self._checkOutputs)
        return True

    def SetOutput(self, name, data):
        #print "SetOutput: Setting %s value to %s" %(name, data)
        self.stateobj[name][0].setValue(float(data))
        return True
    ################################################################
    # pulse sequencer commands

    def pp_run(self):#, widget = None, data = None):
        self.xem.ActivateTriggerIn(0x40, 3)
        self.pp_upload()
        self.xem.ActivateTriggerIn(0x40, 2)

        #time.sleep(0.2) commented for speed CWC 08312012

        if (self._checkOutputs):
            print 'shifting out'
            self.xem.SetWireInValue(0x00, (1<<2))
            self.xem.UpdateWireIns()
            self.xem.UpdateWireOuts()
#            print hex(self.xem.GetWireOutValue(0x20))
#            print hex(self.xem.GetWireOutValue(0x21))
#            print hex(self.xem.GetWireOutValue(0x22))
#            print hex(self.xem.GetWireOutValue(0x23))
            #print 'test_o'
            #print hex(self.xem.GetWireOutValue(0x25))
        return True

    def pp_run_2(self):#, widget = None, data = None):
        #same as pp_run, but does not re-upload the pp file
        self.xem.ActivateTriggerIn(0x40, 2)
        self.xem.UpdateWireOuts()
        return True

    def py_run(self):#, widget = None, data = None):
        #runs a python script.
        execfile(self.pyfile)
        return True

    def pp_stop(self):#, widget, data= None):
        self.xem.ActivateTriggerIn(0x40, 3)
        self.restore_state(self.state)
        return True

    def pp_Host_stop(self):#, widget = None, data = None):
        self.xem.ActivateTriggerIn(0x40, 3)
        return True

    def pp_save(self):#, widget, data= None):
        data = self.data

        file = QtGui.QFileDialog.getOpenFileName(self, 'Save data to:')

        try:
            fd = open(file, 'w')
            for i in range(len(data)):
                fd.write('%d %d %d\n'%(data[i, 0], data[i, 1], data[i,2]))
            fd.close
        except Exception, E:
            print E

        return True

    def pp_load(self):#, widget, data = None):
        file = QtGui.QFileDialog.getOpenFileName(self, 'Choose file:','.\prog')

        print file

        self.pp_setprog(file)

        print file
        self.pp_upload()
        return True

    def py_load(self):#, widget, data = None):

        file = QtGui.QFileDialog.getOpenFileName(self, 'Choose a .py file:','.\scripts')

        self.pyfile = file
        print self.pyfile


    def pp_setprog(self, file):
        self.codefile = file

        return True

    def pp_upload(self):
        t3 = time.time()
        self.params.update_defs()
        parameters = self.params.defs
        if self.ExpConGUIstarted == True:
            self.ExpConGUI.ppfile = self.codefile
            self.ExpConGUI.update_pp_filename()


##        for key in self.params.defs:
##            parameters.update({key : self.params.get_data(key, 1)})

        code = pp2bytecode(self.codefile, self.boardChannelIndex, self.boards, parameters)

        databuf = ''
        for op, arg in code:
            memword = '%c%c'%((arg&0xFF), (arg>>8)&0xFF) + '%c%c'%((arg>>16)&0xFF, op + (arg>>24))
            #print '%x, %x, %x, %x' %(ord(memword[0]), ord(memword[1]), ord(memword[2]), ord(memword[3]))
            databuf = databuf + memword
        t4 = time.time()
        #print "pp compile time %fs"%(t4 - t3)
        t1 = time.time()
        self.xem.SetWireInValue(0x00, 0, 0x0FFF)	# start addr at zero
        self.xem.UpdateWireIns()
        self.xem.ActivateTriggerIn(0x41, 1)
        self.xem.WriteToPipeIn(0x80, databuf)
        t2 = time.time()
        #print "Upload successful in time %fs"%(t2 - t1)
        return True

    def parameter_read(self, name):
        return "RESULT: %g\n"%(float(self.params.get_data(name, 1)))

    def parameter_set(self, name, value):
        self.params.set_data(name, 1, float(value))
        return True

    def pp_is_running(self):
        self.lock.acquire()
        try:
			#Commented CWC 04032012
            data = '\x00'*32
            self.xem.ReadFromPipeOut(0xA1, data)

            if ((data[:2] != '\xED\xFE') or (data[-2:] != '\xED\x0F')):
                print "Bad data string: ", map(ord, data)
                return True

            data = map(ord, data[2:-2])

            #Decode
            active =  bool(data[1] & 0x80)
        finally:
            self.lock.release()

        return active

    def pp_readout(self, widget = None, data = None):
        self.update_count()

        self.plotdata[:,0:2] = self.data[:,0:2]
        self.plotdata[:,2] = numpy.log(numpy.abs(self.data[:, 2]) + 1)
        self.axis1.clear()
        self.axis2.clear()
        self.axis1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
        self.axis1.set_ylabel('Counts', color='r')
        self.axis1.set_xlabel('Bins')
        self.axis2.plot(self.plotdata[:,0],self.plotdata[:,2],'b') #should add readout to the plot
        self.axis2.set_ylabel('Hist', color='b')
        self.plot.draw()


        return True

    def pp_reset(self):#, widget = None, data = None):
        self.xem.ActivateTriggerIn(0x40,0)
        self.xem.ActivateTriggerIn(0x41,0)
        print "pp_reset is not working right now... CWC 08302012"
##        for key in self.stateobj:
##            if ((key[:3] != 'DDS') and (key != 'SHUTR')): continue
##            #self.stateobj[key][0].handler_block(self.stateobj[key][1])
##            self.stateobj[key][0].setValue(0.0)
##            #self.stateobj[key][0].handler_unblock(self.stateobj[key][1])

        return True

    def pp_plot_reset(self, widget = None, data = None):
        self.axis1.clear()  #Should Clear the Plot
        self.axis2.clear()
        self.plot.draw()

        return True


    def get_datastart(self):
        data=self.parameter_read('datastart')
        out=data.split()
        datastart=int(out[1])
        #print datastart
        return datastart

    def get_datapoints(self):
        datapoints=4000-self.get_datastart()+1 #Changed CWC 09122012
        return datapoints

    ###############################################################
    # update_count
    #
    # Displays latest count
    ###############################################################
    def update_count(self):
        t1 = time.time()
        readout_OK = False
        while (self.pp_is_running()): #wait until pp is not running to proceed CWC 08032012
            #time.sleep(0.001)
            continue
        #print self.pp_is_running()
        data_start=self.get_datastart()
        datapoints=4000-data_start+1 #changed CWC 09122012
        self.data=numpy.zeros([datapoints,2],'Int32')
        count = numpy.zeros([datapoints],'Int32')
        readout_OK = True
        #self.plotdata =numpy.zeros([datapoints,2], 'Float32')

        self.xem.SetWireInValue(0x00, data_start, 0x0FFF)	# start addr at 3900
        self.xem.UpdateWireIns()
        self.xem.ActivateTriggerIn(0x41, 1)

        data = '\x00'*4*datapoints
        self.xem.ReadFromPipeOut(0xA0, data)
        data = map(ord, data)

        for addr in range(datapoints):
             temp = (data[4*addr + 3]<<24) + (data[4*addr + 2]<<16) + (data[4*addr + 1]<<8) + data[4*addr]

             if (temp<1000):
                count[addr] = temp
             else:
                readout_OK = False
            #count=numpy.random.normal(25,5,1);
            #count=int(numpy.rint(count))
        if (readout_OK):
            self.data[:,1] = count
            for addr in range(datapoints):
                self.data[addr][0] = addr
##            if (len(self.hist)!=datapoints):
##              self.hist=numpy.zeros(datapoints,'Int32')
##            if (len(self.hist)!=datapoints):
##                self.hist=numpy.zeros(datapoints,'Int32')
##            histogram=numpy.histogram(self.data[:,1],datapoints,(0,datapoints))
            #print histogram[0]
##            self.hist=self.hist+histogram[0]
            #if (len(self.hist)!=hist_max+1):
            #    self.hist=numpy.zeros(hist_max+1,'Int32')
            #histogram=numpy.histogram(self.data[:,1],hist_max+1,(0,hist_max),True)
            #print histogram[0]
            #self.hist=self.hist+histogram[0]
            #self.hist=histogram[0]
            t2 = time.time()
            #print "Memory read in %.6f seconds" % (t2-t1)

        else:
            t2 = time.time()
            print "Memory read in %.6f seconds" % (t2-t1)
            print "Data readout error"

        return readout_OK
##        t1 = time.time()
##        self.xem.SetWireInValue(0x00, 3900, 0x0FFF)	# start addr at 3900
##        self.xem.UpdateWireIns()
##        self.xem.ActivateTriggerIn(0x41, 1)
##
##        data = '\x00'*400
##        self.xem.ReadFromPipeOut(0xA0, data)
##        data = map(ord, data)
##
##        for addr in range(100):
##            count = (data[4*addr + 3]<<24) + (data[4*addr + 2]<<16) + (data[4*addr + 1]<<8) + data[4*addr]
##            #count=numpy.random.normal(25,5,1);
##            #count=int(numpy.rint(count))
##            self.data[addr][0] = addr
##            self.data[addr][1] = count
##
##
##	    # Histogram
##            if (count < 100):
##                self.data[count][2] = self.data[count][2] + 1
##
##
##        t2 = time.time()
##        print "Memory read in %.6f seconds" % (t2-t1)
##        #print "Memory contents: ", map(hex, map(int, self.data[:,1]))
##        return

    ###############################################################
    # read_memory
    #
    # Reads specific memory slots
    ###############################################################
    def read_memory(self, index_i, n_read):
        t1 = time.time()
##        while (self.pp_is_running()): #wait until pp is not running to proceed CWC 08032012
##            continue

        value = numpy.zeros(n_read)
        readout_OK = True
        #self.plotdata =numpy.zeros([datapoints,2], 'Float32')

        self.xem.SetWireInValue(0x00, index_i, 0x0FFF)	# start addr at 3900
        self.xem.UpdateWireIns()
        self.xem.ActivateTriggerIn(0x41, 1)

        data = '\x00'*4*n_read
        self.xem.ReadFromPipeOut(0xA0, data)
        data = map(ord, data)

        for addr in range(n_read):
             temp = (data[4*addr + 3]<<24) + (data[4*addr + 2]<<16) + (data[4*addr + 1]<<8) + data[4*addr]
             if (temp<10000):
                value[addr] = temp
             else:
                readout_OK = False
            #count=numpy.random.normal(25,5,1);
            #count=int(numpy.rint(count))
        if (readout_OK):
            t2 = time.time()
            #print "Memory read in %.6f seconds" % (t2-t1)

        else:
            t2 = time.time()
            #print "Memory read in %.6f seconds" % (t2-t1)
            print "Data readout error"

        return value



    def net_countabove(self):
        self.pp_readout()
        count = 0
        threshold0 = self.stateobj['THRES0'][0].get_value()
        threshold1 = self.stateobj['THRES1'][0].get_value()
        for addr in range(100):
            if (self.data[addr][1] > threshold1):
                count = count + 2
            elif (self.data[addr][1] > threshold0):
                count = count + 1

        return "RESULT: %d\n"%(count)

    def net_lastavg(self):
        count = 0
        tot = 0
        threshold0 = self.stateobj['THRES0'][0].get_value()
        threshold1 = self.stateobj['THRES1'][0].get_value()
        for addr in range(100):
            if (self.data[addr][1] > threshold1):
                count = count + 2
                tot = tot + self.data[addr][1]
            elif (self.data[addr][1] >= threshold0):  #changed this line to >= from >  For heating rate exp.  (Craig Oct 24 2008)
                count = count + 1
                tot = tot + self.data[addr][1]

	if (count < 5):
       	    return "RESULT: 0\n"
        else:
            return "RESULT: %f\n"%(1.0*tot/count)




    def net_memory(self):
        self.pp_readout()

        memory = 'RESULT:'
        for addr in range(100):
	    memory = memory + " %i"%(self.data[addr][1])

        return memory + "\n"

    def user_stop(self):
        return self.pp_Host_stop()

class indexed_spin_button(QtGui.QWidget):
    def __init__(self,gui,climb_rate, digits, range_low, range_high,
            increments, wrap, value, callback, key):
        super(indexed_spin_button, self).__init__()
        self.box = QtGui.QVBoxLayout()
        self.sb = QtGui.QDoubleSpinBox()
        self.box.addWidget(self.sb)
        self.sb.setRange(range_low, range_high)
        self.sb.setDecimals(digits)
        self.sb.setSingleStep(increments)
        self.index = key
        self.sb.setKeyboardTracking(False)
        #sb.set_wrap(wrap)
##        if (value == None):
##            value = mcxem.get_state(key)
        self.sb.setValue(value)

        if callback:
            self.hid = self.sb.valueChanged.connect(self.valchanged)
            QtCore.QObject.connect(self,QtCore.SIGNAL("changed"),callback)
        else:
            self.hid = None
        return

    def valchanged(self):
        self.emit(QtCore.SIGNAL("changed"),self.index)

    def value(self):
        return self.sb.value()

    def setValue(self,val):
        self.sb.setValue(float(val))
        self.valchanged()
        return
        
        
class LabeledPushButton(QtGui.QWidget):    
#------------------------------------------------------------------------------
#class for making shutter contol buttons
#------------------------------------------------------------------------------    
    #def __init__(self, vlabel, hlabel, callback):
    def __init__(self):

        super(LabeledPushButton, self).__init__()
        self.box = QtGui.QVBoxLayout()
        self.tb = QtGui.QPushButton()
        self.tb.setCheckable(True)
        self.box.addWidget(self.tb)
        #self.vlabel = vlabel
        #self.hlabel = hlabel
        #self.tb.toggled.connect(self.tb_toggled) #This signal is never invoked! CWC09252012
        #QtCore.QObject.connect(self,QtCore.SIGNAL("tb_toggled"),callback)

    #def tb_toggled(self):
        #print '%s toggled.' %(self.vlabel+self.hlabel)
        #self.emit(QtCore.SIGNAL("tb_toggled"),self.hlabel)
        
        
def main():
    app = QtGui.QApplication(sys.argv)
    ex = gui()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
