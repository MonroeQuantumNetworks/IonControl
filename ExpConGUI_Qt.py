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
#from datetime import datetime
import datetime
#import pango, math
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
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as \
        FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as \
        NavigationToolbar
from matplotlib.axes import Subplot
from matplotlib.axes import Axes
from pylab import *
import matplotlib.patches as patches
import matplotlib.path as path
import coltree_Qt

from PyQt4 import QtGui, QtCore
import shutil
import visa

dirname = 'C:/Data/'
#dirname = '/Users/ahankin/Research/Data/'



##def main():
##    pass
##
##if __name__ == '__main__':
##    main()


class ExpConGUI_Qt(QtGui.QWidget):
    def __init__(self,driver,file):#):#
        super(ExpConGUI_Qt, self).__init__()
        self.threads = []
        self.thread_count = 0
        self.ppfile = './prog/'+file
        self.plotdatalength = 21
        self.plotdata=numpy.zeros((self.plotdatalength,2),'Float32')
        self.plotdata[:,0]=numpy.linspace(0, self.plotdatalength-1,
                self.plotdatalength)
        self.plotdata[:,1]=numpy.zeros(self.plotdatalength)
        self.stateobj = {}
        self.controls = {}
        self.ind = {}
        self.filename = []
        self.timestamp = time.strftime('%Y%m%d_%H%M%S')
        self.run_exp = True
        self.pause = False
        self.new_scan = True #Switch for a new scan. Log file created if True.
        self.hist_max = 30
        self.t1 = time.time()
        self.scan_types =['Continuous','Frequency','1038 Frequency','Time','Voltage', 'DDS Amplitude', 'Ramsey Phase Scan']
        self.text_to_write = ''
        #self.SHUTR_CHAN = {'SHUTR_MOT_': 0, 'SHUTR_Repump_': 1,'SHUTR_uWave_':
        #        7, 'SHUTR_D1_': 5, 'SHUTR_Dipole_': 3, 'SHUTR_MOT_Servo_':
        #        4, 'SHUTR_MOTradial_': 2, 'SHUTR_459_': 6, 'SHUTR_1038_': 8} #Define the TTL channels
        self.SHUTR_CHAN = driver.SHUTR_CHAN
        # Initialize public variables
        self.data_start = 4000
        self.reuseDataEnd = 3100
        self.reuseDataStart = 3001
        self.reuseBinAddr = 3000

        self.PCon = driver      #DDS_GUI_Sandia_AQC.DDS_gui()
        self.PCon.pp_setprog(str(self.ppfile))#DarkHist  Detect DarkHist
        self.PCon.pp_upload()
        self.n_reps = self.PCon.get_datapoints()

        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        hbox3 = QtGui.QHBoxLayout()
        hbox4 = QtGui.QHBoxLayout()
        hbox5 = QtGui.QHBoxLayout()
        hbox6 = QtGui.QHBoxLayout()
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
        self.scan_entry = QtGui.QComboBox()
        
        self.btn_1038popup = QtGui.QPushButton('1038 control',self)
        #self.connect(self.btn_1038popup, QtCore.SIGNAL("clicked()"), self.OpenPopUpWindow)

        
        for n in range(len(self.scan_types)):
            self.scan_entry.addItem(self.scan_types[n])
        
        self.scan_entry.currentIndexChanged.connect(self.update_scan_type)

        var_label = QtGui.QLabel("Scan variable")
        
        self.var_entry = QtGui.QComboBox()
        self.PCon.params.update_defs()
        for key in self.PCon.params.defs:
            self.var_entry.addItem(key)
        #self.var_entry.set_popdown_strings()
        self.var_entry.setDisabled(True)
        
        self.var_entry.currentIndexChanged.connect(self.update_var)
        
        #layout hbox2
        hbox2.addStretch(.3)
        hbox2.addWidget(self.btn_1038popup)
        hbox2.addStretch(.3)
        hbox2.addWidget(scan_label)
        hbox2.addWidget(self.scan_entry)
        hbox2.addStretch(.3)
        hbox2.addWidget(var_label)
        hbox2.addWidget(self.var_entry)
        hbox2.addStretch(.3)
        
        control_table = self.make_table_control()

        self.range_low_label = QtGui.QLabel("Start")
        self.scan_range_low_sb = QtGui.QDoubleSpinBox()
        self.scan_range_low_sb.setRange(-10, 10)
        self.scan_range_low_sb.setSingleStep(0.1)
        self.scan_range_low_sb.setValue(0)
        self.scan_range_low_sb.setDecimals(3)
        hbox3.addWidget(self.range_low_label)
        hbox3.addWidget(self.scan_range_low_sb)

        self.range_high_label = QtGui.QLabel("Stop")
        self.scan_range_high_sb = QtGui.QDoubleSpinBox()
        self.scan_range_high_sb.setRange(-10, 10)
        self.scan_range_high_sb.setSingleStep(0.1)
        self.scan_range_high_sb.setValue(10)
        self.scan_range_high_sb.setDecimals(3)
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
        self.n_index = QtGui.QLabel("-")
        hbox3.addWidget(self.n_index_label)
        hbox3.addWidget(self.n_index)
        
        self.scanVal_label = QtGui.QLabel("Current value:")
        self.scanVal = QtGui.QLabel("-")
        hbox3.addWidget(self.scanVal_label)
        hbox3.addWidget(self.scanVal)

        self.shuffle_label = QtGui.QLabel("Shuffle scan")
        self.shuffle_cb = QtGui.QCheckBox()
        self.shuffle_cb.setChecked(True)
        self.shuffle_cb.setDisabled(True)
        hbox3.addWidget(self.shuffle_label)
        hbox3.addWidget(self.shuffle_cb)
        
        self.qubit_D_label = QtGui.QLabel("Qubit detection")
        self.qubit_D_cb = QtGui.QCheckBox()
        self.qubit_D_cb.setChecked(False)
        self.qubit_D_cb.setDisabled(False)
        hbox3.addWidget(self.qubit_D_label)
        hbox3.addWidget(self.qubit_D_cb)
        
        self.rep_label = QtGui.QLabel("Rep. per point")
        self.rep_sb = QtGui.QSpinBox()
        self.rep_sb.setRange(1, 1000)
        self.rep_sb.setSingleStep(1)
        self.rep_sb.setValue(self.n_reps)
        hbox3.addWidget(self.rep_label)
        hbox3.addWidget(self.rep_sb)

        # TODO: throw exception if reqeusted memory is too large
        self.partitionFpgaMemory()

        self.Load_SW_label = QtGui.QLabel("Load atom")
        self.Load_SW_cb = QtGui.QCheckBox()
        self.Load_SW_cb.setChecked(True)
        self.Load_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['LOAD_SWITCH'])==1):
            self.Load_SW_cb.setChecked(False)
        hbox4.addWidget(self.Load_SW_label)
        hbox4.addWidget(self.Load_SW_cb)

        self.Cool_SW_label = QtGui.QLabel("PG cooling")
        self.Cool_SW_cb = QtGui.QCheckBox()
        self.Cool_SW_cb.setChecked(True)
        self.Cool_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['COOL_SWITCH'])==1):
            self.Cool_SW_cb.setChecked(False)
        hbox4.addWidget(self.Cool_SW_label)
        hbox4.addWidget(self.Cool_SW_cb)

        self.Wait2_SW_label = QtGui.QLabel("Wait2")
        self.Wait2_SW_cb = QtGui.QCheckBox()
        self.Wait2_SW_cb.setChecked(True)
        self.Wait2_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['WAIT2_SWITCH'])==1):
            self.Wait2_SW_cb.setChecked(False)
        hbox4.addWidget(self.Wait2_SW_label)
        hbox4.addWidget(self.Wait2_SW_cb)

        self.OP_SW_label = QtGui.QLabel("O. Pumping")
        self.OP_SW_cb = QtGui.QCheckBox()
        self.OP_SW_cb.setChecked(True)
        self.OP_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['OP_SWITCH'])==1):
            self.OP_SW_cb.setChecked(False)
        hbox4.addWidget(self.OP_SW_label)
        hbox4.addWidget(self.OP_SW_cb)

        self.Wait3_SW_label = QtGui.QLabel("Wait3")
        self.Wait3_SW_cb = QtGui.QCheckBox()
        self.Wait3_SW_cb.setChecked(True)
        self.Wait3_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['WAIT3_SWITCH'])==1):
            self.Wait3_SW_cb.setChecked(False)
        hbox4.addWidget(self.Wait3_SW_label)
        hbox4.addWidget(self.Wait3_SW_cb)

        self.Exp_SW_label = QtGui.QLabel("Exp")
        self.Exp_SW_cb = QtGui.QCheckBox()
        self.Exp_SW_cb.setChecked(True)
        self.Exp_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['EXP_SWITCH'])==1):
            self.Exp_SW_cb.setChecked(False)
        hbox4.addWidget(self.Exp_SW_label)
        hbox4.addWidget(self.Exp_SW_cb)

        self.Wait4_SW_label = QtGui.QLabel("Wait4")
        self.Wait4_SW_cb = QtGui.QCheckBox()
        self.Wait4_SW_cb.setChecked(True)
        self.Wait4_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['WAIT4_SWITCH'])==1):
            self.Wait4_SW_cb.setChecked(False)
        hbox4.addWidget(self.Wait4_SW_label)
        hbox4.addWidget(self.Wait4_SW_cb)

        self.Check_SW_label = QtGui.QLabel("Check atom for reuse")
        self.Check_SW_cb = QtGui.QCheckBox()
        self.Check_SW_cb.setChecked(True)
        self.Check_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['CHECK_SWITCH'])==1):
            self.Check_SW_cb.setChecked(False)
        hbox4.addWidget(self.Check_SW_label)
        hbox4.addWidget(self.Check_SW_cb)
        
        self.Loss_SW_label = QtGui.QLabel("Use atom loss as signal")
        self.Loss_SW_cb = QtGui.QCheckBox()
        self.Loss_SW_cb.setChecked(True)
        self.Loss_SW_cb.stateChanged.connect(self.set_stage_Disabled)
        if (not float(self.PCon.params.defs['LOSS_SWITCH'])==1):
            self.Loss_SW_cb.setChecked(False)
        self.Loss_SW_cb.setDisabled(True)
        hbox4.addWidget(self.Loss_SW_label)
        hbox4.addWidget(self.Loss_SW_cb)

        self.LOADTHOLD_label = QtGui.QLabel("LOADTHOLD")
        self.LOADTHOLD_lsb = LabeledSpinBox('LOADTHOLD',self.update_global_var)#QtGui.QSpinBox()
        self.LOADTHOLD_lsb.sb.setRange(0, 25)
        self.LOADTHOLD_lsb.sb.setSingleStep(1)
        self.LOADTHOLD_lsb.sb.setDecimals(0)
        self.LOADTHOLD_lsb.sb.setValue(float(self.PCon.params.defs['LOADTHOLD']))
        self.controls['LOADTHOLD']=(self.LOADTHOLD_lsb.sb, 'LOADTHOLD')
        

        self.LOADREP_label = QtGui.QLabel("LOADREP")
        self.LOADREP_lsb = LabeledSpinBox('LOADREP',self.update_global_var)#QtGui.QSpinBox()
        self.LOADREP_lsb.sb.setRange(0, 20000)
        self.LOADREP_lsb.sb.setSingleStep(1)
        self.LOADREP_lsb.sb.setDecimals(0)
        self.LOADREP_lsb.sb.setValue(float(self.PCon.params.defs['LOADREP']))
        self.controls['LOADREP']=(self.LOADREP_lsb.sb, 'LOADREP')
        

        self.CHECKTHOLD_label = QtGui.QLabel("CHECKTHOLD")
        self.CHECKTHOLD_lsb = LabeledSpinBox('CHECKTHOLD',self.update_global_var)#QtGui.QSpinBox()
        self.CHECKTHOLD_lsb.sb.setRange(0, 25)
        self.CHECKTHOLD_lsb.sb.setSingleStep(1)
        self.CHECKTHOLD_lsb.sb.setDecimals(0)
        self.CHECKTHOLD_lsb.sb.setValue(float(self.PCon.params.defs['CHECKTHOLD']))
        self.controls['CHECKTHOLD']=(self.CHECKTHOLD_lsb.sb, 'CHECKTHOLD')
        

        self.CHECKREP_label = QtGui.QLabel("CHECKREP")
        self.CHECKREP_lsb = LabeledSpinBox('CHECKREP',self.update_global_var)#QtGui.QSpinBox()
        self.CHECKREP_lsb.sb.setRange(0, 5)
        self.CHECKREP_lsb.sb.setSingleStep(1)
        self.CHECKREP_lsb.sb.setDecimals(0)
        self.CHECKREP_lsb.sb.setValue(float(self.PCon.params.defs['CHECKREP']))
        self.controls['CHECKREP']=(self.CHECKREP_lsb.sb, 'CHECKREP')

        hbox5.addWidget(self.LOADTHOLD_label)
        hbox5.addLayout(self.LOADTHOLD_lsb.box)
        hbox5.addStretch(1)
        hbox5.addWidget(self.LOADREP_label)
        hbox5.addLayout(self.LOADREP_lsb.box)
        hbox5.addStretch(1)
        hbox5.addWidget(self.CHECKTHOLD_label)
        hbox5.addLayout(self.CHECKTHOLD_lsb.box)
        hbox5.addStretch(1)
        hbox5.addWidget(self.CHECKREP_label)
        hbox5.addLayout(self.CHECKREP_lsb.box)
        hbox5.addStretch(5)

        self.F_MOT_cool_final_label = QtGui.QLabel("F_MOT_cool_final")
        self.F_MOT_cool_final_lsb = LabeledSpinBox('F_INC',self.update_F_MOT_cool_final)#QtGui.QSpinBox()
        self.F_MOT_cool_final_lsb.sb.setRange(0, 100)
        self.F_MOT_cool_final_lsb.sb.setSingleStep(0.1)
        self.F_MOT_cool_final_lsb.sb.setValue(float(self.PCon.params.defs['F_MOT_cool'])+float(self.PCon.params.defs['F_INC'])*float(self.PCon.params.defs['RAMPTOT']))
        

        self.V_MOT_cool_final_label = QtGui.QLabel("V_MOT_cool_final")
        self.V_MOT_cool_final_lsb = LabeledSpinBox('V_INC',self.update_V_MOT_cool_final)#QtGui.QSpinBox()
        self.V_MOT_cool_final_lsb.sb.setRange(0, 4.999)
        self.V_MOT_cool_final_lsb.sb.setSingleStep(0.01)
        self.V_MOT_cool_final_lsb.sb.setValue(float(self.PCon.params.defs['V_MOT_cool'])+float(self.PCon.params.defs['V_INC'])*float(self.PCon.params.defs['RAMPTOT']))
        

        self.RAMPTOT_label = QtGui.QLabel("PG cooling ramp steps")
        self.RAMPTOT_lsb = LabeledSpinBox('RAMPTOT',self.update_global_var)#QtGui.QSpinBox()
        self.RAMPTOT_lsb.sb.setRange(0, 200)
        self.RAMPTOT_lsb.sb.setValue(float(self.PCon.params.defs['RAMPTOT']))
        self.controls['RAMPTOT']=(self.RAMPTOT_lsb.sb, 'RAMPTOT')
        
        hbox6.addWidget(self.F_MOT_cool_final_label)
        hbox6.addLayout(self.F_MOT_cool_final_lsb.box)
        hbox6.addStretch(1)
        hbox6.addWidget(self.V_MOT_cool_final_label)
        hbox6.addLayout(self.V_MOT_cool_final_lsb.box)
        hbox6.addStretch(1)
        hbox6.addWidget(self.RAMPTOT_label)
        hbox6.addLayout(self.RAMPTOT_lsb.box)
        hbox6.addStretch(5)

