#!/bin/bash
set -e
set -o pipefail
set -u

# Build delay fault simulator
cd ../../../delayFaultSimulatorRust/
cargo build --release 2>/dev/null 
cd -

# Set scripts we'll need to generate benchmarks as executable
#chmod +777 run_gen_verilator_trace.sh 
#chmod +777 run_groundtruth_benchmark.sh 

# Determine which SYNTH_SUBMODULE we're working with
set +o pipefail
set +e
SYNTH_SUBMODULE=$(cat $1 | jq -e -r .submodule_name)
if [ $? -ne 0 ]; then
  echo "Could not get submodule name"
  SYNTH_SUBMODULE=""
  #exit $?
fi
echo "Value ${SYNTH_SUBMODULE}"

SYNTH_SHORT_SUBMODULE_NAME=$(cat $1 | jq -e -r .short_submodule_name)
if [ $? -ne 0 ]; then
  echo "Could not get submodule name"
  SYNTH_SHORT_SUBMODULE_NAME=""
  #exit $?
fi
echo Value SYNTH_SHORT_SUBMODULE_NAME ${SYNTH_SHORT_SUBMODULE_NAME}

set -e
set -o pipefail
#CHECK_ARCHITECTURE=$(cat $1 | jq -e .check_architectural_correctness)
#if [ $? -ne 0 ]; then
#  echo "Could not get check architecture value \n"
#  exit $?
#fi
#echo Check architecture ${CHECK_ARCHITECTURE}

VERILATOR_PATH=$(cat $1 | jq -r .verilator_path)
#if [ $? -ne 0 ]; then
#  echo "Could not get verilator path"
#  exit $?
#fi

HEX_PAYLOAD=$(cat $1 | jq -r .hex_payload)


CIRCUIT_OUT_FILEPATH=$(cat $1 | jq -r .circuit_out_fp)
#echo "Circuit out fp  $CIRCUIT_OUT_FILEPATH"

OUTPUT_DIR=$(cat $1 | jq -r .output_dir)

export ECC_ON=$(cat $1 | jq -r .ecc_on)

#echo $OUTPUR_DIR
#if OUTPUR_DIR=$(jq -r --arg key "output_dir" '.[$key]' "$1"); then
#    echo "Key 'outpur_dir' exists in the JSON. Value: $OUTPUR_DIR"
    # Now you can use the $value variable as needed.
#else
#    echo "Key 'output_dir' does not exist in the JSON."
#fi
#exit 0

if [ $OUTPUT_DIR != "null" ]; then
  if [ $VERILATOR_PATH == "null" ]; then 
    VERILATOR_PATH="$OUTPUT_DIR/testbench_verilator"
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
#exit 0

# Create data folders
#mkdir -p data/plots
#mkdir -p data/plotsnew 

# Synthesize the module
#cp replacement_files/run_top.ys run_top.ys

#cp replacement_files/state.v state.v
#cp replacement_files/decoder.v decoder.v
#



#if [ ${SYNTH_SHORT_SUBMODULE_NAME} = "decoder" ]; then 
#  sed -i "s/(\* keep_hierarchy \*)//g" state.v
#  sed -i "s/(\* keep_hierarchy \*)//g" cpuregs.v
#elif [ ${SYNTH_SHORT_SUBMODULE_NAME} = "cpuregs" ]; then 
#  sed -i "s/(\* keep_hierarchy \*)//g" state.v
#  sed -i "s/(\* keep_hierarchy \*)//g" decoder.v
#else
#  sed -i "s/(\* keep_hierarchy \*)//g" decoder.v
#  sed -i "s/(\* keep_hierarchy \*)//g" cpuregs.v
#fi


#sed -i "s/SYNTH_SUBMODULE/$SYNTH_SUBMODULE/g" run_top.ys
#sed -i "s/SYNTH_SHORT_SUBMODULE_NAME/$SYNTH_SHORT_SUBMODULE_NAME/g" run_top.ys
#yosys -s run_top.ys

cd ../ibex-private/

cp rtl/gold/ibex_alu.sv rtl/
cp rtl/gold/ibex_decoder.sv rtl/
cp rtl/gold/ibex_register_file_ff.sv rtl/
cp rtl/gold/ibex_prefetch_buffer.sv rtl/
cp rtl/gold/ibex_load_store_unit.sv rtl/

if [ ${ECC_ON} == "null" ]; then
  echo "No ECC choice set"
  exit -1
elif [ ${ECC_ON} = 1 ]; then
  cp rtl/gold/ibex_register_file_ff_ecc.sv rtl/ibex_register_file_ff.sv
else
  cp rtl/gold/ibex_register_file_ff.sv rtl/ibex_register_file_ff.sv
fi

if [[ ${SYNTH_SHORT_SUBMODULE_NAME} == "decoder" ]]; then 
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_alu.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_register_file_ff.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_load_store_unit.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_prefetch_buffer.sv
elif [[ ${SYNTH_SHORT_SUBMODULE_NAME} == "register" ]]; then 
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_alu.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_decoder.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_load_store_unit.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_prefetch_buffer.sv
elif [[ ${SYNTH_SHORT_SUBMODULE_NAME} == "alu" ]]; then 
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_decoder.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_register_file_ff.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_load_store_unit.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_prefetch_buffer.sv
elif [[ ${SYNTH_SHORT_SUBMODULE_NAME} == "prefetch" ]]; then 
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_decoder.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_load_store_unit.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_register_file_ff.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_alu.sv
elif [[ ${SYNTH_SHORT_SUBMODULE_NAME} == "loadstore" ]]; then 
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_decoder.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_register_file_ff.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_alu.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_prefetch_buffer.sv
elif [[ ${SYNTH_SHORT_SUBMODULE_NAME} == "" ]]; then
  echo "Doing full chip!"
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_decoder.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_register_file_ff.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_alu.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_prefetch_buffer.sv
  sed -i "s/(\* keep_hierarchy \*)//g" rtl/ibex_load_store_unit.sv
