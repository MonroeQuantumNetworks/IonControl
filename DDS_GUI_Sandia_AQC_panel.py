# Modification of GaTech PP Gui which is a modification of MIT PP Gui.
# Craig R. Clark
# March 3-23-2012
#------------------------------------------------------------------------------------------------------------------------------------------
# Install Requirments

#python2.7  windows  32 bit becuase some of the packages only have 32 bit
# download numpy at http://sourceforge.net/projects/numpy/files/NumPy/1.5.1/ (file--numpy-1.5.1-win32-superpack-python2.7.exe)
# download gtk-all-in-one at http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/ (file--pygtk-all-in-one-2.24.1.win32-py2.7.msi)
# download scipy at http://sourceforge.net/projects/scipy/files/scipy/0.9.0/ (file--scipy-0.9.0-win32-superpack-python2.7.exe)
# download matplotlib at http://sourceforge.net/projects/matplotlib/files/matplotlib/matplotlib-1.1.0/ (file--matplotlib-1.1.0.win32-py2.7.exe)
# need to instal Opal Kelly Software to have appropriate python API

#Other Requirments ---
#Make sure the FPGA id is correct on line 719, 721 and 722.  This can be changed via the Front Panel Softwarw provided by Opal Kelly

#--------------------------------------------------------------------------------------------------------------------------------------------

import ok, os
import gtk, gobject, pango, math
import numpy
import threading, socket, time
import coltree, etherplug
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from numpy import arange, sin, pi
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.axes import Subplot
from matplotlib.axes import Axes

from ppcomp import *

NETPORT = 11120
datastart = 3900
datapoints = 4000-datastart
hist_max = 30