##        self.figure = plt.figure()
##        self.trace1 = self.figure.add_subplot(211)
##        self.plot = FigureCanvas(self.figure)
##        #self.plotdata[:,1] = numpy.random.shuffle(arange(21))
##        self.line1, = self.trace1.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
##        self.trace2 = self.figure.add_subplot(212)
##        #self.trace2.plot(self.plotdata[:,0],self.plotdata[:,1],'r')
##        self.plot.draw()


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

        self.button_cont = QtGui.QPushButton("Continue",self)
        self.button_cont.setDisabled(True)
        hbox.addWidget(self.button_cont)

        self.button_upParams.clicked.connect(self.update_params)
        self.button_run.clicked.connect(self.start_new_scan)
        self.button_pause.clicked.connect(self.pause_scan)
        self.button_resume.clicked.connect(self.resume_scan)
        self.button_stop.clicked.connect(self.stop_scan)
        self.button_cont.clicked.connect(self.continue_scan)

        vbox.addStretch(1)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox4)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox5)
        vbox.addLayout(hbox6)
        #vbox.addWidget(self.plot)

        vbox.addLayout(control_table)
        self.setLayout(vbox)
        self.show()


    def make_table_control(self):
        table_control = QtGui.QGridLayout()
        self.h_labels = ['Load', 'Wait1', 'PG cooling', 'Wait2', 'OP', 'Wait3', 'Exp', 'Wait4', 'Detect', 'Wait5', 'Check','Wait6']
        self.h_subscripts = ['load', 'wait1', 'cool', 'wait2', 'op', 'wait3', 'exp', 'wait4', 'detect', 'wait5', 'check', 'wait6']
        self.v_sb_labels = ['Duration (us)','MOT coils', 'uWave freq.', 'D1 OP power', 'MOT power', 'MOT detuning', 'Repump power', 'Bx', 'By', 'Bz']
        self.v_sb_subscripts = ['us_Time_', 'V_MOTcoil_', 'F_uWave_', 'A_OP_', 'V_MOT_', 'F_MOT_', 'V_Repump_', 'V_Bx_', 'V_By_', 'V_Bz_']
        self.v_tb_labels = ['MOT (TTL0)', 'Repump (TTL1)', 'uWave (TTL7)', 'D1 (TTL5)', 'Dipole (TTL3)', 'MOT P servo (TTL4)', 'MOT radial (TTL2)', '459 (TTL6)', '1038 (TTL8)']
        self.v_tb_index = ['SHUTR_MOT_', 'SHUTR_Repump_', 'SHUTR_uWave_', 'SHUTR_D1_', 'SHUTR_Dipole_', 'SHUTR_MOT_Servo_', 'SHUTR_MOTradial_', 'SHUTR_459_', 'SHUTR_1038_']

        for i in range(len(self.h_labels)):
            table_control.addWidget(QtGui.QLabel(self.h_labels[i]),0,i+1)
        for i in range(len(self.v_sb_labels)):
            table_control.addWidget(QtGui.QLabel(self.v_sb_labels[i]),i+1,0)
        for i in range(len(self.v_tb_labels)):
            table_control.addWidget(QtGui.QLabel(self.v_tb_labels[i]),i+len(self.v_sb_labels)+1,0)
        for i in range(len(self.v_sb_labels)):
            for j in range(len(self.h_labels)):
                lsb = self.make_spin_box(self.v_sb_subscripts[i],self.h_subscripts[j], self.PCon.params.defs[self.v_sb_subscripts[i]+self.h_subscripts[j]], self.update_global_var)
                #lsb.sb.setDisabled(True)
                table_control.addLayout(lsb.box,i+1,j+1)
                self.controls[self.v_sb_subscripts[i]+self.h_subscripts[j]] = (lsb.sb, self.v_sb_subscripts[i]+self.h_subscripts[j])

        for i in range(len(self.v_tb_index)):
            for j in range(len(self.h_subscripts)):
                lpb = LabeledPushButton(self.v_tb_index[i],self.h_subscripts[j], self.update_SHUTR)
                #if (not(self.h_subscripts[j]=='detect' or self.h_subscripts[j]=='wait5' or self.h_subscripts[j]=='wait6')):
                #    lpb.tb.setDisabled(True)
                table_control.addLayout(lpb.box,i+len(self.v_sb_subscripts)+1,j+1)
                self.controls[self.v_tb_index[i]+self.h_subscripts[j]] = (lpb.tb, self.v_tb_index[i]+self.h_subscripts[j])

        for i in range(len(self.v_tb_index)):
            for j in range(len(self.h_subscripts)):
                if (int(float(self.PCon.params.defs['SHUTR_'+self.h_subscripts[j]])) & 1<<self.SHUTR_CHAN[self.v_tb_index[i]]):
                    self.controls[self.v_tb_index[i]+self.h_subscripts[j]][0].setChecked(True)
                    

