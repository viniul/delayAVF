#!/bin/bash
set -e

if [ "$#" -eq 0 ]; then
      echo "Configuration file required!"
      exit -1
fi

for f in "$@"; do
	# Run setup
	bash run_setup.sh $f
	../../../delayFaultSimulatorRust/target/release/delay_fault_simulator $f
	python3 ../../../calculateFitDecreaseNew.py $f
done
