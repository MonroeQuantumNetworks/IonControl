'''
Created on Jun 27, 2014

@author: pmaunz
'''

import Read_N9010A
import Read_E5100B
import Read_N9342CN

instrumentmap = {
    'N9342CN' : Read_N9342CN.N9342CN,
    'E5100B' : Read_E5100B.E5100B,
    'N9010A' : Read_N9010A.N9010A
}
