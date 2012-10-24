import os, sys 
from PyQt4 import QtGui
from PyQt4 import QtCore

class MainWindow(QtGui.QWidget): 
    def __init__(self): 
        super(MainWindow, self).__init__()

        # Initialize variables
        self.ppfile = './prog/'+ 'APDcounts.pp'

         
        self.mainvbox = QtGui.QVBoxLayout() 
        self.init_main_win()
        self.init_menu()
        #p2_vertical = QtGui.QHBoxLayout() 
        #p1_vertical.addLayout(p2_vertical)
        self.init_exp_con_tab()
        self.setLayout(self.mainvbox) 

     
    def center(self): 
        screen = QtGui.QDesktopWidget().screenGeometry() 
        size = self.geometry() 
        self.move((screen.width()-size.width())/2,
                (screen.height()-size.height())/2) 

    def init_exp_con_tab(self):
        # ExpConGUI_Qt parameters
        self.scan_types =['Continuous', 'Frequency', 'Time', 'Voltage',
                'DDS Amplitude']
        #Define the TTL channels
        self.SHUTR_CHAN = { 'SHUTR_MOT_':       0, 
                            'SHUTR_Repump_':    1,
                            'SHUTR_uWave_':     7,
                            'SHUTR_D1_':        5,
                            'SHUTR_Dipole_':    3,
                            'SHUTR_MOT_Servo_': 4,
                            'SHUTR_MOTradial_': 2} 

        expTabGui = QtGui.QGridLayout(self.expTab)
        #button1 = QtGui.QPushButton("button1") 
        #expTabGui.addWidget(button1)

        #vbox = QtGui.QVBoxLayout()
        #hbox = QtGui.QHBoxLayout()
        #hbox1 = QtGui.QHBoxLayout(self.expTab)
        #hbox2 = QtGui.QHBoxLayout()
        #hbox3 = QtGui.QHBoxLayout()
        #hbox4 = QtGui.QHBoxLayout()
        #hbox5 = QtGui.QHBoxLayout()
        #hbox6 = QtGui.QHBoxLayout()

        self.setWindowTitle("Blah")

        # ppfile entry
        Filename_label=QtGui.QLabel("Pulse Sequence File")
        expTabGui.addWidget(Filename_label,0,0)
        self.Filename_entry=QtGui.QLineEdit()
        self.Filename_entry.setText(self.ppfile)
        expTabGui.addWidget(self.Filename_entry,0,1)

        # Scan type spin button
        scan_label = QtGui.QLabel("Scan type")
        expTabGui.addWidget(scan_label,1,0)
        self.scan_entry = QtGui.QComboBox()
        for n in range(len(self.scan_types)):
            self.scan_entry.addItem(self.scan_types[n])
        expTabGui.addWidget(self.scan_entry,1,1)
        #TODO: implement update scan type
        #self.scan_entry.currentIndexChanged.connect(self.update_scan_type)

        # Scan variable
        #TODO: get scan variables from config file
        var_label = QtGui.QLabel("Scan variable")
        expTabGui.addWidget(var_label,1,2)
        self.var_entry = QtGui.QComboBox()
        #self.PCon.params.update_defs()
        #for key in self.PCon.params.defs:
        #    self.var_entry.addItem(key)
        self.var_entry.setDisabled(True)
        expTabGui.addWidget(self.var_entry,1,3)
        #self.var_entry.currentIndexChanged.connect(self.update_var)

    def init_main_win(self):
        # Window geometry and asthetics 
        self.setGeometry(0,0, 500,650) 
        self.setWindowTitle("Debreate") 
        self.setWindowIcon(QtGui.QIcon("icon.png")) 
        self.resize(500,650) 
        self.setMinimumSize(500,650) 
        self.center() 

        # Setup tabs buttons for main window
        tab_widget = QtGui.QTabWidget() 
        self.expTab = QtGui.QWidget() 
        self.tab2 = QtGui.QWidget() 
        tab_widget.addTab(self.expTab, "Exp. Control") 
        tab_widget.addTab(self.tab2, "Plots") 
        self.mainvbox.addWidget(tab_widget) 

    def init_menu(self):
        # --- Menu --- # 
        open = QtGui.QAction("Exit", self) 
        save = QtGui.QAction("Save", self) 
        build = QtGui.QAction("Build", self) 
        exit = QtGui.QAction("Quit", self) 
         
        menu_bar = QtGui.QMenuBar() 
        file = menu_bar.addMenu("&File") 
        help = menu_bar.addMenu("&Help") 
         
        file.addAction(open) 
        file.addAction(save) 
        file.addAction(build) 
        file.addAction(exit) 
        self.mainvbox.addWidget(menu_bar) 



app = QtGui.QApplication(sys.argv) 
frame = MainWindow() 
frame.show()
sys.exit(app.exec_())  
