import pygsti
from pygsti.extras import idletomography as idt
from qiskit import *
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
import os


provider = IBMQ.load_account()
backend = provider.get_backend('ibmq_essex')

nQubits = 5
maxLengths = [1,2,4,8]

mdl_target = pygsti.construction.build_localnoise_model(nQubits, ["Gx","Gy","Gcnot"])
paulidicts = idt.determine_paulidicts(mdl_target)
listOfExperiments = idt.make_idle_tomography_list(nQubits, maxLengths, paulidicts)
print(len(listOfExperiments), "Idle Tomography experiments for {} qubits".format(nQubits))

r = [1, 2, 3] # data collection for multiple run

for elem in r:
    
    print("##### Run -- ", elem, "Long ####")
    run_number = "/run-" + str(elem)

    run = "./" + run_number

    try:
        os.mkdir(run)
    except:
        pass

    try:
        os.mkdir(run + "/result")
    except:
        pass

    try:
        os.mkdir(run + "/result" + "/count")
    except:
        pass

    # preparing IBM compatible quantum circuits list
    circ = []

    for kk in range(len(listOfExperiments)):
        c = listOfExperiments[kk].convert_to_openqasm(gatename_conversion=
                                                      {'Gy': 'ry(1.5707963267948966)',
                                                       'Gx': 'rx(1.5707963267948966)',
                                                       'Gcnot': 'cx'})

        circ.append( qiskit.circuit.QuantumCircuit.from_qasm_str(c) )
    
    # Execution on IBMQ machines
    batch_size = 75
    if len(listOfExperiments) % batch_size == 0:
        _range = int( len(listOfExperiments) / batch_size )
    else:
        _range = int( len(listOfExperiments) / batch_size ) + 1

    shots = 8192

    for kk in range( _range ):

        if kk == _range - 1:
            end = len( listOfExperiments)
            fileWriteRange = int( len( listOfExperiments)%batch_size ) # hardcoded for the time being 372 total circuit - 9 * 40 = 12
        else:
            end = (kk + 1) * batch_size
            fileWriteRange = batch_size


        job_exp = execute(circ[kk*batch_size:end], backend=backend, shots=shots)
        print("job finished")
        result_exp = job_exp.result()
        print(kk + 1, "batch jobs finished")

        for ii in range( fileWriteRange ):
            file_number = kk * batch_size + ii + 1

            fc = open(run + "/result/count/" + str(file_number) + '.txt', 'w')
            counts_exp = result_exp.get_counts(circ[file_number-1])
            fc.write( str(counts_exp) )
            fc.close()

        print(kk + 1, "batch write to file finished of run ", elem)
