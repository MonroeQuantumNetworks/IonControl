from ctypes import *
import sys
import os

sys.path.insert(0, os.path.abspath('..'))

import niSyncFunctions as niSync

Session = c_void_p(0)
errorMessage = create_string_buffer(100)
device = c_char_p('PXI1Slot2')

status = niSync.init(device, 0, 0, byref(Session))
if status != 0:
    status = niSync.error_message(Session, status, errorMessage)
    print errorMessage.value

attValue = niSync.ViInt32_P()
status = niSync.GetAttributeViInt32(Session, c_char_p(),
                                    niSync.NISYNC_ATTR_SERIAL_NUM,
                                    byref(attValue))
if status != 0:
    status = niSync.error_message(Session, status, errorMessage)
    print errorMessage.value

print attValue.value

status = niSync.close(Session)