'''
Created on Feb 23, 2014

@author: pmaunz
'''


def interleave_iter( *iterables ):
    iterlist = [ iter(a) for a in iterables if a is not None ]
    while True:
        try:
            for it in iterlist:
                yield it.next()
        except StopIteration:
            return

def concatenate_iter( *iterables ):
    iterlist = [ iter(a) for a in iterables if a is not None ]
    for it in iterlist:
        try:
            while True:
                yield it.next()
        except StopIteration:
            pass
    return 

if __name__ == "__main__":
    a = [1,2,3]
    b = [4,5,6]
    c = None
    d = [10,11,12]
    
    for i in concatenate_iter(a,b,c,d):
        print i
        
    for i in concatenate_iter( *(range(j) for j in [2,3,4]) ):
        print i