#modification from DDScon2 fo xc3s1500 xilinx board on OK XEM 1050-1500
#####################################################################
# class gui
#
# The user interface
#####################################################################
class gui:
    #################################################################THOR`
    # __init__
    #
    # Create all the labels, menus, boxes etc.
    #################################################################
    def __init__(self):
        self.lock = threading.Lock()
        self.data = numpy.array([], 'Int32')
        #self.plotdata=numpy.array([],'Float32')
        self.hist=[]
        self.stateobj = {}
        self.state = {}
        self.dds_base_freq = 240    #Changed from 240 to 120 CWC 04092012 #480 MHz sysclk

        vbox = gtk.VBox(False, 0)
        hbox = gtk.HBox(False, 0)
        window = gtk.Window()
        window.set_title("DDS Controller")

        stateframe = gtk.Frame("State")

        box = self.make_state_view()
        stateframe.add(box)
        progdef = self.make_progdef_view()
        controlbox = self.make_control_view()

        self.figure = plt.figure() # define the Figure
        self.axis1 = self.figure.add_subplot(111)  # Add Plot to the figure
        self.axis2 = self.axis1.twinx() # Add Second plot to figure which uses other yaxis
        self.plot = FigureCanvas(self.figure)  # a gtk.DrawingArea


        # Add frames
        vbox.pack_start(stateframe, False, False, 1)
        vbox.pack_start(self.plot, True, True, 1)
        vbox.pack_start(controlbox, False, False, 1)
        hbox.pack_start(vbox, True, True, 1)
        hbox.pack_start(progdef, False, False, 1)

        window.add(hbox)

        # connect quit signals
        window.connect("delete_event", self.on_quit_activate, None)
        window.connect("destroy", self.on_quit_activate, None)

        # add an idle callback
        gobject.timeout_add(50, self.update_state) #Changed 50 to 2000 CWC 04042012
        # Done, show it
        window.show_all()


        # start network
        self.plug = etherplug.etherplug(self.service_netcomm, NETPORT,'127.0.0.1')#'127.0.0.1'
        self.plug.register_hook('FREQ0', self.stateobj['DDS0_FRQ'][0].set_value)
        self.plug.register_hook('FREQ1', self.stateobj['DDS1_FRQ'][0].set_value)
        self.plug.register_hook('FREQ2', self.stateobj['DDS2_FRQ'][0].set_value)
        self.plug.register_hook('FREQ3', self.stateobj['DDS3_FRQ'][0].set_value)
        self.plug.register_hook('FREQ4', self.stateobj['DDS4_FRQ'][0].set_value)
        self.plug.register_hook('FREQ5', self.stateobj['DDS5_FRQ'][0].set_value)
        self.plug.register_hook('AMP0', self.stateobj['DDS0_AMP'][0].set_value)
        self.plug.register_hook('AMP1', self.stateobj['DDS1_AMP'][0].set_value)
        self.plug.register_hook('AMP2', self.stateobj['DDS2_AMP'][0].set_value)
        self.plug.register_hook('AMP3', self.stateobj['DDS3_AMP'][0].set_value)
        self.plug.register_hook('AMP4', self.stateobj['DDS4_AMP'][0].set_value)
        self.plug.register_hook('AMP5', self.stateobj['DDS5_AMP'][0].set_value)
        self.plug.register_hook('SHUTR', self.stateobj['SHUTR'][0].set_value)
        self.plug.register_hook('SETPROG', self.pp_setprog)
        self.plug.register_hook('PARAMETER', self.parameter_set)
        self.plug.register_hook('RUNIT', self.pp_run_2) # Will run with preloaded parameters
        self.plug.register_hook('RUNIT?', self.pp_run)  #will upload parameter before running
        self.plug.register_hook('NBRIGHT?', self.net_countabove)
        self.plug.register_hook('LASTAVG?', self.net_lastavg)
        self.plug.register_hook('MEMORY?', self.net_memory)
        self.plug.register_hook('PARAMETER?', self.parameter_read)
        self.plug.register_hook('STOP', self.pp_Host_stop)

        return

    def make_state_view(self):
        box = gtk.VBox(False, 0)

        table_aom = gtk.Table(rows=9, columns=4, homogeneous=True)
        table_aom.attach(gtk.Label('Frequency'),1,2,0,1, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        table_aom.attach(gtk.Label('Amplitude'),2,3,0,1, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('Phase'),3,4,0,1,gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('DDS0'),0,1,1,2, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('DDS1'),0,1,2,3, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('DDS2'),0,1,3,4, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('DDS3'),0,1,4,5, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('DDS4'),0,1,5,6, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('DDS5'),0,1,6,7, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('SHUTR'),0,1,7,8, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('THRES0'),0,1,8,9, gtk.FILL, gtk.FILL)
        table_aom.attach(gtk.Label('THRES1'),2,3,8,9, gtk.FILL, gtk.FILL)

        for i in range(6):
            # Create a freq spinbutton
            spin, hid = self.make_spin_button(.2, 6, 0, 250, .1, False, 0, self.freq_changed, i)
            self.stateobj['DDS%i_FRQ'%i] = (spin, hid)
            table_aom.attach(spin, 1, 2, i+1, i+2, gtk.FILL, gtk.FILL)
            # Create an amp spinbutton (DDS1)
            spin, hid = self.make_spin_button(.2, 0, 0, 2**10 - 1, 1, False, 0, self.amp_changed, i)
            self.stateobj['DDS%i_AMP'%i] = (spin, hid)
            table_aom.attach(spin, 2, 3, i+1, i+2, gtk.FILL, gtk.FILL)
            # Create a phase spinbutton (DDS1)
            spin, hid = self.make_spin_button(.2, 0, 0, 2**14 - 1, 100, False, 0, self.phase_changed, i)
            self.stateobj['DDS%i_PHS'%i] = (spin, hid)
            table_aom.attach(spin, 3, 4, i+1, i+2, gtk.FILL, gtk.FILL)

        spin, hid = self.make_spin_button(.2, 0, 0, 15, 1, False, 0, self.shutter_changed, 0)
        self.stateobj['SHUTR'] = (spin, hid)
        table_aom.attach(spin, 1, 2, 7, 8, gtk.FILL, gtk.FILL)

        spin, hid = self.make_spin_button(.2, 1, 0, 100, 1, False, 3.5, None, 0)
        self.stateobj['THRES0'] = (spin, hid)
        table_aom.attach(spin, 1, 2, 8, 9, gtk.FILL, gtk.FILL)

        spin, hid = self.make_spin_button(.2, 1, 0, 100, 1, False, 50, None, 0)
        self.stateobj['THRES1'] = (spin, hid)
        table_aom.attach(spin, 3, 4, 8, 9, gtk.FILL, gtk.FILL)


        table_pp = gtk.Table(rows=2, columns=4, homogeneous=True)
        table_pp.attach(gtk.Label('CMD '),0,1,0,1, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        table_pp.attach(gtk.Label('DATA'),2,3,0,1, gtk.FILL, gtk.FILL)
        table_pp.attach(gtk.Label('PC  '),0,1,1,2, gtk.FILL, gtk.FILL)
        table_pp.attach(gtk.Label('W   '),2,3,1,2, gtk.FILL, gtk.FILL)

        # Create a threshold spinbutton
        self.stateobj['CMD'] = gtk.Label('-----')
        table_pp.attach(self.stateobj['CMD'], 1, 2, 0, 1, gtk.FILL, gtk.FILL)
        self.stateobj['DATA'] = gtk.Label('-----')
        table_pp.attach(self.stateobj['DATA'], 3, 4, 0, 1, gtk.FILL, gtk.FILL)
        self.stateobj['PC'] = gtk.Label('-----')
        table_pp.attach(self.stateobj['PC'], 1, 2, 1, 2, gtk.FILL, gtk.FILL)
        self.stateobj['W'] = gtk.Label('-----')
        table_pp.attach(self.stateobj['W'], 3, 4, 1, 2, gtk.FILL, gtk.FILL)

        box.pack_start(table_aom, True, True, 0)
        box.pack_start(table_pp, True, True, 10)
        return box

    def make_progdef_view(self):
        box = gtk.VBox(False, 0)
        self.params = coltree.typical_ncol_tree([(gobject.TYPE_STRING, 'Parameter Name', 1),
                                                (gobject.TYPE_DOUBLE, 'Parameter Value', 1)])

        keys = coltree.list_keys_from_config('Params:tree')

        for key in keys:
            self.params.add_row(key, 0)
        for i in range(len(keys), 20):
            self.params.add_row('<PARAM%d>'%(i), 0)

        self.params.restore_state('Params')

        box.pack_start(self.params.treeview, True, True, 0)
        return box

    def make_control_view(self):
        box = gtk.HBox(False, 0)

        # buttons to run pulse sequencer
        button_load = gtk.Button("Load", gtk.STOCK_OPEN)
        box.pack_start(button_load, True, True, 0)

        button_save = gtk.Button("Save", gtk.STOCK_SAVE_AS)
        box.pack_start(button_save, True, True, 0)

        button_run = gtk.Button("Run")
        box.pack_start(button_run, True, True, 0)

        button_stop = gtk.Button("Stop")
        box.pack_start(button_stop, True, True, 0)

        button_read = gtk.Button("Readout")
        box.pack_start(button_read, True, True, 0)

        button_reset = gtk.Button("Reset PP")
        box.pack_start(button_reset, True, True, 0)

        button_plot_reset = gtk.Button("Reset Plot")
        box.pack_start(button_plot_reset, True, True, 0)

        button_run.connect("clicked", self.pp_run)
        button_stop.connect("clicked", self.pp_stop)
        button_load.connect("clicked", self.pp_load)
        button_save.connect("clicked", self.pp_save)
        button_read.connect("clicked", self.pp_readout)
        button_reset.connect("clicked", self.pp_reset)
        button_plot_reset.connect("clicked", self.pp_plot_reset)

        return box

    ################################################################
    # on_quit_activate
    #
    # Run when window is closed
    ################################################################
    def on_quit_activate(self, widget, event, data = None):
        self.params.save_state("Params")
        self.plug.close()
        gtk.main_quit()
        return True

    def make_spin_button(self, climb_rate, digits, range_low, range_high, increments, wrap, value, callback, key):
        sb = gtk.SpinButton(None, climb_rate, digits)
        sb.set_range(range_low, range_high)
        sb.set_increments(increments, increments)
        sb.set_wrap(wrap)
        if (value == None):
            value = mcxem.get_state(key)
        sb.set_value(value)
        if callback:
            hid = sb.connect("value-changed", callback, key)
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

    def update_state(self):
        self.lock.acquire()
        try:
			#Commented CWC 04032012
            data = '\x00'*32
            xem.ReadFromPipeOut(0xA1, data)

            if ((data[:2] != '\xED\xFE') or (data[-2:] != '\xED\x0F')):
                print "Bad data string: ", map(ord, data)
                return True

            data = map(ord, data[2:-2])

            #Decode
            active =  bool(data[1] & 0x80)
            self.state['pp_PC'] = ((data[1] & 0xF)<<8) + data[0]
            self.state['pp_W'] = (data[3]<<8) + data[2]
            self.state['pp_DATA'] = (data[6]<<16) + (data[5]<<8) + data[4]
            self.state['pp_CMD'] = data[7]
            self.state['DDS0_FRQ'] = self.dds_base_freq*((data[11]<<24) + (data[10]<<16) + (data[9]<<8) + data[8])
            self.state['DDS1_FRQ'] = self.dds_base_freq*((data[15]<<24) + (data[14]<<16) + (data[13]<<8) + data[12])
            self.state['DDS2_FRQ'] = self.dds_base_freq*((data[19]<<24) + (data[18]<<16) + (data[17]<<8) + data[16])
            self.state['DDS0_AMP'] = data[20]&0x3F
            self.state['DDS1_AMP'] = ((data[21]&0xF)<<2) + (data[20]>>6)
            self.state['DDS2_AMP'] = ((data[22]&0x3)<<4) + (data[21]>>4)
            self.state['DDS0_PHS'] = (data[23]<<6) + (data[22]>>2)
            self.state['DDS1_PHS'] = ((data[25]&0x3F)<<8) + (data[24])
            self.state['DDS2_PHS'] = ((data[27]&0xF)<<10) + (data[26]<<6) + (data[25]>>6)
            self.state['SHUTR'] = data[27]>>4

            # Display
            self.stateobj['PC'].set_label('%d'%self.state['pp_PC'])
            self.stateobj['CMD'].set_label('%d'%self.state['pp_CMD'])
            self.stateobj['DATA'].set_label('%d'%self.state['pp_DATA'])
            self.stateobj['W'].set_label('%d'%self.state['pp_W'])

            for key in self.state:
                if not self.stateobj.has_key(key):
                    continue

                if ((self.state.has_key('pp_active') and self.state['pp_active']) or active):
                    self.stateobj[key][0].handler_block(self.stateobj[key][1])
                    self.stateobj[key][0].set_sensitive(False)
                    self.stateobj[key][0].set_value(self.state[key])
                    self.stateobj[key][0].handler_unblock(self.stateobj[key][1])
                else:
                    self.stateobj[key][0].set_sensitive(True)

                    if (abs(self.stateobj[key][0].get_value() - self.state[key]) > 1e-6): #modified? 04042012
                        print "Inconsistent state of %s, actual value:"%(key), self.state[key], self.stateobj[key][0].get_value()

            self.state['pp_active'] =  bool(data[1] & 0x80)
        finally:
            self.lock.release()

        return True


    ################################################################
    # Static DDS commands

    def freq_changed(self, widget, data = None):
        freq = widget.get_value()	# frequency in MHz

        x = int((freq/self.dds_base_freq)*0x80000000)	# frequency in number
        print freq, hex(int(x))

        chan = data % 2
        board = int(data)/2		# 0 = DDS1, 1 = DDS2, 2 = DDS3
        chanCmd = 0x0006 + (0x01 << (6 + chan))
        print data, board, chan, chanCmd
        #fint = int(round(x))
        #xlow = fint & 0xffff
        #xhigh = (fint >> 16) & 0xffff

        #********************************************************************************************
        print 'sending channel update'
        xem.SetWireInValue(0x01, chanCmd)
        xem.SetWireInValue(0x02, 0x0000)
        xem.SetWireInValue(0x00, (board<<2) + 0x3, 0x0FFF)
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x40, 1)

        #time.sleep(0.2)

        #print 'shifting out'
        #xem.UpdateWireOuts()
        #print hex(xem.GetWireOutValue(0x20))
        #print hex(xem.GetWireOutValue(0x21))
        #print hex(xem.GetWireOutValue(0x22))
        #print hex(xem.GetWireOutValue(0x23))

        #time.sleep(0.2)

        #********************************************************************************************
        print 'sending frequency update'
        xem.SetWireInValue(0x01, (x & 0x0000FFFF))
        xem.SetWireInValue(0x02, (x & 0xFFFF0000) >> 16)
        xem.SetWireInValue(0x00, (board<<2) + 0x0, 0x0FFF)
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x40, 1)

        #time.sleep(0.2)

        #print 'shifting out'
        #xem.UpdateWireOuts()
        #print hex(xem.GetWireOutValue(0x20))
        #print hex(xem.GetWireOutValue(0x21))
        #print hex(xem.GetWireOutValue(0x22))
        #print hex(xem.GetWireOutValue(0x23))

        #print "Setting amplitude %gdB"%(amp/2.)
        return True

    def amp_changed(self, widget, data= None):
        amp = int(max(0, round(widget.get_value())))
        a = int(0x06001000 + amp)
        print amp, hex(a)

        chan = data % 2
        board = int(data)/2		# 0 = DDS1, 1 = DDS2, 2 = DDS3
        chanCmd = 0x0006 + (0x01 << (6 + chan))
        print board, chan, chanCmd

        #********************************************************************************************
        print 'sending channel update'
        xem.SetWireInValue(0x01, chanCmd)
        xem.SetWireInValue(0x02, 0x0000)
        xem.SetWireInValue(0x00, (board<<2) + 0x3, 0x0FFF)
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x40, 1)

        #time.sleep(0.2)

        #print 'shifting out'
        #xem.UpdateWireOuts()
        #print hex(xem.GetWireOutValue(0x20))
        #print hex(xem.GetWireOutValue(0x21))
        #print hex(xem.GetWireOutValue(0x22))
        #print hex(xem.GetWireOutValue(0x23))

        #time.sleep(0.2)

        #********************************************************************************************


        print 'sending amplitude update'
        xem.SetWireInValue(0x01, (a & 0x0000FFFF))
        xem.SetWireInValue(0x02, (a & 0xFFFF0000) >> 16)
        xem.SetWireInValue(0x00, (board<<2) + 0x2, 0x0FFF)
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x40, 1)

        #time.sleep(0.2)

        #print 'shifting out'
        #xem.UpdateWireOuts()
        #print hex(xem.GetWireOutValue(0x20))
        #print hex(xem.GetWireOutValue(0x21))
        #print hex(xem.GetWireOutValue(0x22))
        #print hex(xem.GetWireOutValue(0x23))

        #print "Setting amplitude %gdB"%(amp/2.)
        return True

    def phase_changed(self, widget, data= None):
        phase = int(max(0, round(widget.get_value())))
        p = int(0x00050000 + phase)
        print phase, hex(p)

        chan = data % 2
        board = int(data)/2		# 0 = DDS1, 1 = DDS2, 2 = DDS3
        chanCmd = 0x0006 + (0x01 << (6 + chan))
        print data, board, chan, chanCmd

        #********************************************************************************************
        print 'sending channel update'
        xem.SetWireInValue(0x01, chanCmd)
        xem.SetWireInValue(0x02, 0x0000)
        xem.SetWireInValue(0x00, (board<<2) + 0x3, 0x0FFF)
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x40, 1)

        #time.sleep(0.2)

        #print 'shifting out'
        #xem.UpdateWireOuts()
        #print hex(xem.GetWireOutValue(0x20))
        #print hex(xem.GetWireOutValue(0x21))
        #print hex(xem.GetWireOutValue(0x22))
        #print hex(xem.GetWireOutValue(0x23))

        #time.sleep(0.2)

        #********************************************************************************************


        print 'sending phase update'
        xem.SetWireInValue(0x01, (p & 0x0000FFFF))
        xem.SetWireInValue(0x02, (p & 0xFFFF0000) >> 16)
        xem.SetWireInValue(0x00, (board<<2) + 0x1, 0x0FFF)
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x40, 1)

        #time.sleep(0.2)

        #print 'shifting out'
        #xem.UpdateWireOuts()
        #print hex(xem.GetWireOutValue(0x20))
        #print hex(xem.GetWireOutValue(0x21))
        #print hex(xem.GetWireOutValue(0x22))
        #print hex(xem.GetWireOutValue(0x23))

        #print "Setting phase to %d"%(phase)

        return True

    def shutter_changed(self, widget, data=None):
        shutter = int(max(0, widget.get_value()))
        xem.SetWireInValue(0x00, shutter<<12, 0xF000)    # address, value, mask
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x40, 1)

        print "Setting shutter to %d"%(shutter)

        return True


    ################################################################
    # pulse sequencer commands

    def pp_run(self, widget = None, data = None):
        xem.ActivateTriggerIn(0x40, 3)
        self.pp_upload()
        starttime=time.time()
        xem.ActivateTriggerIn(0x40, 2)

