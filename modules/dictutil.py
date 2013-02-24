# -*- coding: utf-8 -*-
"""
Created on Sat Feb 23 15:19:22 2013

@author: pmaunz
"""

def subdict( fulldict, keys ):
    return dict((name,fulldict[name]) for name in keys if name in fulldict)
    
    
if __name__=="__main__":
    d = {1:2, 3:4, 5:6, 7:8, 9:10}
    k = [1,5]
    print subdict(d,k)