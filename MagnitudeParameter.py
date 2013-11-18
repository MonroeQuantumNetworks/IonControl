from pyqtgraph.parametertree.parameterTypes import WidgetParameterItem, registerParameterType
from pyqtgraph.parametertree.Parameter import Parameter
from MagnitudeSpinBox import MagnitudeSpinBox

class MagnitudeWidgetParameterItem(WidgetParameterItem):
    def __init__(self, param, depth):
        WidgetParameterItem.__init__(self, param, depth)

    def makeWidget(self):
        w = MagnitudeSpinBox()
        w.sigChanged = w.valueChanged
        return w

class MagnitudeParameter(Parameter):
    itemClass = MagnitudeWidgetParameterItem
    
    def __init__(self, *args, **kargs):
        Parameter.__init__(self, *args, **kargs)
 
registerParameterType('magnitude', MagnitudeParameter, override=True)   

if __name__=="__main__":
    pass
   