##        test_lsb = LabeledSpinBox('F_MOT_load',self.update_global_var)
##        test_lsb.sb.setValue(90.0)
##
##        table_control.addLayout(test_lsb.box, len(self.v_tb_index)+len(self.v_sb_subscripts)+1,1)

        return table_control


    def make_spin_box(self, v_label, h_label, value, callback):
        lsb = LabeledSpinBox(v_label+h_label, callback)
        lsb.sb.setDecimals(3)
        if (v_label == 'us_Time_'):
            lsb.sb.setDecimals(1)
            lsb.sb.setSingleStep(1)
            lsb.sb.setRange(0,5000)
        elif (v_label == 'F_MOT_' or v_label == 'F_uWave_'):
            lsb.sb.setSingleStep(0.1)
            lsb.sb.setRange(-30,100)
        elif (v_label == 'A_OP_'):
            lsb.sb.setSingleStep(1)
            lsb.sb.setDecimals(0)
            lsb.sb.setRange(0,1023)
        else:
            lsb.sb.setSingleStep(0.1)
            lsb.sb.setRange(0,4.999)
        lsb.sb.setValue(float(value))

        return lsb

    def partitionFpgaMemory(self):
        # Set memory usage for the pp file based on use request,
        # TODO: exit program if requested memory space is too large
        self.data_start = 4000 - self.n_reps+1; #Changed CWC 09122012
        self.reuseDataEnd = self.data_start - 1
        self.reuseDataStart = self.reuseDataEnd - self.n_reps + 1
        self.reuseBinAddr = self.reuseDataStart - 1
        self.PCon.parameter_set('datastart',self.data_start)
        self.PCon.parameter_set('reuseDataEnd',self.reuseDataEnd)
        self.PCon.parameter_set('reuseDataStart',self.reuseDataStart)
        self.PCon.parameter_set('reuseBinAddr',self.reuseBinAddr)

    def update_global_var(self,label,value):
        self.PCon.parameter_set(label,value)
        if label == 'us_Time_cool':
            val = value/float(self.PCon.params.defs['RAMPTOT'])-7
            if val < 1:
                raise "RAMPTOT too high for the specified cooling time. Try reducing ramp steps or longer cooling time."
            else:
                self.PCon.parameter_set('us_RAMP_T',val)

    def update_F_MOT_cool_final(self, label, value):
        val = (value - float(self.PCon.params.defs['F_MOT_cool']))/float(self.PCon.params.defs['RAMPTOT'])
        self.PCon.parameter_set(label,val)

    def update_V_MOT_cool_final(self, label, value):
        val = (value - float(self.PCon.params.defs['V_MOT_cool']))/float(self.PCon.params.defs['RAMPTOT'])
        self.PCon.parameter_set(label,val)

    def update_SHUTR(self, h_subscript):
        SHUTR_value = 0