##        time.sleep(0.2)
        #print 'shifting out'
        xem.UpdateWireOuts()
        finishtime=time.time()
        print "Time taken to trigger the FPGA: %.6f" %(finishtime-starttime)
##        print hex(xem.GetWireOutValue(0x20))
##        print hex(xem.GetWireOutValue(0x21))
##        print hex(xem.GetWireOutValue(0x22))
##        print hex(xem.GetWireOutValue(0x23))
##        print "cmd: "
##        print hex(xem.GetWireOutValue(0x24))
##        print hex(xem.GetWireOutValue(0x25))
##        print hex(xem.GetWireOutValue(0x26))
##        print hex(xem.GetWireOutValue(0x27))


        return True

    def pp_run_2(self, widget = None, data = None):
        #time.sleep(0.2)
        xem.ActivateTriggerIn(0x40, 2)

        #print 'shifting out'
        xem.UpdateWireOuts()
        #print hex(xem.GetWireOutValue(0x20))
        #print hex(xem.GetWireOutValue(0x21))
        #print hex(xem.GetWireOutValue(0x22))
        #print hex(xem.GetWireOutValue(0x23))
        #print "cmd: "
        #print hex(xem.GetWireOutValue(0x24))
        #print hex(xem.GetWireOutValue(0x25))
        #print hex(xem.GetWireOutValue(0x26))
        #print hex(xem.GetWireOutValue(0x27))
        return True

    def pp_Host_stop(self, widget = None, data = None):
        xem.ActivateTriggerIn(0x40, 3)
        return True

    def pp_stop(self, widget, data= None):
        xem.ActivateTriggerIn(0x40, 3)
        return True

    def pp_save(self, widget, data= None):
        data = self.data
        buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK)
        d = gtk.FileChooserDialog("Choose File", None, gtk.FILE_CHOOSER_ACTION_SAVE, buttons)
        d.set_current_folder(os.getcwd())

        rv = d.run()
        if rv == gtk.RESPONSE_OK:
            file = d.get_filename()
			#file="Bluetest.pp"
            try:
                fd = open(file, 'w')
                for i in range(len(data)):
                    fd.write('%d %d %d\n'%(data[i, 0], data[i, 1], data[i,2]))
                fd.close
            except Exception, E:
                print E
        d.destroy()

        return True

    def pp_load(self, widget, data = None):
        buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)
        d = gtk.FileChooserDialog("Choose File", None, gtk.FILE_CHOOSER_ACTION_OPEN, buttons)
        d.set_current_folder(os.getcwd() + '/prog/')

        rv = d.run()
        if rv == gtk.RESPONSE_OK:
            file = d.get_filename()
            print file
            d.destroy()
        else:
            d.destroy()
            return True

        self.pp_setprog(file)

        print file
        self.pp_upload()
        return True

    def pp_setprog(self, file):
        self.codefile = file
        xem.ActivateTriggerIn(0x40, 3)
        self.pp_upload()
        return True

    def pp_upload(self):

        parameters = {}
        for key in self.params.rows:
            parameters.update({key : self.params.get_data(key, 1)})

        code = pp2bytecode(self.codefile, parameters)

        databuf = ''
        for op, arg in code:
            memword = '%c%c'%((arg&0xFF), (arg>>8)&0xFF) + '%c%c'%((arg>>16)&0xFF, op + (arg>>24))
            #print '%x, %x, %x, %x' %(ord(memword[0]), ord(memword[1]), ord(memword[2]), ord(memword[3]))
            databuf = databuf + memword

        t1 = time.time()
        xem.SetWireInValue(0x00, 0, 0x0FFF)	# start addr at zero
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x41, 1)
        xem.WriteToPipeIn(0x80, databuf)
        t2 = time.time()
        print "Upload successful in time %fs"%(t2 - t1)
        return True

    def parameter_read(self, name):
        return "RESULT: %g\n"%(self.params.get_data(name, 1))

    def parameter_set(self, name, value):
        self.params.set_data(name, 1, float(value))
        return True

    def pp_is_running(self):
        self.lock.acquire()
        try:
			#Commented CWC 04032012
            data = '\x00'*32
            xem.ReadFromPipeOut(0xA1, data)

            if ((data[:2] != '\xED\xFE') or (data[-2:] != '\xED\x0F')):
                print "Bad data string: ", map(ord, data)
                return True

            data = map(ord, data[2:-2])

            #Decode
            active =  bool(data[1] & 0x80)
        finally:
            self.lock.release()
        #print active
        return active

    def pp_readout(self, widget = None, data = None):
        # while(self.pp_is_running()==True):
            # print 'Wait for pp to finish running'

        self.update_count()

        #self.plotdata[:,2] = numpy.log(numpy.abs(self.data[:,2]) + 1)
        self.axis1.clear()
        self.axis2.clear()
        self.axis1.plot(self.data[:,0],self.data[:,1],'r')
        self.axis1.set_ylabel('Counts', color='r')
        self.axis1.set_xlabel('Bins')
        #self.axis2.plot(self.plotdata[:,0],self.plotdata[:,2],'b') #should add readout to the plot
        self.axis2.plot(self.hist,'b') #should add readout to the plot
        self.axis2.set_ylabel('Hist', color='b')
        self.plot.draw()


        return True

    def pp_reset(self, widget = None, data = None):
        xem.ActivateTriggerIn(0x40,0)
        xem.ActivateTriggerIn(0x41,0)
        for key in self.stateobj:
            if ((key[:3] != 'DDS') and (key != 'SHUTR')): continue
            self.stateobj[key][0].handler_block(self.stateobj[key][1])
            self.stateobj[key][0].set_value(0.0)
            self.stateobj[key][0].handler_unblock(self.stateobj[key][1])

        return True

    def pp_plot_reset(self, widget = None, data = None):
        self.axis1.clear()  #Should Clear the Plot
        self.axis2.clear()
        self.hist=numpy.zeros(self.get_datapoints(),"Int32")
        self.plot.draw()

        return True

    def get_datastart(self):
        data=self.parameter_read('datastart')
        out=data.split()
        datastart=int(out[1])
        #print datastart
        return datastart

    def get_datapoints(self):
        datapoints=4000-self.get_datastart()
        return datapoints

    ###############################################################
    # update_count
    #
    # Displays latest count
    ###############################################################
    def update_count(self):
        t1 = time.time()
        while (self.pp_is_running()):
            continue
        #print self.pp_is_running()
        data_start=self.get_datastart()
        datapoints=4000-data_start
        self.data=numpy.zeros([datapoints,2],'Int32')
        count = numpy.zeros([datapoints],'Int32')
        readout_OK = True
        #self.plotdata =numpy.zeros([datapoints,2], 'Float32')

        xem.SetWireInValue(0x00, data_start, 0x0FFF)	# start addr at 3900
        xem.UpdateWireIns()
        xem.ActivateTriggerIn(0x41, 1)

        data = '\x00'*4*datapoints
        xem.ReadFromPipeOut(0xA0, data)
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
            if (len(self.hist)!=hist_max+1):
                self.hist=numpy.zeros(hist_max+1,'Int32')
            histogram=numpy.histogram(self.data[:,1],hist_max+1,(0,hist_max),True)
            #print histogram[0]
            #self.hist=self.hist+histogram[0]
            self.hist=histogram[0]
            t2 = time.time()
            #print "Memory read in %.6f seconds" % (t2-t1)

        else:
            t2 = time.time()
            print "Memory read in %.6f seconds" % (t2-t1)
            print "Data readout error"

        return readout_OK
	    # Histogram
         #   if (count < datapoints):
         #       self.data[count][2] = self.data[count][2]+ 1

