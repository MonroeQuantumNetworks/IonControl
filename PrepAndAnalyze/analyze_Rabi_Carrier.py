# Python code to analyze the TOA data file

import glob
import numpy as np
import matplotlib.pyplot as plt

from scipy import optimize
from matplotlib.backends.backend_pdf import PdfPages

directory = r"C:\Users\Public\Documents\experiments\HOA\2013\2013_05\2013_05_16"

# Check if directory terminates in a '\'
if directory[-1] != '\\':
	directory += '\\'

# Get filenames of all files *.dat
filename = directory + "RabiFlop_003.txt"
mass=40  # Calcium mass
angle=0; # angle between the laser and the trap axis.  In the MOL Chamber this is currently 0
freq=0.8 # Secular freq in MHz
A0=1 #Amplitude of State Prep 0-1
omega0=.28 #Rabi Freq
n0=7 # intial guess at avergae n 


# Output file
output_file =  "Rabi_analysis.pdf"
pp = PdfPages(output_file)

# Number of header lines in file
header_lines = 63


hbar=1.05457148e-34;
m=mass*1.66053886e-27;
secfreq=freq*1e6;
eta=(2*np.pi/729e-9)*np.cos(angle*np.pi/180)*np.sqrt(hbar/(2*m*2*np.pi*secfreq));
et2=eta*eta

data = np.loadtxt(filename,skiprows=header_lines)
X=data[:,0];
Y=data[:,1];

# Fit function
fnfit = lambda t, A,n,o: A/2*(1-1/(n+1)*(np.cos(2*o*t)*(1-n/(n+1)*np.cos(2*o*t*et2))+(n/(n+1))*np.sin(2*o*t)*np.sin(2*o*t*et2))/(1+(n/(n+1))**2-2*(n/(n+1))*np.cos(2*o*t*et2)))
	# Fit
try:
	xopt, xcov = optimize.curve_fit(fnfit, X, Y, [A0,n0,omega0])
except RuntimeError:
	print("Cannot fit data for line")
print xopt 
	# Generate figure for the analysis summary
plt.clf()

	# Plot Raw data
plt.subplot(211)
plt.tight_layout()
plt.xlabel("time (us)")
plt.ylabel("D_5/2 Population")
plt.title("Carrier Rabi")
#	plt.plot(X,Y,'bo-')
plt.plot(X,fnfit(X,xopt[0],xopt[1],xopt[2]),X,Y,'ro')
##
 
nstart=2*xopt[1]
taufinal=(1/xopt[2])/(eta);
US_SCTIMEINIT=(1/xopt[2])/(eta*np.sqrt(xopt[1]))
NS_SCINC=(taufinal-US_SCTIMEINIT)/nstart*1000
number_of_loops=nstart


plt.subplot(212)
plt.tight_layout()
plt.axis([0,10,0,11])
plt.axis("off")
plt.text(0.5, 10, "n = " + str(xopt[1]))
plt.text(0.5,  9, "A = "+ str(xopt[0]))
plt.text(0.5,  7, "eta = "+ str(eta))
plt.text(0.5,  6, "tauFinal = " + str(taufinal))
plt.text(0.5,  5, "IntialSCTime = " + str(US_SCTIMEINIT))
plt.text(0.5,  4, "NS_SCINC =" + str(NS_SCINC))
plt.text(0.5,  3, "number of loops= " + str(number_of_loops))
    
plt.savefig(pp, format='pdf')
##
### Now produce the summary report
##
###Convert from a list to an array
##a_coef = np.array(a_coef)
##phi_coef = np.array(phi_coef)
##a_coef_std = np.array(a_coef_std)
##phi_coef_std = np.array(phi_coef_std)
##
##plt.clf()
##
##plt.subplot(211)
##plt.xlabel("Line Number")
##plt.ylabel("RF amplitude (fit)")
##plt.errorbar( np.arange(0,len(a_coef))+1, a_coef, a_coef_std)
##
##plt.subplot(212)
##plt.xlabel("Line Number")
##plt.ylabel("RF Phase (fit) (degrees)")
##plt.errorbar( np.arange(0,len(phi_coef))+1, 180*phi_coef/np.pi, 180*phi_coef_std/np.pi)
##
##plt.savefig(pp, format='pdf')
##
pp.close()
