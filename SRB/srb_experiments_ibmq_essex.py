import numpy as np
from qiskit import *
import qiskit.ignis.verification.randomized_benchmarking as rb


provider = IBMQ.load_account()
backend = provider.get_backend('ibmq_essex')
basis_gates = ['u1','u2','u3','cx']
shots = 1024

#Number of seeds (random sequences)
nseeds = 50
#Number of Cliffords in the sequence (start, stop, steps)
nCliffs = np.arange(1,150,2)

qbits_pair_1 = [0,1]
qbits_pair_2 = [3,4]

for kk in range(3):
    if kk == 0:
        nQ = 2
        rb_pattern = [qbits_pair_1]
        length_multiplier = [1]
    elif kk ==1:
        nQ = 4
        rb_pattern = [qbits_pair_1, qbits_pair_2]
        print("Executing:",rb_pattern)
        length_multiplier = [1,1]
    elif kk == 2:
        nQ = 2
        rb_pattern = [qbits_pair_2]
        length_multiplier = [1]

    rb_opts = {}
    rb_opts['length_vector'] = nCliffs
    rb_opts['nseeds'] = nseeds
    rb_opts['rb_pattern'] = rb_pattern
    rb_opts['length_multiplier'] = length_multiplier
    rb_circs, xdata = rb.randomized_benchmarking_seq(**rb_opts)

    result_list = []

    for rb_seed,rb_circ_seed in enumerate(rb_circs):
        print('Compiling seed {}'.format(rb_seed))
        new_rb_circ_seed = qiskit.compiler.transpile(rb_circ_seed,
                                            basis_gates=basis_gates)
        qobj = qiskit.compiler.assemble(new_rb_circ_seed, shots=shots)
        print('Simulating seed {}'.format(rb_seed))
        job = backend.run(qobj)
        qiskit.tools.monitor.job_monitor(job)
        result_list.append(job.result())
    

    rbfit = rb.fitters.RBFitter(result_list, xdata, rb_opts['rb_pattern'])

    epc_0 = rbfit._fit[0]['epc']
    epg_0 = epc_0/1.5

    print("Error per Clifford = {}".format(epc_0))
    print("Error per Gate for CX {} = {}".format(rb_pattern[0], epg_0))
    
    if kk==1:
        epc_1 = rbfit._fit[1]['epc']
        epg_1 = epc_1/1.5

        print("Error per Clifford = {}".format(epc_1))
        print("Error per Gate for CX {} = {}".format(rb_pattern[1], epg_1))
