import pygsti
from pygsti.extras import idletomography as idt
import ast

def analysis(readFile, writeFile, dirName, nQubits):
    """"""This file reads experimental data from IBM.
    Prepares pyGSTi compatible dataset and analyze the dataset to extract error-rates.
    Args:
      readFile: experiment data file name as counts from IBM device
      writeFile: pyGSTi dataset
      dirName: directory of the experimental data
      nQubits: total number of qubits on which IDT was run
    """

    f = open(readFile, 'r')
    ds = open(writeFile, 'w')

    # preparing pyGSTi compatible dataset for IDT analysis
    w = ['0']*(2**(nQubits) + 1)
    w[0] = "## Columns ="
    for k in range(2**(nQubits)):
        if k == 2**(nQubits)-1:
            w[k+1] = format(k, "0"+str(nQubits)+"b") + " count\n"
        else:
            w[k+1] = format(k, "0"+str(nQubits)+"b") + " count,"
    ds.write(" ".join(w))

    k = 1

    for line in f:
        toWrite = ['0']*(2**nQubits + 1)
        toWrite[0] = line[0:len(line)-1]
        fIbmData = open( dirName + str(k)+'.txt', 'r' )

        for lineIbm in fIbmData:
            _dict = ast.literal_eval(lineIbm)

        # reversing the count string to make it pyGSTi compatible
        for key in _dict:
            keyReverse = key[::-1]
            toWrite[ int(keyReverse, 2) + 1 ] = str( _dict[key] )

        linew = '  '.join(toWrite)
        linew = linew + '\n'

        ds.write(linew)

        k = k + 1

    f.close()
    ds.close()

    f = open('data.txt', 'r')

    ds = pygsti.io.load_dataset('data.txt')
    maxLengths = [1,2,4,8]

    mdl_target = pygsti.construction.build_localnoise_model(nQubits, ["Gx","Gy","Gcnot"])
    paulidicts = idt.determine_paulidicts(mdl_target)

    # IDT results object that contains all error rates
    results = idt.do_idle_tomography(nQubits, ds, maxLengths, paulidicts)
