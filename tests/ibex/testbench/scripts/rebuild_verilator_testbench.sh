#!/bin/bash
set -e
set -u
set -o pipefail

if [ "$#" -ne 1 ]; then
      echo "Configuration file required!"
      exit -1
fi
echo "Starting"
#CHECK_ARCHITECTURE=$(cat $1 | jq -r .check_architectural_correctness)
#if [ $? -ne 0 ]; then
#  echo "Could not get check architecture value"
#  exit $?
#fi
#echo ${CHECK_ARCHITECTURE}

VERILATOR_PATH=$(cat $1 | jq -r .verilator_path)
if [ $? -ne 0 ]; then
  echo "Could not get verilator path"
  exit $?
fi

#exit 0


CIRCUIT_OUT_FILEPATH=$(cat $1 | jq -r .circuit_out_fp)
#echo "Circuit out fp  $CIRCUIT_OUT_FILEPATH"

OUTPUT_DIR=$(cat $1 | jq -r .output_dir)
# Generate injection targets
if [ $OUTPUT_DIR != "null" ]; then
  if [ $VERILATOR_PATH == "null" ]; then 
    VERILATOR_PATH="$OUTPUT_DIR/testbench_verilator"
    VERILATOR_TESTBENCH_LIBRARY_PATH="$OUTPUT_DIR/testbench_library.so"
  fi
  if [ $CIRCUIT_OUT_FILEPATH == "null" ]; then 
    CIRCUIT_OUT_FILEPATH="$OUTPUT_DIR/circuit_out.json"
  fi
   #echo "$OUTPUT_DIR is not NULL"
   #VERILATOR_PATH="$OUTPUT_DIR/testbench_verilator"
   #CIRCUIT_OUT_FILEPATH="$OUTPUT_DIR/circuit_out.json"
   #mkdir -p "$OUTPUT_DIR"
fi

echo "$OUTPUT_DIR"
echo "circuiut out $CIRCUIT_OUT_FILEPATH"
#exit 0
if [ $CIRCUIT_OUT_FILEPATH == "null" ]; then 
  echo "No circuit out filepath set"
  exit -1
fi 
if [ $VERILATOR_PATH == "null" ]; then 
  echo "No verilator path filepath set"
  exit -1
fi 
mkdir -p "$(dirname "$VERILATOR_PATH")" 
echo "Generint injection targets"
mkdir -p build_tmp
cp src/sim_main.cpp build_tmp/sim_main.template.cpp
make from_template
python3 ../../../genInjectionTargets.py build_tmp/testbench_verilator_dir_out/Vsim_top___024root.h build_tmp/sim_main.template.cpp build_tmp/sim_main.cpp $CIRCUIT_OUT_FILEPATH # ${CHECK_ARCHITECTURE}
make
cp ./build_tmp/testbench_verilator_dir/Vsim_top $VERILATOR_PATH
cp ./build_tmp/testbench_library.so $VERILATOR_TESTBENCH_LIBRARY_PATH