fi

cd syn/

rm -rf syn_out/*
#rm -rf build_tmp/*

cp tcl/gold/yosys_run_synth.tcl tcl/yosys_run_synth.tcl
sed -i "s/SYNTH_SUBMODULE_REPLACE_HERE/$SYNTH_SUBMODULE/g" tcl/yosys_run_synth.tcl
sed -i "s/SYNTH_SHORT_SUBMODULE_NAME/$SYNTH_SHORT_SUBMODULE_NAME/g" tcl/yosys_run_synth.tcl

echo "Calling syn scripts!"

bash syn_setup.sh
bash syn_yosys.sh

cd ../../testbench/
rm -rf build_tmp/
mkdir -p syn_out
mkdir -p build_tmp

cp ../ibex-private/syn/syn_out/*/generated/ibex_top_netlist.v syn_out/. 
cp ../ibex-private/syn/syn_out/*/generated/ibex_top_netlist_attr.v syn_out/ 


if [[ ${SYNTH_SHORT_SUBMODULE_NAME} != "" ]]; then
  cp ../ibex-private/syn/syn_out/*/generated/ibex_top_submodule_netlist.v syn_out/.
  cp ../ibex-private/syn/syn_out/*/generated/ibex_top_submodule_netlist_attr.v syn_out/
fi

#exit 0 
python3 ../../../util_scripts/genNegEdgeFlops.py syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_negedge.v clk_i
mv syn_out/ibex_top_negedge.v syn_out/ibex_top_netlist_attr.v



sed -i 's/\\$paramod[^\\]*\\//g' syn_out/*.v
sed -i 's/\\RV32B=s32'\''00000000000000000000000000000000//g' syn_out/*v
sed -i 's/ibex_prefetch_buffer \\u_ibex_core.if_stage_i.gen_prefetch_buffer.prefetch_buffer_i/ibex_prefetch prefetch/g' syn_out/*.v
sed -i 's/ibex_prefetch_buffer/ibex_prefetch/g' syn_out/*.v
sed -i 's/ibex_alu  \\u_ibex_core.ex_block_i.alu_i/ibex_alu alu/g' syn_out/*.v
sed -i 's/ibex_loadstore \\u_ibex_core.load_store_unit_i/ibex_loadstore loadstore/g' syn_out/*.v
sed -i 's/ibex_decoder  \\u_ibex_core.id_stage_i.decoder_i/ibex_decoder decoder/g' syn_out/*.v
sed -i 's/ibex_register_file_ff  \\gen_regfile_ff.register_file_i/ibex_register_file_ff register/g' syn_out/*.v
sed -i 's/ibex_register_file_ff/ibex_register/g' syn_out/*.v
#if [ ${SYNTH_SHORT_SUBMODULE_NAME} != ""]; then
#sed -i 's/\\$paramod[^\\]*\\//g' syn_out/ibex_top_netlist.v syn_out/ibex_top_submodule_netlist.v syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_submodule_netlist_attr.v
#sed -i 's/\\RV32B=s32'\''00000000000000000000000000000000//g' syn_out/ibex_top_netlist.v syn_out/ibex_top_submodule_netlist.v syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_submodule_netlist_attr.v
#sed -i 's/  ibex_prefetch_buffer  \\u_ibex_core.if_stage_i.gen_prefetch_buffer.prefetch_buffer_i/ibex_prefetch_buffer prefetch/g' syn_out/ibex_top_netlist.v syn_out/ibex_top_submodule_netlist.v syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_submodule_netlist_attr.v
#sed -i 's/ibex_alu  \\u_ibex_core.ex_block_i.alu_i/ibex_alu alu/g' syn_out/ibex_top_netlist.v syn_out/ibex_top_submodule_netlist.v syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_submodule_netlist_attr.v
#sed -i 's/ibex_decoder  \\u_ibex_core.id_stage_i.decoder_i/ibex_decoder decoder/g' syn_out/ibex_top_netlist.v syn_out/ibex_top_submodule_netlist.v syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_submodule_netlist_attr.v
#sed -i 's/ibex_register_file_ff  \\gen_regfile_ff.register_file_i/ibex_register_file_ff register/g' syn_out/ibex_top_netlist.v syn_out/ibex_top_submodule_netlist.v syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_submodule_netlist_attr.v
#sed -i 's/ibex_register_file_ff/ibex_register/g' syn_out/ibex_top_netlist.v syn_out/ibex_top_submodule_netlist.v syn_out/ibex_top_netlist_attr.v syn_out/ibex_top_submodule_netlist_attr.v
pushd .

cd ../../
#./make_firmware.sh
popd
#echo "Output dir $OUTPUT_DIR"
cp $HEX_PAYLOAD $OUTPUT_DIR/$(basename $HEX_PAYLOAD)
cp $1 $OUTPUT_DIR/config.dict
## Run to generate required files
cp src/sim_main.cpp build_tmp/sim_main.template.cpp
make from_template
./build_tmp/testbench_verilator_dir_out/Vsim_top +vcd +firmware="../../benchmarks/hello_vincent/hello_vincent.hex" +timeout=200000
#cd -
#cp testbench.vcd .
cp -r syn_out $OUTPUT_DIR/syn_out
python3 ../../../dump_circuit.py $1
./scripts/rebuild_verilator_testbench.sh $1
#./rebuild_verilator_testbench.sh $1
