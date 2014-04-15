'''
Created on Apr 15, 2014

@author: plmaunz
'''

from functools import partial

import WeakMethod

class WeakPartial(partial):
    def __init__(self, func, *args, **kwargs):
        super(WeakPartial, self).__init__( None, *args, **kwargs )
        self.myfunc = WeakMethod.ref(func)
                
    def __call__(self, *args, **kwargs):
        kw = self.keywords.copy() if self.keywords else dict()
        kw.update(kwargs)
        funcobj = self.myfunc()
        return funcobj( *(self.args+args), **kwargs)
    
if __name__=="__main__":
    class C(object):
        def f(self, one, two, three, other="Nothing"):
            print "Hallo", one, two, three, other
            
        def __del__(self):
            print "C says bye"
            
    c = C()
    
    p = WeakPartial( c.f, "one" , "two", other="other" )
    p("three", other="other")
    
    del c
    p("else")