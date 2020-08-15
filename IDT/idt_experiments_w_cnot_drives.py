import pygsti
from pygsti.extras import idletomography as idt
from qiskit import *
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
import os



# enabling IBM Q account

provider = IBMQ.enable_account()
backend = provider.get_backend('ibmq_essex')


def run_idt_cnot( cnotQubits, _run, totalnQubits):
    '''Executes idle tomography experiments on an IBM device.
    args:
        cnotQubits: Qubit pair as a list On which repeated CNOT drive
                    will be applied.
        _run:   Run number as an integer. IDT data is collected for 
                   multiple runs.
        totalnQubits:   Total number of qubits in the quantum computer.
                        For `ibmq_essex` it is 5. 
    '''

    # Creating necessary directories to save results
    print("#### Run -- ", _run, " ####")
    run_number = "/run-" + str(_run)
    run = "./cnot_" + str(cnotQubits[0]) + str(cnotQubits[1]) + run_number + '/' # uncomment this line for short sequence run

    try:
        os.mkdir( "./cnot_" + str(cnotQubits[0]) + str(cnotQubits[1]) )
    except:
        pass

    try:
        os.mkdir(run)
    except:
        pass

    # preparing IBM compatible quantum circuits list
    nQubits = totalnQubits - 2
    maxLengths = [1,2,4,8]

    mdl_target = pygsti.construction.build_localnoise_model(nQubits, ["Gx","Gy","Gcnot"])
    paulidicts = idt.determine_paulidicts(mdl_target)
    listOfExperiments = idt.make_idle_tomography_list(nQubits, maxLengths, paulidicts)
    pygsti.io.write_circuit_list('ckt.txt', listOfExperiments, header=None)
    print(len(listOfExperiments), "Idle Tomography experiments for {} qubits".format(nQubits))

    new = list(range(totalnQubits))
    new.remove(cnotQubits[0])
    new.remove(cnotQubits[1])

    circ = []

    for kk in range(len(listOfExperiments)):
        c = listOfExperiments[kk].convert_to_openqasm(gatename_conversion=
                                                      {'Gy': 'ry(1.5707963267948966)',
                                                       'Gx': 'rx(1.5707963267948966)',
                                                       'Gcnot': 'cx'})
        f = open('circuit.txt', 'w')
        f.write(c)
        f.close()

        f = open('circuit.txt', 'r')
        fnew = open('circuit_cnot_added.txt', 'w')

        for line in f:

            if line[0] == 'b':
                fnew.write('cx '+ 'q[' + str(cnotQubits[0]) + '],'
                                + 'q[' + str(cnotQubits[1]) + '];\n' )
                line = 'barrier q[0], q[1], q[2], q[3], q[4];'
                fnew.write( line + '\n')
            elif line[0:4] == 'qreg':
                fnew.write('qreg q[5];\n')
            elif line[0] == 'r' or line[0:2] == 'id' or line[0] == 'm':

                if 'q[0]' in line:
                    _line = line.replace('q[0]', 'q[' + str(new[0]) + ']')
                    fnew.write(_line)
                elif 'q[1]' in line:
                    _line = line.replace('q[1]', 'q[' + str(new[1]) + ']')
                    fnew.write(_line)
                elif 'q[2]' in line:
                    _line = line.replace('q[2]', 'q[' + str(new[2]) + ']')
                    fnew.write(_line)
            else:
                fnew.write(line)
        fnew.close()
        f = open('circuit_cnot_added.txt','r')
        c = f.read()

        circ.append( qiskit.circuit.QuantumCircuit.from_qasm_str(c) )


    # Execution on IBMQ machines
    batch_size = 75 # All the Idle Tomography circuits cannot be
                    # executed on IBM machine at the same time.
                    # Therefore, the circuit list is broken into 
                    # `batches` and scheduled on the IBM quantum comp.
                    # Max. number of circuits IBM allows in 75.
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

            fc = open(run + str(file_number) + '.txt', 'w')
            counts_exp = result_exp.get_counts(circ[file_number-1])
            fc.write( str(counts_exp) )
            fc.close()

        print(kk + 1, "batch write to file finished of run ", _run)
