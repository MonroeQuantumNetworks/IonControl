"""
Created on 04 Dec 2015 at 1:49 PM

author: jmizrahi
"""

from modules.Expression import Expression

class VarAsOutputChannel(object):
    """This is a class that makes the AWG parameters work as an external parameter output channel in a parameter scan.

    The AWG variables are not external parameter output channels, but the external parameter scan method the scan parameter
    to have several specific methods and attributes (as OutputChannel does). This class provides those attributes."""
    def __init__(self, device, name):
        self.device = device
        self.name = name
        self.useExternalValue = False
        self.savedValue = None

    @property
    def value(self):
        return self.device.settings.waveform.varDict[self.name]['value']

    @property
    def strValue(self):
        return self.device.settings.waveform.varDict[self.name]['text']

    def saveValue(self, overwrite=True):
        """save current value"""
        if self.savedValue is None or overwrite:
            self.savedValue = self.value
        return self.savedValue

    def setValue(self, targetValue):
        """set the variable to targetValue"""
        if targetValue is not None:
            self.device.settings.waveform.varDict[self.name]['value'] = targetValue
            self.device.program()
        return True

    def restoreValue(self):
        """restore the value saved previously, if any, then clear the saved value."""
        value = self.savedValue if self.strValue is None else Expression().evaluateAsMagnitude(self.strValue, self.globalDict)
        if value is not None:
            self.setValue(value)
            self.savedValue = None
        return True