import visa

class VisaInstrument(object):
    def __init__(self, **kwargs):
        self.inst = None
        pass

    def query(self, command):
        pass

    def write(self, command):
        pass

    def close(self):
        pass

    def __del__(self):
        self.close()
