import numpy as np

a = np.array([1,0,5,0,-1])
c = a != 0

print c
print np.sum(c)
print a[c]