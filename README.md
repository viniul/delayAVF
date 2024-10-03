# Artifact For: DelayAVF: Calculating Architectural Vulnerability Factors for Delay Faults
This is the artifact for DelayAVF: Calculating Architectural Vulnerability Factors for Delay Faults, paper [here](https://people.csail.mit.edu/mengjia/data/2024.MICRO.DelayAVF.pdf). The artifact contains the SDF-injection framework, scripts to synthesize and analyze the Ibex core, and the source code for the benchmarks. A dockerfile to run the pipeline is included for convenience. Note the ibex submodule, so please run `git submodule init && git submodule update` initially.

## Contained  Code:

* The benchmarks are in `tests/benchmarks/ported_beebs_benchmarks/`
* Python scripts to parse RTL into a json-description of a circuit
* An SDF-injection framework that takes as input json-description of a circuit and a config file describing the fault injection campaign, and output dynamically reachable sets (in `delayFaultSimulatorRust`)
* Python scripts and an ibex testbench that takes dynamically reachable sets as inputs, and computes a structure's AVF value. 


## Analyzing the Ibex Core 

To analyze the DelayFaultAVF of a given Ibex structure with respect to a certain benchmark, run the following code:
1. First, run `git submodule init && git submodule update` and then  build and launch the docker container through the script `./build_and_run_docker.sh`. You will be dropped into a docker shell. 
2. Now, cd into `tests/ibex/testbench/`. 
3. Pick a configuration that you want to run. A configuration is a json file, describing the parameters of the fault injection campaign like so. The micro configuration files are provided in 
`tests/ibex/testbench/configs/beeps`. The configuration file to be read as follows:
```
{
    "synth_file": "syn_out/ibex_top_netlist.v", //Temporary output files
    "sub_synth_file": "syn_out/ibex_top_submodule_netlist.v",
    "submodule_name": "ibex_decoder", // The structure that should be analyzed
    "short_submodule_name": "decoder",
    "pdk_path": "../../../tech_libraries/nangate45/lib/NangateOpenCellLibrary_typical_nocomplex.lib", //The pdk
    "top_path": "TOP.sim_top.dut.cpu.cpu.",
    "clk_path": "TOP.sim_top.dut.cpu.cpu.clk_i",
    "hex_payload": "../../benchmarks/ported_beebs_benchmarks/md5.hex", //The benchmark that we want to run
    "delay_range": [ //What length of delays to compute the AVF for. This list is to comput the delayAVF with respect to 10%,20%, ..,90% delay
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9
    ],
    "percent_sampled_cycles_delay": 4, //Sampling rate for the injected delayFaults
    "percent_sampled_cycles_particle": 50,
    "ecc_on": 0,
    "output_dir": "beeps_benchmark_data/results/md5/decoder/" //Output folder
}
```
4. To evaluate a structure's delayAVF, execute the `run_all.sh <path-to-config.json>` script in the `tests/ibex/testbench` directory.
For example, to compute the decoder's DelayAVF with respect to the md5 benchmark, run:
```
./run_all.sh configs/beeps/md5_decoder.dict
```
Roughly, the framework follows the following workflow: 
* First, synthesize the Ibex core into RTL, using the freepdk-45nm library and build the benchmarks.
* Then, cconvert the RTL into a json representation.
* Call the rust SDF injector to determine dynamically reachable sets.
* Use a verilator testbench to determine groupACEness and aggregate the results.
5. The results will be stored in `<output_dir>/protection_rates.json`, e.g., `tests/ibex/beeps_benchmark_data/results/md5/decoder/protection_rates.json`. To be read as:
```
{
  "delayavf_per_delay": {
    "184": { // Discretized length of injected delay
      "delayAVF": 0,
    },
    "1656": {
      "delayAVF": 0.012679360419095308, //DelayAVF value
    }
  },
  "clk_period": 1840, //Discretized length of the clock period.
}
```
6. you can compute the delayAVF of multiple structure/benchmark combinations and compare the results.
