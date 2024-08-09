#!/bin/bash
set -e
#cd fusesoc_libraries/picorv32/
#make testbench_verilator
./build_tmp/testbench_verilator_dir_out/Vsim_top +trace-underscore +vcd +firmware=$1 +timeout=$2 --x-initial=1 --x-assign=1 +seed=50
cd -
