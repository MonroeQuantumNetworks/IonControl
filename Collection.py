#-------------------------------------------------------------------------------
# Name:        Collecection
# Purpose:
#
# Author:      craclar
#
# Created:     12/07/2012
# Copyright:   (c) craclar 2012
#-------------------------------------------------------------------------------
import numpy, math, socket, os, DDSdriver, time

dirname = 'C:/Users/craclar/Documents/Research/Optics trap/July-26-20012/'
timestamp = time.strftime('_%m_%d_%Y_%H_%M_%S')
filename =dirname +'Ion-MeasTime-500ns-Shelftime-250ns'+ timestamp + '.txt'

if not os.path.isdir(dirname):
    os.mkdir(dirname)


DDS.parameter_set('SHUTR',3)                   #Set the Shutter Command to ensure the Doppler beams are on

thresh=15                         #Ion brightnes threshold value
totalScans=2000                       #number of iteration to loop over the pp file
data=numpy.array([],'Int32')                 #empty array to store the data in
iteration=0                          #variable to determine how offten to check and recool the ion
lost=0                               #Dumby variable to kill program
data_start=3500
check_start=3995
Check_time=1000


DDS.parameter_set('datastart',data_start) #set the datastart value to the tree of variable
DDS.parameter_set('us_MeasTime',Check_time) #set the us_MeasTime value to the tree of variable
#print data_start
DDS.pp_setprog('C:\Users\craclar\Desktop\FPGA-DDSProgram\prog\CE.pp') # Load and sets teh .pp file at the given location
start_time=time.time()
self.axis1.clear()
self.axis2.clear()

for j in range(int(totalScans)):
    DDS.pp_run2()                #Runs the above .pp file
    counts=DDS.read_memory()         #Extracts the data from the memory
    iteration=iteration+1
    data=numpy.append(data,counts)
    if (iteration>=400):             # compars the value of interation to check for ion and recool
        DDS.parameter_set('datastart',check_start)  #changes the value of datastart to perform quick check for ion
        DDS.pp_setprog('C:\Users\craclar\Desktop\FPGA-DDSProgram\prog\PMTtest.pp')  # Open different pp file recool and check for ion
        DDS.pp_run2()            # runn the above pp file
        IonBright=DDS.net_lastavg() #return the lastavg of the date
        print 'Ion bright', IonBright

        DDS.parameter_set('datastart', data_start)  #Set the datastart value back to the origian value

        if IonBright<thresh:                          #compare the ion bright vale to the threshold vlaue
            print "ion lost"
            lost=-1

        DDS.pp_setprog('C:\Users\craclar\Documents\Research\FPGA07122012\prog\CE.pp')
        iteration=0                  #reset the iteration value to zero to not check to offten

    if lost<0:                       #break point if the ion is lost
        break


    self.axis1.plot(j,numpy.mean(data),'r')
    self.axis1.set_ylabel('CE', color='r')
    self.axis1.set_xlabel('interation')
    self.plot.draw()
    #print counts

time_now=time.time()
print 'time to run =', time_now-start_time

numpy.savetxt(filename,data,fmt='%i')          #saves data to the file

CE=numpy.mean(data)

print numpy.sum(data)
print len(data)
print CE
