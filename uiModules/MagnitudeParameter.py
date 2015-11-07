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
        w.sigChanged = w.valueChanged
        #w.valueChanged.connect(self.widgetValueChanged)
        w.dimension = self.dimension
        return w

class ExpressionParameter(Parameter):
    itemClass = ExpressionWidgetParameterItem

    def __init__(self, *args, **kargs):
        self.dimension = kargs.get('dimension')
        Parameter.__init__(self, *args, **kargs)


registerParameterType('magnitude', MagnitudeParameter, override=True)   
registerParameterType('expression', ExpressionParameter, override=True)

if __name__=="__main__":
    pass
