import sys
import json
import numpy as np
from injector import params
import os
from injector import circuit
import tqdm
from injector import util
from injector import vcdTrace


def main():
    with open(sys.argv[1]) as fp:
        config_dict = json.load(fp)
    output_dir_basepath = config_dict.get("output_dir", None)
    synth_file = os.path.join(output_dir_basepath, config_dict["synth_file"])
    sub_synth_file = os.path.join(output_dir_basepath, config_dict["sub_synth_file"])
    if not os.path.exists(synth_file):
        synth_file = config_dict.get("synth_file", None)
        sub_synth_file = config_dict.get("sub_synth_file", None)
    print(f"Using synth file {synth_file}")
    submodule_name = config_dict.get("submodule_name", None)
    short_submodule_name = config_dict.get("short_submodule_name", None)
    pdk_path = config_dict["pdk_path"]
    #trace_path = config_dict["trace_path"]
    top_path = config_dict["top_path"]
    clk_path = config_dict["clk_path"]
    hex_payload = config_dict["hex_payload"]
    use_fuse_soc = config_dict.get("use_fuse_soc", False)
    #outfile_path = config_dict.get("out", "fault_scenarios.json")
    add_global_delay = config_dict.get("add_global_delay", True) # False to add relative delay
    delay_min = float(config_dict.get("delay_min", 0.1))
    delay_max = float(config_dict.get("delay_max", 1))
    delay_range_step = config_dict.get("delay_range_steps")
    #verilator_timeout = config_dict["verilator_timeout"]
    
    circuit_out_path = config_dict.get("circuit_out_fp", None)
    if circuit_out_path is None:
        if output_dir_basepath is None:
            raise Exception("Output dir basepath is None")
        circuit_out_path = os.path.join(output_dir_basepath, "circuit_out.json")
    circuit_out_path_full = os.path.join(output_dir_basepath, "circuit_out_full.json")
    json_vcdtrace_path = config_dict.get("json_vcdtrace_fp", None)
    if json_vcdtrace_path is None:
        if output_dir_basepath is None:
            raise Exception("Output dir basepath is None")
        json_vcdtrace_path = os.path.join(output_dir_basepath, "dump_vcdtrace.json")
    metadata_json_path = util.get_metadata_path_from_config_dict(config_dict)
    trace_path = util.get_testbench_vcdtrace_path_from_config_dict(config_dict) # os.path.join(output_dir_basepath, "testbench_trace.vcd")
    #pickle_path = config_dict.get("circuit_pickle_path", None)
    params.ADD_ABSOLUTE_DELAY = add_global_delay
    params.DELAY_FAULT_RANGE = None # np.linspace(delay_min,delay_max,delay_range_step)
    #params.VERILATOR_TIMEOUT = verilator_timeout
    print("Loading circuit")
    delay_circuit = circuit.delayCircuit(synth_file, pdk_path, sub_synth_file, submodule_name, just_dump=True)
    print("Preparing circuit")
    delay_circuit.prepare()
    os.makedirs(os.path.dirname(circuit_out_path), exist_ok=True)
    delay_circuit.dump_circuit_to_json(circuit_out_path_full)
    delay_circuit.pruneExternalNodes()
    delay_circuit.dump_circuit_to_json(circuit_out_path)
    
    #print("Longest path", delay_circuit.calculate_path_lengths()[1])
    #return

    util.generate_trace_with_verilator_subcall(hex_payload,trace_path, params.VERILATOR_MAX_TIMEOUT, use_fuse_soc=use_fuse_soc)
    tr = vcdTrace.vcdTrace(trace_path, top_path, clk_path)
    # self.tr = trace.Trace("verilator_simulation/trace.vcd",
    #                      "TOP.servant_sim.dut.cpu.cpu.decode.", "TOP.servant_sim.dut.cpu.cpu.clk")
    elements = list(delay_circuit.c.outputs()) + \
        list(delay_circuit.c.inputs())
    flops = []
    # Map the elements in our circuit to those in the vcd trace 
    for circuit_element in elements:
        flop_name = util.circuitgraph_to_vcd_flop_name(circuit_element, short_submodule_name)
        flops.append(flop_name)
    all_flops = flops
    all_elements = elements
    flop_trace = {}
    total_cycles = tr.getNumCycles()
    #total_cycles = config_dict["total_cycles"]
    #fault_cadence = config_dict["fault_cadence"]
    percent_cycles_delay = float(config_dict["percent_sampled_cycles_delay"]) / 100.0
    fault_cadence = int(total_cycles / (total_cycles * percent_cycles_delay))
    with open(metadata_json_path, "w") as fp:
        metadata = {}
        metadata["verilator_timeout"] = tr.timeout()
        metadata["max_cycles"] = tr.getNumCycles()
        metadata["inject_into_cycles_len"] = len(list(range(1,total_cycles,fault_cadence)))
        json.dump(metadata, fp)
    #flop_to_int_mapping = {flop_name: idx}
    #for idx, name in tqdm.tqdm(enumerate(elements)):
    #    flop_trace[idx] = {}
    #    flop_to_int_mapping[name] = idx
    #for cycle in range(1,tr.getNumCycles(),max(int(tr.getNumCycles()/params.NUM_SIM_CYCLES),1)):
    for cycle in range(1,total_cycles,fault_cadence):
        #Make sure all flop values are cached
        flop_values_this_cycle = tr.getFlopStates(all_flops, all_elements, cycle)
        flop_values_prior_cycle = tr.getFlopStates(all_flops, all_elements, cycle-1)
        #flop_values_this_cycle["tie_0"] = 0
        #flop_values_this_cycle["tie_1"] = 1
        flop_trace[cycle] = {key: int(value) for (key, value) in flop_values_this_cycle.items()}
        flop_trace[cycle-1] = {key: int(value) for (key, value) in flop_values_prior_cycle.items()}
    vcdtrace_object = {}
    vcdtrace_object["inject_into_cycles"] = list(range(1,total_cycles,fault_cadence)) #list(range(1,tr.getNumCycles(),max(int(tr.getNumCycles()/params.NUM_SIM_CYCLES),1)))
    vcdtrace_object["flop_values"] = flop_trace
    vcdtrace_object["total_cycles"] = total_cycles
    with open(json_vcdtrace_path, "w") as fp:
        json.dump(vcdtrace_object, fp)

if __name__=="__main__":
    main()
