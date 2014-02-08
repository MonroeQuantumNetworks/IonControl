import os
import platform
import sys


# This file sets the path for the location of the niSync dll, which differs depending on the os.
# Windows XP: C:\Program Files\National Instruments\IVI Foundation\VISA\WinNT\Bin
# Widnows 7: C:\Program Files (x86)\IVI Foundation\VISA\WinNT\Bin
#
# The API reference documentation is in the following directory:
# C:\Program Files (x86)\IVI Foundation\VISA\WinNT\niSync
if sys.platform.startswith('win'):
    lib_directory = r'C:\Program Files\IVI Foundation\VISA\WinNT\Bin'
    lib_directory += "//"

    if platform.release() == '7':
	if sys.platform.endswith('32'):
		lib_directory = r'C:\Program Files\IVI Foundation\VISA\WinNT\Bin'
		lib_directory += "\\"
	else:
        	lib_directory = r'C:\Program Files (x86)\IVI Foundation\VISA\WinNT\Bin'
        	lib_directory += "\\"
    if os.path.exists(r'C:\Program Files (x86)'):
        lib_directory = r'C:\Program Files (x86)\IVI Foundation\VISA\WinNT\Bin'
        lib_directory += "\\"
        
    lib_name = "niSync"

else:
    raise NotImplementedError, "Location of niSync library unknown on %s." % (sys.platform)