##        print SHUTR_value
        SW = []
##        for key in self.controls:
##            if (key[:3]=='SHU'):
##                print key+':'+str(self.controls[key][1])
        for i in range(len(self.v_tb_index)):
            SW.append(0)
            if self.controls[self.v_tb_index[i]+h_subscript][0].isChecked(): SW[i] = 1

        for i in range(len(self.v_tb_index)):
            SHUTR_value += SW[i]<<self.SHUTR_CHAN[self.v_tb_index[i]]

        self.PCon.parameter_set('SHUTR_'+h_subscript, float(SHUTR_value))
        #print 'SHUTR_'+h_subscript+':%s' %bin(SHUTR_value)

    def update_pp_filename(self):
        self.Filename_entry.setText(self.ppfile)

    def update_params(self):
        self.PCon.params.update_defs()
        self.PCon.pp_upload()

    def update_var(self):
        self.n_index.setText('0')
        self.button_cont.setDisabled(True)
        self.new_scan = True

    def update_scan_type(self):
        self.n_index.setText('0')
        self.new_scan = True
        if (self.scan_entry.currentText()=='Continuous'):
            self.PCon.params.update_defs()
            self.button_cont.setDisabled(True)
            self.shuffle_cb.setDisabled(True)
            self.scan_range_low_sb.setDisabled(True)
            self.scan_range_high_sb.setDisabled(True)
            self.n_points_sb.setDisabled(True)
            self.var_entry.setDisabled(True)
            self.Loss_SW_cb.setEnabled(False)
            self.Loss_SW_cb.setChecked(False)
        elif (self.scan_entry.currentText()=='Frequency'):
            self.PCon.params.update_defs()
            self.button_cont.setDisabled(True)
            self.shuffle_cb.setDisabled(False)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(-30,100)
            self.scan_range_low_sb.setDecimals(3)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(-30,100)
            self.scan_range_high_sb.setDecimals(3)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            for key in sorted(self.PCon.params.defs.iterkeys()):#self.PCon.params.defs:
                if (key[:2]=='F_' or key[:2]=='f_'):
                    self.var_entry.addItem(key)
            self.var_entry.setEnabled(True)
            self.Loss_SW_cb.setEnabled(False)
            self.Loss_SW_cb.setChecked(False)
        elif (self.scan_entry.currentText()=='1038 Frequency'):
            self.PCon.params.update_defs()
            self.button_cont.setDisabled(True)
            self.shuffle_cb.setChecked(False)
            self.shuffle_cb.setDisabled(True)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(1.0,2.9)
            self.scan_range_low_sb.setDecimals(5)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(1.2,3.0)
            self.scan_range_high_sb.setDecimals(5)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            self.var_entry.addItem('F_uWave_exp')
            self.var_entry.setEnabled(False)
            self.Loss_SW_cb.setEnabled(True)
            self.Loss_SW_cb.setChecked(True)
        elif (self.scan_entry.currentText()=='Time'):
            self.PCon.params.update_defs()
            self.button_cont.setDisabled(True)
            self.shuffle_cb.setDisabled(False)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(0,100)
            self.scan_range_low_sb.setDecimals(2)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(1,10000)
            self.scan_range_high_sb.setDecimals(2)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            for key in sorted(self.PCon.params.defs.iterkeys()):
                if (key[:3]=='ns_' or key[:3]=='NS_' or key[:3]=='us_' or key[:3]=='US_' or key[:3]=='ms_' or key[:3]=='MS_'):
                    self.var_entry.addItem(key)
            self.var_entry.setEnabled(True)
            self.Loss_SW_cb.setEnabled(True)
            self.Loss_SW_cb.setChecked(False)
        elif (self.scan_entry.currentText()=='Voltage'):
            self.PCon.params.update_defs()
            self.button_cont.setDisabled(True)
            self.shuffle_cb.setDisabled(False)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(-0.1,5)
            self.scan_range_low_sb.setDecimals(4)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(-0.1,5)
            self.scan_range_high_sb.setDecimals(4)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            for key in sorted(self.PCon.params.defs.iterkeys()):
                if (key[:2]=='V_' or key[:2]=='v_'):
                    self.var_entry.addItem(key)
            self.var_entry.setEnabled(True)
            self.Loss_SW_cb.setEnabled(False)
            self.Loss_SW_cb.setChecked(False)
        elif (self.scan_entry.currentText()=='DDS Amplitude'):
            self.PCon.params.update_defs()
            self.button_cont.setDisabled(True)
            self.shuffle_cb.setDisabled(False)
            self.scan_range_low_sb.setDisabled(False)
            self.scan_range_low_sb.setRange(0,1023)
            self.scan_range_low_sb.setDecimals(0)
            self.scan_range_high_sb.setDisabled(False)
            self.scan_range_high_sb.setRange(0,1023)
            self.scan_range_high_sb.setDecimals(0)
            self.n_points_sb.setDisabled(False)
            self.var_entry.clear()
            for key in sorted(self.PCon.params.defs.iterkeys()):
                if (key[:2]=='A_' or key[:2]=='A_'):
                    self.var_entry.addItem(key)
            self.var_entry.setEnabled(True)
            self.Loss_SW_cb.setEnabled(False)
            self.Loss_SW_cb.setChecked(False)
        elif (self.scan_entry.currentText()=='Ramsey Phase Scan'):
            self.PCon.params.update_defs()
            self.disableAll(False)
            for key in sorted(self.PCon.params.defs.iterkeys()):
                if (key[:3]=='PH_'):
                    self.var_entry.addItem(key)
            self.scan_range_low_sb.setRange(-0.1,5)
            self.scan_range_high_sb.setRange(0,16384)
            self.scan_range_low_sb.setDecimals(0)
            self.scan_range_high_sb.setDecimals(0)

        else:
            print "Unknow scan type."

    def disableAll(self, aBool):
        self.button_cont.setDisabled(aBool)
        self.shuffle_cb.setDisabled(aBool)
        self.scan_range_low_sb.setDisabled(aBool)
        self.scan_range_high_sb.setDisabled(aBool)
        self.n_points_sb.setDisabled(aBool)
        self.var_entry.clear()
        self.var_entry.setDisabled(aBool)
        self.Loss_SW_cb.setDisabled(aBool)

    
    def init_scan(self, plotlength):
        self.plotdatalength = plotlength
        self.plotdata=numpy.zeros((self.plotdatalength,3),'Float32')

    def start_new_scan(self):
        self.new_scan = True
        self.run_scan()

    def run_scan(self):
        self.run_exp = True
        self.pause = False
        self.button_run.setDisabled(True)
        self.button_resume.setDisabled(True)
        self.button_pause.setDisabled(False)
        self.button_stop.setDisabled(False)
        self.button_cont.setDisabled(True)

        print "Starting a new scan: %i" %self.new_scan

        # Only update the log file when starting a new scan. Parameters can not
        # be changed if continuing a scan. CWC 09242012
        # Determine if a certain step in the pulse sequence Load_cool_exp_check
        # should be skipped CWC 09172012
        if self.new_scan:
            for key in self.controls:
                if not key[:3]=='SHU':
                    self.update_global_var(self.controls[key][1],
                            self.controls[key][0].value())
            for i in range(len(self.h_subscripts)):
                self.update_SHUTR(self.h_subscripts[i])

            self.PCon.params.save_params("Params")
            self.PCon.update_state()
            coltree_Qt.save_state("State", self.PCon.state)

            # Define data saving and config files save locations
            day = str(datetime.datetime.now().day)
            year = str(datetime.datetime.now().year)
            month = str(datetime.datetime.now().month)
            fnameBase = (str(self.scan_entry.currentText()))
            if (self.scan_entry.currentText()!='Continuous'):
                fnameBase += '__' + str(self.var_entry.currentText())
                
            self.timestamp = time.strftime('%H_%M_%S')
            #self.timestamp = time.strftime('%Y%m%d_%H%M%S')
            self.saveDataDir = (dirname + year + '/' + month + '/' + day + '/')
            self.configDir = (self.saveDataDir + 'config/' 
                    + self.timestamp + '_' + fnameBase + '/')
            if not os.path.isdir(self.saveDataDir):
                os.makedirs(self.saveDataDir)
            if not os.path.isdir(self.configDir):
                os.makedirs(self.configDir)
            
            shutil.copy2(str(self.ppfile), self.configDir)
            shutil.copy2('config.ddscon', self.configDir)
            
            
            
            self.filename = (self.saveDataDir + self.timestamp + '_' +
                    fnameBase) 
            self.plotPicFname = (self.configDir + fnameBase)
            
            fd = file(self.filename+'.txt', "a")


            # Get number of data points entered by user and use this
            # to set memory usage for the pp file
            # TODO: exit program if requested memory space is too large
            # TODO: ask James why he didn't use this.datastart
            #self.PCon.parameter_set('datastart', 4000-self.n_reps+1) #changed
            #CWC 09132012
            self.n_reps = self.rep_sb.value()
            self.partitionFpgaMemory()


            #Log the value of the parameters
            self.update_params()

            params_to_write = 'Pulse Programmer (pp) file:'+str(self.ppfile)+'\n'
            params_to_write+= 'Parameters: '
            for key in sorted(self.PCon.params.defs.iterkeys()):
                params_to_write+= (str(key) + ': ' +
                        str(self.PCon.params.defs[key]) + '; ')
            params_to_write+='\n'

            stateobj_to_write = 'Stateobj: '
            for key in sorted(self.PCon.stateobj.iterkeys()):
                if (key[:3] == 'DDS' or key[:3] == 'DAC' or key == 'SHUTR'):
                    stateobj_to_write += (key + ': ' +
                            str(self.PCon.stateobj[key][0].value()) + '; ')
            stateobj_to_write+='\n'

            self.PCon.data = numpy.zeros([self.n_reps,1], 'Int32')

            if (self.scan_entry.currentText()=='Continuous'):
                if self.new_scan:
                    self.text_to_write = 'Continuous scan.\n'
                    self.text_to_write+=params_to_write
                    self.text_to_write+=stateobj_to_write
                    fd.write(self.text_to_write)
                    fd.close()
                    self.init_scan(21)
                    self.plotdata[:,0]=numpy.linspace(0, self.plotdatalength-1,
                            self.plotdatalength)

                plot_thread = PlotThread(self, self.thread_count, self.qubit_D_cb.isChecked())
                self.threads.append(plot_thread)
                exp_thread = ContExpThread(self, plot_thread)
                self.threads.append(exp_thread)
                self.thread_count+=1


            elif (self.scan_entry.currentText()=='Frequency' or
                    self.scan_entry.currentText()=='Time' or
                    self.scan_entry.currentText()=='Voltage' or
                    self.scan_entry.currentText()=='DDS Amplitude' or
                    self.scan_entry.currentText()=='Ramsey Phase Scan' or
                    self.scan_entry.currentText()=='1038 Frequency'):

                #Only update the log file when starting a new scan. CWC 09242012
                if self.new_scan:
                    self.init_scan(self.n_points_sb.value())
                    self.text_to_write = (str(self.scan_entry.currentText()) +
                            ' scan.\n')
                    self.text_to_write+=params_to_write
                    self.text_to_write+=stateobj_to_write
                    scan_vals = numpy.linspace(self.scan_range_low_sb.value(),
                            self.scan_range_high_sb.value(),
                            self.n_points_sb.value())
                    if self.scan_entry.currentText()=='Ramsey Phase Scan':
                        scan_vals = map(lambda x: int(x), scan_vals)
                    else:
                        scan_vals = map(lambda x: float(round(10000*x)/10000),
                                scan_vals)
                    self.plotdata[:,0]=scan_vals
                    self.ind = {}
                    for n in range(len(scan_vals)):
                        self.ind[scan_vals[n]]=n


                    self.text_to_write+= ('Scan variable: ' +
                            str(self.var_entry.currentText()) + '\n')
                    self.text_to_write+= ('Range:' +
                            str(self.scan_range_low_sb.value()) + ' to ' +
                            str(self.scan_range_high_sb.value()) + '\n')
                    self.text_to_write+= ('Number of points: ' +
                            str(self.n_points_sb.value()) +'\n')
                    self.text_to_write+= ('Rep. per point: '+
                            str(self.rep_sb.value()) +'\n')
                    self.text_to_write+= ('Plotting population:'+str(self.qubit_D_cb.isChecked())+'\n')
                    self.text_to_write+= 'Scan var. val.'+'\t'+'Meas. Avg.'+'\t'
                    for n in range(self.rep_sb.value()):
                        self.text_to_write += 'Rep. #'+str(n)+'\t'
                    self.text_to_write +='\n'
                    fd.write(self.text_to_write)
                    fd.close()

                if (self.shuffle_cb.isChecked() == True):
                    # Shuffle the list of scanned variable values each time a
                    # scan is started, whether continuing or not. CWC 09242012
                    numpy.random.shuffle(scan_vals)

                plot_thread = PlotThread(self, self.thread_count, self.qubit_D_cb.isChecked())
                self.threads.append(plot_thread)

                # Changed the receiver for the update event from self (GUI) to
                # plot_thread
                exp_thread = ScanExpThread(self, plot_thread, scan_vals)
                self.threads.append(exp_thread)
                self.thread_count+=1

            else:
                print "Unknow scan type."
        print "Thread count: %i" %self.thread_count
        self.threads[2*(self.thread_count-1)].start()
        self.threads[2*(self.thread_count-1)+1].start()

    def set_stage_Disabled(self):
        widget = self.sender()
        TF = widget.isChecked()
        if TF:
            SW = 1
        else:
            SW = 0

        if (widget == self.Load_SW_cb):
            h_label = 'load'
            self.PCon.parameter_set('LOAD_SWITCH', SW)
        elif (widget == self.Cool_SW_cb):
            h_label = 'cool'
            self.PCon.parameter_set('COOL_SWITCH', SW)
        elif (widget == self.Wait2_SW_cb):
            h_label = 'wait2'
            self.PCon.parameter_set('WAIT2_SWITCH', SW)
        elif (widget == self.OP_SW_cb):
            h_label = 'op'
            self.PCon.parameter_set('OP_SWITCH', SW)
        elif (widget == self.Wait3_SW_cb):
            h_label = 'wait3'
            self.PCon.parameter_set('WAIT3_SWITCH', SW)
        elif (widget == self.Exp_SW_cb):
            h_label = 'exp'
            self.PCon.parameter_set('EXP_SWITCH', SW)
        elif (widget == self.Wait4_SW_cb):
            h_label = 'wait4'
            self.PCon.parameter_set('WAIT4_SWITCH', SW)
        elif (widget == self.Check_SW_cb):
            h_label = 'check'
            self.PCon.parameter_set('CHECK_SWITCH', SW)
        elif (widget == self.Loss_SW_cb):
            h_label = 'loss'
            self.PCon.parameter_set('LOSS_SWITCH', SW)

        if h_label != 'loss':
            for i in range(len(self.v_sb_subscripts)):
                self.controls[self.v_sb_subscripts[i]+h_label][0].setDisabled(not TF)
            for i in range(len(self.v_tb_index)):
                self.controls[self.v_tb_index[i]+h_label][0].setDisabled(not TF)

        disable_additional_col = 0
        if h_label == 'load':
            h_label = 'wait1'
            disable_additional_col += 1
        elif h_label == 'check':
            h_label = 'wait6'
            disable_additional_col += 1

        if disable_additional_col:
            for i in range(len(self.v_sb_subscripts)):
                self.controls[self.v_sb_subscripts[i]+h_label][0].setDisabled(not TF)
            for i in range(len(self.v_tb_index)):
                self.controls[self.v_tb_index[i]+h_label][0].setDisabled(not TF)



    def pause_scan(self):
        self.pause = True
        self.button_run.setDisabled(False)
        self.button_resume.setDisabled(False)
        self.button_pause.setDisabled(True)
        self.button_stop.setDisabled(False)
        self.button_cont.setDisabled(True)

    def resume_scan(self):
        self.pause = False
        self.button_run.setDisabled(True)
        self.button_resume.setDisabled(True)
        self.button_pause.setDisabled(False)
        self.button_stop.setDisabled(False)
        self.button_cont.setDisabled(True)

    def stop_scan(self):
        self.run_exp = False
        self.pause = False
        self.button_run.setDisabled(False)
        self.button_resume.setDisabled(True)
        self.button_pause.setDisabled(True)
        self.button_stop.setDisabled(True)
        self.button_cont.setDisabled(False)
        self.PCon.user_stop() #Added for proper stop CWC 09172012

    def continue_scan(self):
        self.new_scan = False
        self.run_scan()

    def update_plot_save_data(self, scan_index, new_mean, new_data):
        if (self.scan_entry.currentText()=='Continuous'):
            self.plotdata[0:self.plotdatalength-1,1] = self.plotdata[
                    1:self.plotdatalength,1]
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
        self.trace1.set_ylim(ymin-0.1*(ymax-ymin)-0.01,
                ymax+0.1*(ymax-ymin)+0.01)

        self.trace2.clear()
        #self.trace2.hist(self.PCon.data[:,1],arange(0,self.hist_max+1), normed = 1)
        self.update_hist(new_data)
        self.plot.draw()

        if (self.scan_entry.currentText()=='Continuous'):
            self.text_to_write = str(self.plotdata[scan_index,1])+'\t'
        else:
            self.text_to_write = str(self.plotdata[scan_index,0]) + '\t' + \
                    str(self.plotdata[scan_index,1])+'\t'
        for n in range(self.rep_sb.value()):
            self.text_to_write += str(new_data[n])+'\t'
        self.text_to_write += '\n'
        fd = file(self.filename+'.txt', "a")
        fd.seek(0,2)
        fd.write(self.text_to_write)
        fd.close()


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
        
    def OpenPopUpWindow(self):
        self.w = MyPopup()
        self.w.setGeometry(QRect(100, 100, 400, 200))
        self.w.show()


