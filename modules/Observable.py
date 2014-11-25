class Event(object):
    pass

class Observable(object):
    def __init__(self):
        self.callbacks = []
        
    def subscribe(self, callback):
        self.callbacks.append(callback)
        
    def fireEvent(self, **attrs):
        e = Event()
        e.source = self
        for k, v in attrs.iteritems():
            setattr(e, k, v)
        for fn in self.callbacks:
            fn(e)
            
    def fireBare(self):
        for fn in self.callbacks:
            fn()

    def fire(self, *args, **kwargs):
        for fn in self.callbacks:
            fn(*args, **kwargs)
