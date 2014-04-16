# File weakmethod.py
import weakref 
#import new

class ref(object):
    """Wraps any callable, most importantly a bound method, in
    a way that allows a bound method's object to be GC'ed, while
    providing the same interface as a normal weak reference"""
    def __init__(self, fn):
        try:
            o, f, c = fn.im_self, fn.im_func, fn.im_class
        except AttributeError:
            self._obj = None
            self._func = fn
            self._class = None
        else:
            if o is None:
                self._obj = None
            else:
                self._obj = weakref.ref(o)
            self._func = f
            self._class = c
            
    def __call__(self):
        if self._obj is None:
            return self._func
        else:
            obj = self._obj()
#            return new.instancemethod( self._func, obj, self._class ) if obj is not None else None
            return self._func.__get__( obj, self._class ) if obj is not None else None

        
if __name__=="__main__":
    class C(object):
        def f(self):
            print "Hallo"
            
        def __del__(self):
            print "C says bye"
            
    c = C()
    r = ref(c.f)
    r()()
    del c