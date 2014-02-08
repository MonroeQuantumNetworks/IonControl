# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 10:18:19 2013

@author: wolverine
"""
import csv

import matplotlib.pyplot as plt
import numpy as np


goodGateSequences09= ['003', '005', '006', '006', '007', '008', '009', '010', '011', '012'] #006 is doubled because that one had 100 expts/pt
goodGateSequences10= ['002', '004', '005', '006', '007', '008', '010', '011', '012', '013']
goodGateSequences11= ['002', '003', '004', '005', '006', '007', '008', '009', '010', '011',
                 '012', '013', '014', '015', '016', '017', '019', '020']

goodTestGateSequences09= ['001', '004', '005', '006', '007']
goodTestGateSequences10= ['002', '003', '004', '005', '006']
goodTestGateSequences11= ['002', '003', '005', '007', '009',
                     '010', '011','012', '014']

filenames09 = ['C:\\Users\\Public\\Documents\\experiments\\QGA\\2013\\2013_10\\2013_10_09\\GateSequence_{0}.txt'.format(gateset)
        for gateset in goodGateSequences09]

filenames10 = ['C:\\Users\\Public\\Documents\\experiments\\QGA\\2013\\2013_10\\2013_10_10\\GateSequence_{0}.txt'.format(gateset)
        for gateset in goodGateSequences10]

filenames11 = ['C:\\Users\\Public\\Documents\\experiments\\QGA\\2013\\2013_10\\2013_10_11\\GateSequence_{0}.txt'.format(gateset)
        for gateset in goodGateSequences11]

filenamesTest09 = ['C:\\Users\\Public\\Documents\\experiments\\QGA\\2013\\2013_10\\2013_10_09\\GateTestSet_{0}.txt'.format(gateset)
        for gateset in goodTestGateSequences09]

filenamesTest10 = ['C:\\Users\\Public\\Documents\\experiments\\QGA\\2013\\2013_10\\2013_10_10\\GateTestSet_{0}.txt'.format(gateset)
        for gateset in goodTestGateSequences10]

filenamesTest11 = ['C:\\Users\\Public\\Documents\\experiments\\QGA\\2013\\2013_10\\2013_10_11\\GateTestSet_{0}.txt'.format(gateset)
        for gateset in goodTestGateSequences11]


filenames = filenames09 + filenames10 + filenames11
filenamesTest = filenamesTest09 + filenamesTest10 + filenamesTest11

ydata = np.zeros(1066)
ydataTest = np.zeros(2020)
for filename in filenames:
    with open(filename, 'r') as datafile:
        raw_data = csv.reader(datafile, delimiter = '\t')
        data = np.array([[float(row[0]), float(row[1])] for row in raw_data if row[0][0] != '#'])
        data = data[data[:,0].argsort()]
        ydata += data[:,1:][:,0]

for filenameTest in filenamesTest:
    with open(filenameTest, 'r') as datafile:
        raw_data = csv.reader(datafile, delimiter = '\t')
        data = np.array([[float(row[0]), float(row[1])] for row in raw_data if row[0][0] != '#'])
        data = data[data[:,0].argsort()]
        ydataTest += data[:,1:][:,0]

ydata /= len(filenames)
ydataTest /= len(filenamesTest)

xdata = np.array(range(1066))
xdataTest = np.array(range(2020))

plt.subplot(211)
plt.axis([0,1066,0,1.0])
plt.plot(xdata,ydata,'ro')

plt.subplot(212)
plt.axis([0,2025,0,1.0])
plt.plot(xdataTest,ydataTest,'bo')

plt.show()
print "Number of training experiments per point: {0}".format(len(filenames)*50)
print "Number of testing experiments per point: {0}".format(len(filenamesTest)*50)