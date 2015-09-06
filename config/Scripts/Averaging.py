#Averaging.py created 2015-08-06 13:18:27.682000
#
#Reimplementation of averaging functionality of repeat scan
#Each time a scan is completed, the new data associated with some specified
#evaluation is averaged into an average trace. The average trace is averaged
#into the existing average, and plotted to "Average Plot." This continues until
#the script is stopped.

scanName = 'myScan1'
traceName = scanName+'Average'
plotName = 'Average Plot'
addPlot(plotName) #add a plot to send the average to. This is unnecessary if using an existing plot.
createTrace(traceName, plotName) #create a trace associated with the average
setScan(scanName)
setEvaluation('myEval1')
setAnalysis('myAnalysis1')

num = 1 #The loop counter
myEvalName = 'niceMean' #The name of the evaluation dataset to average
while True: #run until stopped. Could also change this to run for a fixed number of cycles.
    startScan()
    data = getAllData()[myEvalName] #Returns all data associated with "myEvalName" once scan finishes.
    xdata = data[0]
    ydata = data[1]
    if num == 1:
        averagedYdata = ydata
        averagedXdata = xdata
    else:
        averagedYdata = ((num-1)*averagedYdata + ydata)/float(num)
    plotList(averagedXdata, averagedYdata, traceName) #plot the data
    if scriptIsStopped():#This conditional must be here for any infinite loop, otherwise it cannot be stopped!
        break