class ExpThread(QtCore.QThread):
    """ Base class for experiment threads."""
    def __init__(self,GUI,receiver):
        super(ExpThread, self).__init__()
        self.GUI = GUI
        self.n_reps = self.GUI.n_reps
        self.reuseDataStart = self.GUI.reuseDataStart
        self.reuseBinAddr = self.GUI.reuseBinAddr
        self.receiver = receiver
        self.stopped = 0
        self.t1 = time.time()
        self.connect( self, QtCore.SIGNAL("Done_one_point"),
                receiver.update_plot_save_data )
        self.connect( self, QtCore.SIGNAL("Done_scanning"), receiver.stop )

    def __del__(self):
        self.stopped = 1
        self.wait()

    def getAtomReuse(self):
        # Return an array containing total atom reuse per single loading event
        numBins = self.GUI.PCon.read_memory(self.reuseBinAddr,1)
        atomReuseArray = self.GUI.PCon.read_memory(self.reuseDataStart,
                self.n_reps)
        atomReuseArray = numpy.resize(atomReuseArray,numBins)

        return atomReuseArray

    def run():
        pass

    def stop(self):
        self.stopped = 1

class ContExpThread(ExpThread):
    """ Class for contiuous non-scanned experiment thread. This class inherits
    QtCore.QThread through ExpThread."""
    def __init__(self, GUI, receiver):
        super(ContExpThread, self).__init__(GUI,receiver)

    def run(self):
        self.stopped = 0
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

                # Print atom reuse array
                atomReuseArray = self.getAtomReuse()
                print "mean reuse number %.1f" %numpy.mean(atomReuseArray)
                print atomReuseArray

        self.GUI.PCon.restore_state(self.GUI.PCon.state)
        self.emit(QtCore.SIGNAL("Done_scanning"))

