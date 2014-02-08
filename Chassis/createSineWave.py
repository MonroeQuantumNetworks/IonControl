import numpy as np


def createSineWave(amplitude, frequency, sampleRate, numSamples, phase = 0):
    #calculated params
    dt = 1 / np.float64(sampleRate)
    #print 'dt: ' + str(dt)
    totalTime = dt*numSamples
    #print 'total time: ' + str(totalTime)
    t = np.linspace(0 , totalTime, numSamples)
    a = amplitude * np.sin(2*np.pi*frequency*t + phase)
    
    return {'time': t, 'amplitude': a}