##        if (len(self.hist)!=datapoints):
##            self.hist=numpy.zeros(datapoints,'Int32')
##        histogram=numpy.histogram(self.data[:,1],datapoints,(0,datapoints))
##        #print histogram[0]
##        self.hist=self.hist+histogram[0]
        #print self.hist
        #print self.data[:,1]
        #print self.data[:,2]
        #self.data[:,2]=self.hist

        #print self.hist
##        t2 = time.time()
##        print "Memory read in %.6f seconds" % (t2-t1)
##        #print "Memory contents: ", map(hex, map(int, self.data[:,1]))
##        return

    def net_countabove(self):
        self.pp_readout()
        count = 0
        threshold0 = self.stateobj['THRES0'][0].get_value()
        threshold1 = self.stateobj['THRES1'][0].get_value()
        for addr in range(self.get_datapoints()):
            if (self.data[addr][1] > threshold1):
                count = count + 2
            elif (self.data[addr][1] > threshold0):
                count = count + 1

        return "RESULT: %d\n"%(count)

    def net_lastavg(self):
        #self.pp_readout()
        self.update_count()
        count = 0
        tot = 0
        threshold0 = self.stateobj['THRES0'][0].get_value()
        threshold1 = self.stateobj['THRES1'][0].get_value()
        for addr in range(self.get_datapoints()):
            if (self.data[addr][1] > threshold1):
                count = count + 2
                tot = tot + self.data[addr][1]
            elif (self.data[addr][1] >= threshold0):  #changed this line to >= from >  For heating rate exp.  (Craig Oct 24 2008)
                count = count + 1
                tot = tot + self.data[addr][1]
        if (count < 1):
       	    return "RESULT: 0\n"
        else:
            return "RESULT: %f\n"%(1.0*tot/count)




    def net_memory(self):
        #self.pp_readout()
        self.update_count()

        memory = 'RESULT:'
        for addr in range(self.get_datapoints()):
	    memory = memory + " %i"%(self.data[addr][1])

        return memory + "\n"

    def user_stop(self):
        return self.pp_Host_stop()