class ScanExpThread(ExpThread):
    """ Class for scanning a parameter type experiment thread. This class inherits
    QtCore.QThread through ExpThread."""
    def __init__(self, GUI, receiver, scan_vals):
        super(ScanExpThread, self).__init__(GUI,receiver)
        self.scan_vals = scan_vals
        temp = self.GUI.PCon.parameter_read( str(
            self.GUI.var_entry.currentText())).split()
        self.init_val = float(temp[1])
        if (self.GUI.scan_entry.currentText()=='1038 Frequency'):
            """insantiate visa object for frequency synthesizer"""
            try:
                self.visa_Agilent_E4421B = visa.instrument ("GPIB::19")
                print self.visa_Agilent_E4421B.ask("*IDN?")
            except:
                print "failure: GPIB::19, Agilent freq synthesizer.  check address"

    def run(self):
        self.stopped = 0
        self.GUI.PCon.update_state()
        coltree_Qt.save_state("State", self.GUI.PCon.state) #saves all initial values in value/bool table
        n = 0
        while (self.stopped == 0 and self.GUI.run_exp ==True and n<self.GUI.n_points_sb.value()):
            while (self.stopped == 0 and self.GUI.pause == True):
                time.sleep(0.1)
            current_scan_val = self.scan_vals[n] #get scan value from array

            if (self.GUI.scan_entry.currentText()=='1038 Frequency'):
                """ update synthesizer with new frequency and trigger unlock ttl on laser controler"""
                #shutrState = self.GUI.PCon.stateobj["SHUTR"][0].value()
                #self.GUI.PCon.stateobj["SHUTR"][0].setValue(shutrState+512)
                #time.sleep(.0)
                self.visa_Agilent_E4421B.write("TRIG:OUTP:POL NEG")
                self.visa_Agilent_E4421B.write("FREQ " + str(current_scan_val)+" GHz")
                self.visa_Agilent_E4421B.write("TRIG:OUTP:POL POS")
                #self.GUI.PCon.stateobj["SHUTR"][0].setValue(shutrState)
            else:
                self.GUI.PCon.parameter_set(self.GUI.var_entry.currentText(), current_scan_val) #set the scanned var to value

            self.GUI.PCon.pp_run()  #pp_run uploads and exec.;  pp_run_2 only exec what is already in memory
            t3=time.time()
            readoutOK = self.GUI.PCon.update_count()  # .update_count is method for read memory
            t4=time.time()

            #print "pp readout time %3f sec" %(t4-t3)
            if (readoutOK and not self.GUI.PCon.pp_is_running()):
                self.emit(QtCore.SIGNAL("Done_one_point"),
                        self.GUI.ind[current_scan_val],
                        numpy.mean(self.GUI.PCon.data[:,1]),
                        self.GUI.PCon.data[:,1])  #update_cout() retrieved data and stores in PCon.data
