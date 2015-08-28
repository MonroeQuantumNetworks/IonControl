class Event(object):
    pass

class Observable(object):
    def __init__(self):
        self.callbacks = []
        
    def subscribe(self, callback, unique=False):
        if unique:
            if callback not in self.callbacks:
                self.callbacks.append(callback)
        else:
            self.callbacks.append(callback)
        
    def unsubscribe(self, callback):
        self.callbacks.pop( self.callbacks.index(callback) )
        
    def clear(self):
        self.callbacks = []
        
    def fire(self, **attrs):
        e = Event()
        e.source = self
        for k, v in attrs.iteritems():
            setattr(e, k, v)
        for fn in self.callbacks:
            fn(e)
            
    def firebare(self):
        for fn in self.callbacks:
            fn()
