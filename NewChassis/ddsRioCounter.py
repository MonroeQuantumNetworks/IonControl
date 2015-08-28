from devices.ddsRio import ddsRio
from gui.PyQwtPlotDlg import AutoUpdatePlot
from pCounter import IBinPCounter

class ddsRioCounter(object):
    def __init__(self, **kwargs):
        if kwargs.has_key('clientType'):
            clientType = kwargs.pop('clientType')
        else:
            clientType = 'serial'

        if not kwargs.has_key('device'):
            kwargs['device'] = 'COM1'

        self.rio = ddsRio(clientType, **kwargs)
        self.CNT = self.rio.CNT

    def _getSamplesAvailable(self):
        return self.CNT.samplesAvail

    samplesAvailable = property(_getSamplesAvailable)

    def read(self):
        return self.CNT.Read()

    def close(self):
        self.rio.close()

class DDSRioBinCounter(IBinPCounter, ddsRioCounter):
    def __init__(self, **kwargs):
        super(DDSRioBinPCounter, self).__init__()


class RioCntrPlotDlg(ddsRioCounter, AutoUpdatePlot):
    def __init__(self, **kwargs):
        from PyQt4.Qt import Qt
        kwargs['chartXAxisTitle'] = kwargs.get('chartXAxisTitle',
                'Time (Units)')
        kwargs['chartYAxisTitle'] = kwargs.get('chartYAxisTitle',
                'Counts')
        AutoUpdatePlot.__init__(self, **kwargs)
        ddsRioCounter.__init__(self, **kwargs)
        self._curveTitle = 'counts'
        self.addCurve(self._curveTitle, curveColor=Qt.blue)
        self.samplesToAcquire = 70
        self._plot = False
        self._plotData = 0
        self._closed = False

    def timerEvent(self, e):
        print 'test'
        self.update(self._curveTitle, self._plotData)
        #self._plot = False

    def read(self):
        data = super(RioCntrPlotDlg, self).read()
        print 'data: ', data, type(data)
        self._plot = True
        self._plotData = data[0]

    def close(self):
        super(RioCntrPlotDlg, self).close()
        self._closed = True
