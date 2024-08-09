import numpy as np
import multiprocessing
# === PARAMETERS ===

EDGE_FIT = 0.01
FLOP_FIT = 0.01
COMPLEXITY_DEBUG = True

# How much slack to give the clock (in percentage of longest path)
TIMING_SLACK = 0.10

FLOP_INITIAL_VALUE = 0 # Default initial value of inputs flops (#TODO: Could set "?" and propagate?)

# Range of delay faults to test
# Where 0 is no fault, and 1 is an entire clock cycle
#Max steps 152 Delay range [15, 30, 46, 61, 76, 91, 106, 122] 
DELAY_FAULT_RANGE = np.linspace(3,10,7)
#Set to true to add the same delay to all edges
ADD_ABSOLUTE_DELAY = False
#Overall runtime 12_800 cycles
NUM_SIM_CYCLES = 400

# Which flip-flop instance to use when 
DFF_REPLACE = 'DFFRQ_X1'
BUF_REPLACE = 'BUF_X1'


#DFF_REPLACE = 'DFF_X1'
#BUF_REPLACE = 'BUF_X1'

WEIGHT_ATTRIBUTE = "weight"

PLOT_ENABLED = True
PLOT_ZEROS = False
EDGE_FIT = 0.01
FLOP_FIT = 0.01

DUMP_RESULTS = True

TRACE_DEBUG = False
LONGEST_PATH_DEBUG = False
PATH_DEBUG = False
SIMULATION_DEBUG = False
CIRCUIT_BUILD_DEBUG = False
ACE_ANALYSE_DEBUG = False
LOAD_PICKLED = False

DELAY_AT_GATE_OUTPUT = False

COLLECT_FAULTS_X_CYCLES = False
COMPARE_SDC_VS_CRASH = False

DEEPCOPY = False

RUN_PARALLEL = True
#Note that verilator also starts threads. To increase allowed numbers of threads  run echo 600000 | sudo tee /proc/sys/vm/max_map_count
#This should prevent a resource not avaiable error.
NJOBS = multiprocessing.cpu_count() # 80 # 80 # #80 #80

VERILATOR_MAX_TIMEOUT = 50000000

SKIP_FIT_REDUCTION = True

delayStepAttributeString = "delayStep"