xem = ok.FrontPanel()
module_count = xem.GetDeviceCount()

print "Found %d modules"%(module_count)
if (module_count == 0): raise "No XEMs found!"
id = ''

for i in range(module_count):
    serial = xem.GetDeviceListSerial(i)
    tmp = ok.FrontPanel()
    tmp.OpenBySerial(serial)
    id = tmp.GetDeviceID()
    print id
    tmp = None
    if (id == 'Sandia_1725_PP' or id == 'AQC_1272_PP'):
        break
if (id  != 'Sandia_1725_PP' and id != 'AQC_1272_PP'):
    raise "Didn't find Sandia_1725_PP or AQC_1272_PP in module list!"

xem.OpenBySerial(serial)
print "Found device called %s"%(xem.GetDeviceID())

print "Loading PLL config"
pll = ok.PLL22393()
xem.GetEepromPLL22393Configuration(pll)
pll.SetPLLParameters(0, 200, 48, True)
pll.SetPLLParameters(1, 240, 48, False)
pll.SetPLLParameters(2, 240, 48, False)  #change 200 to 240 CWC 05212012

for i in range(5):
    pll.SetOutputSource(i, pll.ClkSrc_PLL0_0)
    pll.SetOutputDivider(i, 2)
    pll.SetOutputEnable(i, (i == 0) or (i==3))

