# Python code to analyze the TOA data file

import glob
import numpy as np
import matplotlib.pyplot as plt

from scipy import optimize
from matplotlib.backends.backend_pdf import PdfPages

directory = "C:\Experiments\CircY_96\Data\TOA\\20120904160656"


# Check if directory terminates in a '\'
if directory[-1] != '\\':
	directory += '\\'

# Get the timestamp of the directory
stamp = directory.rsplit('\\')[-2]

# Get filenames of all files *.dat
filename_list = glob.glob(directory + "*.dat")

# Number of files
num_files = len(filename_list)

# Output file
output_file =  "TOA_analysis-" + stamp + ".pdf"
pp = PdfPages(output_file)

# Number of header lines in file
header_lines = 5

# Number of bins in histogram
num_bins = 100

# Arrays for logging the amplitude and phase
a_coef = []
phi_coef = []
a_coef_std = []
phi_coef_std = []
line_number_array = []
print("Begin analysis...\n")
for fn in filename_list:
    print("Filename: "+fn)

	# Get RF frequency
    handle = open(fn)
    for idy in range(header_lines):
        line = handle.readline().split()

        for word in line:
            if word == "Filename":
                voltage_filename = line[ line.index(word)+2]
            elif word == "Line":
                linenumber = int( line[ line.index(word) + 2] )
            elif word == "RF":
                freq = float( line[ line.index(word) + 3] ) 
    # Close file
    handle.close()

    #log the line number into the array
    line_number_array.append(linenumber)

	# Read data file, skipping header
    data = np.loadtxt(fn,skiprows=header_lines)

    # Check for an empty file. If empty, then skip
    if len(data) == 0:
        print("Empty Data File. Line number " + str(linenumber))
        continue


    # Shift the origin of the data
    data = data - min(data)

    # Generate histogram
    histdata = np.histogram(data,num_bins)
    amp = histdata[0]
    time = (histdata[1][0:-1])*1e-9		# Left edge of bin -> phase shift

    # Fit function
    fnfit = lambda t,a,b,phi: a*np.cos(2*np.pi*freq*1e6*t+phi)+b
    # Fit
    try:
        xopt, xcov = optimize.curve_fit(fnfit, time, amp, [10,10,1])
    except RuntimeError:
        print("Cannot fit data for line: " + str(linenumber) )
        xopt = np.array([0,0,0])
        xcov = np.zeros([3,3])

    # Check for negative amplitudes
    if xopt[0]<0:
        xopt[0] = abs(xopt[0])
        xopt[2] = xopt[2] + np.pi

    # Round three decimal places
    xopt = xopt.round(3)

    # Residuals
    #residuals = amp - fnfit(time,xopt[0],xopt[1],xopt[2])

    # Confidence interval?
    # Std deviation of parameters:
    std_dev = np.sqrt(np.diag(xcov))

    # Save amplitude and phase for summary report
    a_coef.append(xopt[0])
    phi_coef.append(xopt[2])
    a_coef_std.append(std_dev[0])
    phi_coef_std.append(std_dev[2])

    # Generate figure for the analysis summary
    plt.clf()

    # Plot Raw data
    ax = plt.subplot(221)
    plt.tight_layout()
    plt.xlabel("Measurement", fontsize=10, name="Arial")
    plt.ylabel("Time (ns)", fontsize=10, name="Arial")
    plt.title("Raw Data", fontsize=12, name="Arial")
    plt.plot(data,'bo')
    ax.tick_params(axis="both", labelsize=10)

    # Histogram
    ax = plt.subplot(222)
    plt.tight_layout()
    plt.xlabel("Time (ns)", fontsize=10, name="Arial")
    plt.ylabel("Occurances", fontsize=10, name="Arial")
    plt.title("Histogram", fontsize=12, name="Arial")
    plt.hist(data,num_bins)
    ax.tick_params(axis="both", labelsize=10)

    # Fit
    ax = plt.subplot(223)
    plt.tight_layout()
    plt.xlabel("Time (ns)", fontsize=10, name="Arial")
    plt.ylabel("Occurances", fontsize=10, name="Arial")
    plt.title("Fit", fontsize=12, name="Arial")
    plt.plot(time/1e-9,fnfit(time,xopt[0],xopt[1],xopt[2]),time/1e-9,amp,'ro')
    ax.tick_params(axis="both", labelsize=10)

    # Info
    plt.subplot(224)
    plt.tight_layout()
    plt.axis([0,10,0,11])
    plt.axis("off")
    plt.text(0.5, 10, "Line = " + str(linenumber), fontsize=10, name="Arial" )
    plt.text(0.5,  9, "Number of bins = " + str(num_bins), fontsize=10,name="Arial")
    plt.text(0.5,  7, "Fit Function: $f(t) = a\cos(2\pi f_{RF} t + \phi) + b$ ", fontsize=10,name="Arial")
    plt.text(0.5,  6, "Coefficients (std. dev)",fontsize=10,name="Arial")
    plt.text(0.5,  5, "$a$ = " + str(xopt[0]) + " (" + str( std_dev[0] ) + ")",
			fontsize=10, name="Arial")
    plt.text(0.5,  4, "$b$ = " + str(xopt[1]) + " (" + str( std_dev[1] ) + ")",fontsize=10,name="Arial" )
    plt.text(0.5,  3, "$\phi$ = " + str(xopt[2]) + " (" + str( std_dev[2] ) + ")",fontsize=10,name="Arial" )
    plt.text(0.5,  2, "$f_{RF}$ = " + str( freq ) + "MHz",fontsize=10,name="Arial")

    plt.text(0.5,  1, "Voltage File = " + voltage_filename,fontsize=10,name="Arial")


    plt.savefig(pp, format='pdf')

# Now produce the summary report

#Convert from a list to an array
a_coef = np.array(a_coef)
phi_coef = np.array(phi_coef)
a_coef_std = np.array(a_coef_std)
phi_coef_std = np.array(phi_coef_std)

line_number_array = np.array(line_number_array)

plt.clf()

ax = plt.subplot(211)
plt.xlabel("Line Number", fontsize=10, name="Arial")
plt.ylabel("RF amplitude (fit)", fontsize=10, name="Arial")
plt.errorbar( line_number_array, a_coef, a_coef_std)
ax.tick_params(axis="both", labelsize=10)

ax = plt.subplot(212)
plt.xlabel("Line Number", fontsize=10, name="Arial")
plt.ylabel("RF Phase (fit) (degrees)", fontsize=10, name="Arial")
plt.errorbar( line_number_array, 180*phi_coef/np.pi, 180*phi_coef_std/np.pi)
ax.tick_params(axis="both", labelsize=10)

plt.savefig(pp, format='pdf')

pp.close()
