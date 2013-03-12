# -*- coding: utf-8 -*-
"""
Created on Sat Feb 23 15:19:22 2013

@author: pmaunz
"""

def subdict( fulldict, keys ):
    if keys is not None and fulldict is not None:
        return dict((name,fulldict[name]) for name in keys if name in fulldict)
    else:
        return dict()
    
    
if __name__=="__main__":
    d = {1:2, 3:4, 5:6, 7:8, 9:10}
    k = [1,5]
    print subdict(d,k)