##                print self.GUI.ind[current_scan_val]
##                print current_scan_val
                if (time.time()-self.t1) < 0.05:
                    time.sleep(0.03)
                t2 = time.time()
                print 'ExpThread cycle time %.6f seconds' %(t2-self.t1)
                self.t1 = t2

                # Calculate and print out atom reuse
                atomReuseArray = self.getAtomReuse()
                print "mean reuse number %.1f" %numpy.mean(atomReuseArray)
                print atomReuseArray

            n+=1
            self.GUI.n_index.setText(str(n))
            self.GUI.scanVal.setText(str(current_scan_val))
        self.GUI.PCon.restore_state(self.GUI.PCon.state)  #finished all points, return to back to state before run
        self.emit(QtCore.SIGNAL("Done_scanning"))
        self.GUI.PCon.parameter_set(str(self.GUI.var_entry.currentText()),
                self.init_val)  #sets parameters in "driver"

# TODO: Delete below code if the new class sturcture works fine (base class
# ExpThread inherited by ScanExpThread and ContExpThread).
#class ExpThread(QtCore.QThread):
#    def __init__(self, GUI, scan_vals, receiver,):
#        super(ExpThread, self).__init__()
#
#        self.GUI = GUI
#        self.n_reps = self.GUI.n_reps
#        self.reuseDataStart = self.GUI.reuseDataStart
#        self.reuseBinAddr = self.GUI.reuseBinAddr
#        self.receiver = receiver
#        self.scan_vals = scan_vals
#        temp = self.GUI.PCon.parameter_read( str(
#            self.GUI.var_entry.currentText())).split()
#        self.init_val = float(temp[1])
#        self.stopped = 0
#        self.t1 = time.time()
#        self.connect( self, QtCore.SIGNAL("Done_one_point"),
#                receiver.update_plot_save_data )
#        self.connect( self, QtCore.SIGNAL("Done_scanning"), receiver.stop )
#
#    def getAtomReuse():
#        # Return an array containing total atom reuse per single loading event
#        numBins = self.GUI.PCon.read_memory(self.reuseBinAddr,1)
#        atomReuseArray = self.GUI.PCon.read_memory(self.reuseDataStart,
#                self.n_reps)
#        atomReuseArray = numpy.resize(atomReuseArray,numBins)
#
#        return atomReuseArray
#
#    def run(self):
#        self.stopped = 0
#        self.GUI.PCon.update_state()
#        coltree_Qt.save_state("State", self.GUI.PCon.state)
#        n = 0
#        while (self.stopped == 0 and self.GUI.run_exp ==True and n<self.GUI.n_points_sb.value()):
#            while (self.stopped == 0 and self.GUI.pause == True):
#                time.sleep(0.1)
#            current_scan_val = self.scan_vals[n]
#
#            self.GUI.PCon.parameter_set(self.GUI.var_entry.currentText(), current_scan_val)
#
#            self.GUI.PCon.pp_run()
#            t3=time.time()
#            readoutOK = self.GUI.PCon.update_count()
#            t4=time.time()
#
#            #print "pp readout time %3f sec" %(t4-t3)
#            if (readoutOK and not self.GUI.PCon.pp_is_running()):
#                self.emit(QtCore.SIGNAL("Done_one_point"), self.GUI.ind[current_scan_val], numpy.mean(self.GUI.PCon.data[:,1]), self.GUI.PCon.data[:,1])
###                print self.GUI.ind[current_scan_val]
###                print current_scan_val
#                if (time.time()-self.t1) < 0.05:
#                    time.sleep(0.03)
#                t2 = time.time()
#                print 'ExpThread cycle time %.6f seconds' %(t2-self.t1)
#                self.t1 = t2
#
#                # Calculate and print out atom reuse
#                numBins = self.GUI.PCon.read_memory(self.reuseBinAddr,1)
#                atomReuseArray = self.GUI.PCon.read_memory(self.reuseDataStart,
#                        self.n_reps)
#                atomReuseArray = numpy.resize(atomReuseArray,numBins)
#                print "mean reuse number %.1f" %numpy.mean(atomReuseArray)
#                print atomReuseArray
#                #print numpy.std(atomReuseArray)
#
#            n+=1
#            self.GUI.n_index.setText(str(n))
#        self.GUI.PCon.restore_state(self.GUI.PCon.state)
#        #self.GUI.stop_scan()
#        self.emit(QtCore.SIGNAL("Done_scanning"))
#        #self.GUI.fit_result()
#        self.GUI.PCon.parameter_set(str(self.GUI.var_entry.currentText()), self.init_val)
#
#    def stop(self):
#        self.stopped = 1
#
#    def __del__(self):
#        self.stopped = 1
#        self.wait()
#
#class ContExpThread(QtCore.QThread):
#    def __init__(self, GUI, receiver):
#        super(ContExpThread, self).__init__()
#        self.GUI = GUI
#        self.receiver = receiver
#        self.stopped = 0
#        self.t1 = time.time()
#        self.connect( self, QtCore.SIGNAL("Done_one_point"), self.receiver.update_plot_save_data )
#        self.connect( self, QtCore.SIGNAL("Done_scanning"), receiver.stop )
#
#    def run(self):
#        self.stopped = 0
#        self.GUI.PCon.update_state()
#        coltree_Qt.save_state("State", self.GUI.PCon.state)
#        while (self.stopped == 0 and self.GUI.run_exp ==True):
#            while (self.stopped == 0 and self.GUI.pause == True):
#                time.sleep(0.1)
#            self.GUI.PCon.pp_run_2()
#            readoutOK = self.GUI.PCon.update_count()
#            if (readoutOK and not self.GUI.PCon.pp_is_running()):
#                #print(numpy.mean(self.GUI.PCon.data[:,1]))
#                self.emit(QtCore.SIGNAL("Done_one_point"), 0, numpy.mean(self.GUI.PCon.data[:,1]), self.GUI.PCon.data[:,1])
#                if (time.time()-self.t1) < 0.05:
#                    time.sleep(0.03)
#                t2 = time.time()
#                print 'ContExpThread cycle time %.6f seconds' %(t2-self.t1)
#                self.t1 = t2
#
#                # TODO: make these memory reference relative
#                numBins = self.GUI.PCon.read_memory(self.reuseBinAddr,1)
#                atomReuseArray = self.GUI.PCon.read_memory(self.reuseDataStart,
#                        self.n_reps)
#                atomReuseArray = numpy.resize(atomReuseArray,numBins)
#                print "mean reuse number %.1f" %numpy.mean(atomReuseArray)
#                print atomReuseArray
#                #print numpy.std(atomReuseArray)
#
#        self.GUI.PCon.restore_state(self.GUI.PCon.state)
#        self.emit(QtCore.SIGNAL("Done_scanning"))
#
##Need to return to the original configuration after scan. CWC 09052012
#
#    def stop(self):
#        self.stopped = 1
#
#    def __del__(self):
#        self.stopped = 1
#        self.wait()

