import pygsti
import pygsti.construction as pc

from math import sqrt
import numpy as np

#Initialize an empty GateSet object
gateset1 = pygsti.objects.GateSet()

#Populate the GateSet object with states, effects, gates,
# all in the *normalized* Pauli basis: { I/sqrt(2), X/sqrt(2), Y/sqrt(2), Z/sqrt(2) }
# where I, X, Y, and Z are the standard Pauli matrices.
gateset1['rho0'] = [ 1/sqrt(2), 0, 0, 1/sqrt(2) ] # density matrix [[1, 0], [0, 0]] in Pauli basis
gateset1['E0'] = [ 1/sqrt(2), 0, 0, -1/sqrt(2) ]  # projector onto [[0, 0], [0, 1]] in Pauli basis
gateset1['Gi'] = np.identity(4,'d') # 4x4 identity matrix
gateset1['Gx'] = [[1, 0, 0, 0],
                  [0, 1, 0, 0],
                  [0, 0, 0,-1],
                  [0, 0, 1, 0]] # pi/2 X-rotation in Pauli basis

gateset1['Gy'] = [[1, 0, 0, 0],
                  [0, 0, 0, 1],
                  [0, 0, 1, 0],
                  [0,-1, 0, 0]] # pi/2 Y-rotation in Pauli basis

#Create SPAM labels "plus" and "minus" using the special "remainder" label,
# and set the then-needed identity vector.
gateset1.spamdefs['plus'] = ('rho0','E0')
gateset1.spamdefs['minus'] = ('rho0','remainder')
gateset1['identity'] = [ sqrt(2), 0, 0, 0 ]  # [[1, 0], [0, 1]] in Pauli basis

pygsti.io.write_gateset(gateset1, "tutorial_files/MyTargetGateset.txt")


#Create fiducial gate string lists
fiducials = pygsti.construction.gatestring_list( [ (), ('Gx',), ('Gy',), ('Gx','Gx'), ('Gx','Gx','Gx'), ('Gy','Gy','Gy') ])

#Create germ gate string lists
germs = pygsti.construction.gatestring_list( [('Gx',), ('Gy',), ('Gi',), ('Gx', 'Gy',),
         ('Gx', 'Gy', 'Gi',), ('Gx', 'Gi', 'Gy',), ('Gx', 'Gi', 'Gi',), ('Gy', 'Gi', 'Gi',),
         ('Gx', 'Gx', 'Gi', 'Gy',), ('Gx', 'Gy', 'Gy', 'Gi',),
         ('Gx', 'Gx', 'Gy', 'Gx', 'Gy', 'Gy',)] )

#Create maximum lengths list
maxLengths = [1,2,4,8,16,32]

pygsti.io.write_gatestring_list("tutorial_files/MyFiducials.txt", fiducials, "My fiducial gate strings")
pygsti.io.write_gatestring_list("tutorial_files/MyGerms.txt", germs, "My germ gate strings")

listOfExperiments = pygsti.construction.make_lsgst_structs(gateset1.gates.keys(),
                                                                   fiducials, fiducials, germs, maxLengths)
# myset = dict((ex, idx) for idx, ex in enumerate(listOfExperiments))




#Create an empty dataset file, which stores the list of experiments
#plus extra columns where data can be inserted
pygsti.io.write_empty_dataset("tutorial_files/MyDataTemplate.txt", listOfExperiments[-1].allstrs,
                              "## Columns = plus count, count total")