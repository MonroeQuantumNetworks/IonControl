import numpy as np
from scipy.optimize import curve_fit
def func(x, a, b, c, d):
     return np.square(a)/(np.square(a)+np.square(x-b))*np.square(np.sin(np.sqrt(1+np.square(x-b))*np.pi/2*c))+d#a*np.exp(-b*x) + c
x = np.linspace(-4,4,45)
y = func(x, 2.5, 1.3, 0.5, 1.1)
yn = y + 0.05*np.random.normal(size=len(x))
popt, pcov = curve_fit(func, x, yn)
print popt
