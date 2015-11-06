from pyqtgraph.parametertree.Parameter import Parameter
from pyqtgraph.parametertree.parameterTypes import WidgetParameterItem, registerParameterType
from PyQt4 import QtGui
from MagnitudeSpinBox import MagnitudeSpinBox
from ExpressionSpinBox import ExpressionSpinBox
from pyqtgraph.python2_3 import asUnicode


class MagnitudeWidgetParameterItem(WidgetParameterItem):
    def __init__(self, param, depth):
        self.dimension = param.dimension
        WidgetParameterItem.__init__(self, param, depth)

    def makeWidget(self):
        w = MagnitudeSpinBox()
        w.sigChanged = w.valueChanged
        w.dimension = self.dimension
        return w

class MagnitudeParameter(Parameter):
    itemClass = MagnitudeWidgetParameterItem

    def __init__(self, *args, **kargs):
        self.dimension = kargs.get('dimension')
        Parameter.__init__(self, *args, **kargs)

class ExpressionWidgetParameterItem(WidgetParameterItem):
    def __init__(self, param, depth):
        self.dimension = param.dimension
        WidgetParameterItem.__init__(self, param, depth)
        self.hideWidget = False

    def makeWidget(self):
        v = self.param.opts['value']
        w = ExpressionSpinBox(globalDict=v.globalDict)
        w.setExpression(v)
        #w.sigChanged = w.expressionChanged
        #w.valueChanged.connect(self.widgetValueChanged)
        w.dimension = self.dimension
        return w

class ExpressionParameter(Parameter):
    itemClass = ExpressionWidgetParameterItem

    def __init__(self, *args, **kargs):
        self.dimension = kargs.get('dimension')
        Parameter.__init__(self, *args, **kargs)

    def setValue(self, value, blockSignal=None):
        """
        Set the value of this Parameter; return the actual value that was set.
        (this may be different from the value that was requested)
        """
        try:
            if blockSignal is not None:
                self.sigValueChanged.disconnect(blockSignal)
            if self.opts['value'].value == value:
                #self.sigValueChanged.emit(self, value)
                return value
            self.opts['value'].value = value
            self.sigValueChanged.emit(self, value)
        finally:
            if blockSignal is not None:
                self.sigValueChanged.connect(blockSignal)

        return value


registerParameterType('magnitude', MagnitudeParameter, override=True)   
registerParameterType('expression', ExpressionParameter, override=True)

if __name__=="__main__":
    pass