print "Ref is at %gMHz, PLL is at %gMHz"%(pll.GetReference(), pll.GetPLLFrequency(0))
for i in range(5):
    if (pll.IsOutputEnabled(i)):
        print "Clock %d at %gMHz"%(i, pll.GetOutputFrequency(i))

print "Programming PLL"
# xem.SetEepromPLL22393Configuration(pll)
xem.SetPLL22393Configuration(pll)

print "Programming FPGA"
#xem.ConfigureFPGA('DDSfirmware-original.bit')
xem.ConfigureFPGA('DDSfirmware.bit')#.bit PLL_clk _2_ti_clk


#********************************************************************************************
print 'Resetting DDS Boards and Updating PLL Multipliers'
for board in range(3):
    xem.SetWireInValue(0x03, 0x0001) #set sel to 1 CWC 08092012
    xem.SetWireInValue(0x00, (board<<2) + 0x2, 0x0FFF) #set ddscmd[3:2] to choose the corresponding DDS (0, 1, or 2) 0x2 -> 0b10 setting AMP CWC 08092012

    xem.UpdateWireIns()

    #reset individual board
    xem.ActivateTriggerIn(0x42, 0)
    time.sleep(0.2)

    #send individual command
    xem.ActivateTriggerIn(0x40, 1)
    #time.sleep(0.1)
    xem.SetWireInValue(0x03, 0x0000) #set sel to 0 CWC 08092012
    xem.UpdateWireIns()

    #time.sleep(0.2)

    #print 'shifting out'
    #xem.UpdateWireOuts()
    #print hex(xem.GetWireOutValue(0x20))
    #print hex(xem.GetWireOutValue(0x21))
    #print hex(xem.GetWireOutValue(0x22))
    #print hex(xem.GetWireOutValue(0x23))

    #time.sleep(0.2)

    xem.SetWireInValue(0x01, 0x0000)
    xem.SetWireInValue(0x02, 0x01a8) #set dds_data to 0x01a80000, fixedData->0x01a8000000 CWC 08092012
    xem.UpdateWireIns()
    xem.ActivateTriggerIn(0x40, 1) #signaling new command CWC 08092012

    #time.sleep(0.2)

    #print 'shifting out'
    #xem.UpdateWireOuts()
    #print hex(xem.GetWireOutValue(0x20))
    #print hex(xem.GetWireOutValue(0x21))
    #print hex(xem.GetWireOutValue(0x22))
    #print hex(xem.GetWireOutValue(0x23))

    amp = 0     #startup amplitude
    a = int(0x06001000 + amp)
    xem.SetWireInValue(0x01, (a & 0x0000FFFF))
    xem.SetWireInValue(0x02, (a & 0xFFFF0000) >> 16)
    xem.SetWireInValue(0x00, (board<<2) + 0x2, 0x0FFF)
    xem.UpdateWireIns()
    xem.ActivateTriggerIn(0x40, 1)

# gui
app = gui()

# We're threading, init that
gtk.gdk.threads_init()
gtk.gdk.threads_enter()
# Run
try:
    pass
    gtk.main()
finally:
    # If we died, let the child thread know
    print "Quitting..."
gtk.gdk.threads_leave()

