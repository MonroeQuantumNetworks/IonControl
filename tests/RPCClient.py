'''
Created on Jul 1, 2014

@author: pmaunz
'''
import xmlrpclib

s = xmlrpclib.ServerProxy('http://127.0.0.1:8000')
print s.pow(2,3)  # Returns 2**3 = 8
print s.add(2,3)  # Returns 5
print s.div(5,2)  # Returns 5//2 = 2

# Print list of available methods
print s.system.listMethods()