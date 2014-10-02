'''
Created on Sep 30, 2014

@author: wolverine
'''

from multiprocessing.connection import Client

c = Client(("localhost",16000), authkey="peekaboo")
c.send("Hello")
print c.recv()

c.send([1,2,3,4])
print c.recv()

c.send({"name":'Dave','email':'dave@dabeaz.com'})
print c.recv()
