from liberty.parser import parse_liberty
import circuitgraph as cg
import networkx as nx
import re
import numpy as np
import collections
import params
import circuit
import matplotlib.pyplot as plt
import sys
import pandas as pd
import plotErrors
from pqdm.processes import pqdm

def static_analysis(delay_circuit): 

    _, longest_path = delay_circuit.calculate_path_lengths()
    cycle_time = longest_path[1] + params.TIMING_SLACK * longest_path[1]
    if params.PLOT_ENABLED:
        weights_flattened, edge_to_critialpath_count = delay_circuit.path_length_distribution(longest_path[1])
        n, bins, patches = plt.hist(weights_flattened)
        heights =  [patch.get_height() for patch in patches]

        plt.vlines([cycle_time, longest_path[1]],ymin=0,ymax=max(heights),colors=["r","y"])
        plt.show()

    delay_range = params.DELAY_FAULT_RANGE * cycle_time
    
    experiments = []
    for delay in delay_range:
        if params.DELAY_AT_GATE_OUTPUT:
            for node in list(delay_circuit.c.nodes()):
                if delay_circuit.c.is_output(node): continue
                experiments.append([delay_circuit, node, delay, cycle_time])
        else:
            for edge in list(delay_circuit.c.edges()):
                experiments.append([delay_circuit, edge, delay, cycle_time])

    delayed_flops_arr = []
    if params.RUN_PARALLEL:
        delayed_flops_arr = pqdm(experiments, circuit.single_trace, n_jobs=11, argument_type='args')
    else:
        for exp in experiments:
            delayed_flops_arr.append(circuit.single_trace(exp[0], exp[1], exp[2], exp[3]))

    #print(experiments)
    #print(delayed_flops_arr)

    plotErrors.plotErrorDist("Static Analysis (# of Violating Flops)", experiments, delayed_flops_arr, delay_range)


    return
