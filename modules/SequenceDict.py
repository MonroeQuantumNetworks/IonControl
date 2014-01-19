# A list that also works as a dict
from collections import MutableMapping
from operator import itemgetter
from itertools import izip_longest

class SequenceDict(dict, MutableMapping):

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        if not hasattr(self, '_keys'):
            self._keys = []
        self.update(*args, **kwds)

    def clear(self):
        del self._keys[:]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            self._keys.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __iter__(self):
        return iter(self._keys)

    def __reversed__(self):
        return reversed(self._keys)
    
    def renameAt(self, index, new):
        if new in self:
            raise KeyError('renameAt: "{0}" key already exists')
        dict[new] = dict.pop(self, self._keys[index] )
        self._keys[index] = new
        
    def popitem(self):
        if not self:
            raise KeyError('dictionary is empty')
        key = self._keys.pop()
        value = dict.pop(self, key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        inst_dict.pop('_keys', None)
        return (self.__class__, (items,), inst_dict)

    setdefault = MutableMapping.setdefault
    update = MutableMapping.update
    pop = MutableMapping.pop
    keys = MutableMapping.keys
    values = MutableMapping.values
    items = MutableMapping.items

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self.items()))

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, SequenceDict):
            return all(p==q for p, q in  izip_longest(self.items(), other.items()))
        return dict.__eq__(self, other)
    
    def at(self, index):
        return dict.__getitem__(self, self._keys[index])
    
    def keyAt(self, index):
        return self._keys[index]
    
    def sort(self, key=itemgetter(0), reverse=False):
        temp = sorted( self.iteritems(), key=key, reverse=reverse )
        self._keys = [itemgetter(0)(t) for t in temp]
        
    def sortByAttribute(self, attribute, reverse=False):
        temp = sorted( self.iteritems(), key=lambda a: getattr(a[1],attribute), reverse=reverse )
        self._keys = [itemgetter(0)(t) for t in temp]
    
    def index(self, key):
        return self._keys.index(key)
    
    def swap(self,index1,index2):
        self._keys[index1], self._keys[index2] = self._keys[index2], self._keys[index1]
        
    def sortToMatch(self, keylist):
        reverse = dict([ (value,index) for index,value in enumerate(keylist) ])
        self._keys = sorted( self._keys, key=lambda x: reverse[x])
            
if __name__=="__main__":
    a = SequenceDict()
    a[12] = 1
    a.update( {1:13, 3:14})
    print a.at(0)
    a.sort()
    print a.at(0)
    a.sort( key=itemgetter(1) )
    print a.at(0)
    
    class T:
        def __init__(self, i):
            self.t = i
            
        def __repr__(self):
            return "T({0})".format(self.t)
            
    a = SequenceDict()
    a[5] = T(42)
    a[3] = T(13)
    a[1] = T(7)
    
    print a.at(0)
    a.sortByAttribute('t')
    print a.at(0)
    a.sortByAttribute('t', reverse=True)
    print a.at(0)
    
    a.sortToMatch([3,5,7,9,1])
    print a
    
    