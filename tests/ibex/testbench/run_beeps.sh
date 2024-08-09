#!/bin/bash
set -e
set -o pipefail
set -u

stringContain() { case $2 in *$1* ) echo 0;; *) echo 1;; esac ;}
#https:/i/gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425#set--e--u--x--o-pipefail
mkdir -p beeps_benchmark_data/logs
for f in configs/beeps/*.dict; do
    OUTPUT_DIR=$(cat $f | jq  -r .output_dir)
    #if [[ -e $OUTPUT_DIR/protection_rates.json ]]; then
    #	    echo "Skipping $f, already done"
    #else
    	echo "Doing $f"
	benchmark_name=$(basename $f)
	#for substr in "mat_mult_state.dict"; do # 5 substrings
	#for substr in "libstrstr"; do # 5 substrings
	#	echo "$substr"
	#	contained=$(stringContain "$substr" "$benchmark_name")
		#echo "contained $contained"
	#	if [ "$contained" == 1 ] ; then
	#		echo "Skip $benchmark_name!"
	#		continue 2;
	#	fi
	#done
	echo "Will now do $benchmark_name"
	#exit 0
	#exit 0
    	if [[ ! -e $OUTPUT_DIR/circuit_out.json ]]; then
    		./run_setup.sh $f 2>&1 | tee -a "beeps_benchmark_data/logs/${benchmark_name}_log_setup.txt"
	fi
    	#if [[ ! -e $OUTPUT_DIR/timing_metadata.json ]]; then
    	#	../../delayFaultSimulatorRust/target/release/delay_fault_simulator --dump_only $f | tee -a "beeps_benchmark_data/logs/${benchmark_name}_log_delay_fault.txt"
    	#fi
    	if [[ ! -e $OUTPUT_DIR/delay_injection_res.json ]]; then
    		../../../delayFaultSimulatorRust/target/release/delay_fault_simulator $f | tee -a "beeps_benchmark_data/logs/${benchmark_name}_log_delay_fault.txt"
    	fi
  
    #rm -rf $OUTPUT_DIR/aceness_results_cache/
    
    if [[ ! -e $OUTPUT_DIR/protection_rates.json ]]; then
    	python3 ../../../calculateFitDecreaseNew.py $f | tee -a "beeps_benchmark_data/logs/${benchmark_name}_log_fit_decrease.txt"
    fi
    #fi	
    echo $f;
done
