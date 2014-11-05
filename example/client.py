'''
Created on Sep 30, 2014

@author: wolverine
'''

from multiprocessing.connection import Client
from modules.magnitude import mg

c = Client(("localhost",16888), authkey="yb171")
c.send( ('getOutputFrequency', tuple() ) )
print c.recv()
c.send( ('setOutputFrequency', (mg(123,'MHz'), ) ) )
print c.recv()

