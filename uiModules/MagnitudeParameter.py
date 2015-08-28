from pyqtgraph.parametertree.Parameter import Parameter
from pyqtgraph.parametertree.parameterTypes import WidgetParameterItem, registerParameterType
from PyQt4 import QtGui
from MagnitudeSpinBox import MagnitudeSpinBox
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

class PasswordParameterItem(WidgetParameterItem):
    def __init__(self, param, depth):
        WidgetParameterItem.__init__(self, param, depth)

    def makeWidget(self):
        w = QtGui.QLineEdit()
        w.sigChanged = w.editingFinished
        w.value = lambda: asUnicode(w.text())
        w.setValue = lambda v: w.setText(asUnicode(v))
        w.sigChanging = w.textChanged
        w.setEchoMode( QtGui.QLineEdit.Password )
        return w

class PasswordParameter(Parameter):
    itemClass = PasswordParameterItem
    
    def __init__(self, *args, **kargs):
        Parameter.__init__(self, *args, **kargs)

registerParameterType('magnitude', MagnitudeParameter, override=True)   
registerParameterType('password', PasswordParameter, override=True)   

if __name__=="__main__":
    pass
