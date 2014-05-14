'''
Created on Mar 22, 2014

@author: pmaunz
'''


def max_iterable( iterable ):
    """return max of iterable, return None if empty"""
#    it = iter( iterable )
#    m = next(it, None)
#    if m is None:
#        return None
#    return max( max(it), m )
    try:
        mymax = max(iterable)
    except ValueError:
        return None
    return mymax

def min_iterable( iterable ):
    """return min of iterable, return None if empty"""
    it = iter( iterable )
    m = next(it, None)
    if m is None:
        return None
    return min( min(it), m )

if __name__=="__main__":
    print max_iterable( (10-i for i in xrange(7)))
    print min_iterable( (10-i for i in xrange(7)))