class PlotThread(QtCore.QThread):
    def __init__(self, GUI, index, qubit_D):
        super(PlotThread, self).__init__()
        #Pop up two new windows for plot and hist with control bars. See http://eli.thegreenplace.net/files/prog_code/qt_mpl_bars.py.txt CWC 09132012
        self.frame1 = PlotWidget(self)
        self.frame2 = QtGui.QWidget()
        self.GUI = GUI
        self.index = index
        self.qubit_D = qubit_D
        self.plotPicFname = self.GUI.plotPicFname
        self.filename = self.GUI.filename
        self.stopped = 0
        self.t1 = time.time()

        self.fig1 = Figure((5.0, 4.0))
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setParent(self.frame1)
        self.trace1 = self.fig1.add_subplot(111)
        self.trace1.set_title(self.plotPicFname)
        self.yerr = numpy.zeros(self.GUI.n_points_sb.value())
        if self.qubit_D:
            self.trace1.errorbar(self.GUI.plotdata[:,0],self.GUI.plotdata[:,1],xerr=0,yerr=0,fmt='ro-')
        else:
            self.line1, = self.trace1.plot(self.GUI.plotdata[:,0],self.GUI.plotdata[:,1],'ro-')
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
        self.trace2.set_title(self.plotPicFname+'_hist')

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
        new_prob = numpy.mean(map(lambda x: int(x>float(self.GUI.PCon.params.defs['CHECKTHOLD'])), new_data))
        if (self.GUI.scan_entry.currentText()=='Continuous'):
            self.GUI.plotdata[0:self.GUI.plotdatalength-1,1] = self.GUI.plotdata[1:self.GUI.plotdatalength,1]
            if self.qubit_D:
                self.GUI.plotdata[self.GUI.plotdatalength-1,1] = new_prob
                self.trace1.clear()
                self.trace1.set_title(self.plotPicFname)
                err = numpy.sqrt(self.GUI.plotdata[:,1]*(1-self.GUI.plotdata[:,1])/self.GUI.n_reps)
                self.trace1.errorbar(self.GUI.plotdata[:,0],self.GUI.plotdata[:,1],xerr = 0,yerr = err,fmt='ro-')
            else:
                self.GUI.plotdata[self.GUI.plotdatalength-1,1] = new_mean
                self.line1.set_ydata(self.GUI.plotdata[:,1])
        else:# (self.GUI.scan_entry.currentText()=='Frequency' ):
            if self.qubit_D:
                self.yerr[scan_index] = numpy.sqrt(((self.yerr[scan_index])**2*self.GUI.plotdata[scan_index,2]+new_prob*(1-new_prob))/(self.GUI.plotdata[scan_index,2]+self.GUI.n_reps))
                self.GUI.plotdata[scan_index,1] = (self.GUI.n_reps*new_prob+self.GUI.plotdata[scan_index,1]*self.GUI.plotdata[scan_index,2])/(self.GUI.n_reps+self.GUI.plotdata[scan_index,2])
                self.trace1.clear()
                self.trace1.set_title(self.plotPicFname)
                self.trace1.errorbar(self.GUI.plotdata[:,0],self.GUI.plotdata[:,1],xerr=0,yerr=self.yerr,fmt='ro-')
            else:
                self.GUI.plotdata[scan_index,1] = (self.GUI.n_reps*new_mean+self.GUI.plotdata[scan_index,1]*self.GUI.plotdata[scan_index,2])/(self.GUI.n_reps+self.GUI.plotdata[scan_index,2])
                self.line1.set_ydata(self.GUI.plotdata[:,1])
            self.GUI.plotdata[scan_index,2] = self.GUI.plotdata[scan_index,2] + self.GUI.n_reps


        #print "%d, %d" %(len(self.GUIplotdata[:,0]),len(self.GUIplotdata[:,1]))
        ymax = numpy.max(self.GUI.plotdata[:,1])
        ymin = numpy.min(self.GUI.plotdata[:,1])
        self.trace1.set_ylim(ymin-0.1*(ymax-ymin)-0.01, ymax+0.1*(ymax-ymin)+0.01)

        self.trace2.clear()
        #self.GUItrace2.hist(self.GUIPCon.data[:,1],arange(0,self.GUIhist_max+1), normed = 1)
        self.update_hist(new_data)
        self.trace2.set_title(self.plotPicFname+'_hist')
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
        if self.index == self.GUI.thread_count-1:
            self.GUI.stop_scan()
        self.fig1.savefig(self.plotPicFname+'.png')
        pp = matplotlib.backends.backend_pdf.PdfPages(self.plotPicFname+'.pdf')
        pp.savefig(self.fig1)
        #self.fig1.savefig(pp, format='pdf')
        pp.close()
        print 'Saving figure...'


    def __del__(self):
        self.stopped = 1
        if self.index == self.GUI.thread_count-1:
            self.GUI.stop_scan()
        self.fig1.savefig(self.plotPicFname+'.png')
        pp = matplotlib.backends.backend_pdf.PdfPages(self.plotPicFname+'.pdf')
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

class LabeledSpinBox(QtGui.QWidget):
    def __init__(self, label, callback):
        super(LabeledSpinBox, self).__init__()
        self.box = QtGui.QVBoxLayout()
        self.sb = QtGui.QDoubleSpinBox()
        self.box.addWidget(self.sb)
        self.label = label
        self.sb.valueChanged.connect(self.valChanged)
        QtCore.QObject.connect(self,QtCore.SIGNAL("changed"),callback)

    def valChanged(self):
        self.emit(QtCore.SIGNAL("changed"),self.label, self.sb.value())

class LabeledPushButton(QtGui.QWidget):
    def __init__(self, vlabel, hlabel, callback):
        super(LabeledPushButton, self).__init__()
        self.box = QtGui.QVBoxLayout()
        self.tb = QtGui.QPushButton()
        self.tb.setCheckable(True)
        self.box.addWidget(self.tb)
        self.vlabel = vlabel
        self.hlabel = hlabel
        self.tb.toggled.connect(self.tb_toggled) #This signal is never invoked! CWC09252012
        QtCore.QObject.connect(self,QtCore.SIGNAL("tb_toggled"),callback)

    def tb_toggled(self):
        print '%s toggled.' %(self.vlabel+self.hlabel)
        self.emit(QtCore.SIGNAL("tb_toggled"),self.hlabel)

class MyPopup(QtGui.QWidget):
    def __init__(self):
        QWidget.__init__(self)

    def paintEvent(self, e):
        dc = QPainter(self)
        dc.drawLine(0, 0, 100, 100)
        dc.drawLine(100, 0, 0, 100)
