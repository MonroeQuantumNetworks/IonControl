'''
Created on Aug 30, 2014

@author: pmaunz
'''

from modules.RunningStat import RunningStatHistogram, RunningStat
from modules.magnitude import mg

class DynamicDecimation:
    name = 'Dynamic'
    def __init__(self):
        self.stat = RunningStatHistogram()
        self.timeStat = RunningStat()
        self.lastRecordingTime = 0
        self.MaxRecordingInterval = mg(300,'s')
        
    def decimate(self, takentime, value):
        self.stat.add( value )
        self.timeStat.add( takentime )
        if takentime-self.lastRecordingTime > self.MaxRecordingInterval.toval('s') or len(self.stat.histogram)>2:
            self.lastRecordingTime = takentime
            meanVal, minVal, maxVal = self.stat.mean, self.stat.min, self.stat.max
            timeVal = self.timeStat.mean 
            self.stat.clear()
            self.timeStat.clear()
            return True, (timeVal, meanVal, minVal, maxVal)
        return False, None
    
    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict['stat']
        del odict['timeStat']
        return odict
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.stat = RunningStatHistogram()
        self.timeStat = RunningStat()
        
    def paramDef(self):
        return [{'name': 'max gap', 'type': 'magnitude', 'object': self, 'field': 'MaxRecordingInterval', 'value': self.MaxRecordingInterval, 'tip': "max time without recording"}]
        

class Average:
    name = "Average"
    def __init__(self):
        self.stat = RunningStat()
        self.timeStat = RunningStat()
        self.lastRecordingTime = 0
        self.averagePoints = 10
        self.errorBars = 'Min Max'
        
    def decimate(self, takentime, value):
        self.stat.add( value )
        self.timeStat.add( takentime )
        if self.stat.count>=self.averagePoints:
            self.lastRecordingTime = takentime
            if self.errorBars == 'Stddev':
                e = self.stat.stddev
                meanVal, minVal, maxVal = self.stat.mean, self.stat.mean-e, self.stat.mean+e
            elif self.errorBars == 'Stderr':
                e = self.stat.stderr
                meanVal, minVal, maxVal = self.stat.mean, self.stat.mean-e, self.stat.mean+e
            else:   
                meanVal, minVal, maxVal = self.stat.mean, self.stat.min, self.stat.max
            timeVal = self.timeStat.mean 
            self.stat.clear()
            self.timeStat.clear()
            return True, (timeVal, meanVal, minVal, maxVal)
        return False, None
    
    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict['stat']
        del odict['timeStat']
        return odict
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.stat = RunningStat()
        self.timeStat = RunningStat()
        
    def paramDef(self):
        return [{'name': 'points', 'type': 'int', 'object': self, 'field': 'averagePoints', 'value': self.averagePoints, 'tip': "points to average"},
                {'name': 'Error bars', 'type': 'list', 'object': self, 'field': 'errorBars', 'value': self.errorBars, 'tip': 'what is shown as error bars', 'values': ['Min Max','Stddev','Stderr']}]

decimationDict = { DynamicDecimation.name: DynamicDecimation,
                   Average.name: Average }