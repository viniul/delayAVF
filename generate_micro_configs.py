import json
#import calculateFitDecreaseNew

base_config_pico = {
  "synth_file": "picorv32_synth.v",
  "sub_synth_file": "picorv32_{module}_synth.v",
  "submodule_name": "picorv32_{module}",
  "short_submodule_name": "{module}",
  "pdk_path": "../../tech_libraries/NanGate_15nm/NanGate_15nm_OCL_typical_conditional_nldm.lib",
  "top_path": "TOP.picorv32_wrapper.uut.picorv32_core.",
  "clk_path": "TOP.picorv32_wrapper.uut.picorv32_core.clk",
  "hex_payload": "benchmarks/ported_beebs_benchmarks/{benchmark}.hex",
  "delay_range": [0.5, 0.7, 0.9],
  "percent_sampled_cycles_delay": 2,
  "percent_sampled_cycles_particle": 1,
  "ecc_on": 0,
  "output_dir": "beeps_benchmark_data/results/{benchmark}/{module}/"
}


base_config_ibex = {
  "synth_file": "syn_out/ibex_top_netlist.v",
  "sub_synth_file": "syn_out/ibex_top_submodule_netlist.v",
  "submodule_name": "ibex_{module}",
  "short_submodule_name": "{module}",
  "pdk_path": "../../../tech_libraries/nangate45/lib/NangateOpenCellLibrary_typical_nocomplex.lib",
  "top_path": "TOP.sim_top.dut.cpu.cpu.",
  "clk_path": "TOP.sim_top.dut.cpu.cpu.clk_i",
  "hex_payload": "../../benchmarks/ported_beebs_benchmarks/{benchmark}.hex",
  "delay_range": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
  "percent_sampled_cycles_delay": 4,
  "percent_sampled_cycles_particle": 50,
  "ecc_on": 0,
  "output_dir": "beeps_benchmark_data/results/{benchmark}/{module}/"
}


def main():
    for module_name in ["decoder", "alu", "register", "prefetch", "loadstore"]: #["decoder", "state", "cpuregs"]:
        for benchmark in ["md5", "libstrstr", "libcrc", "libbubblesort", "libfibcall"]: #"md5", "libcrc", "libbubblesort", "libstrstr", "matmult", "liblevenshtein", "libfibcall", "lzp", "mat_mult"]:
            current_config = base_config_ibex.copy()
            current_config["sub_synth_file"] = current_config["sub_synth_file"].format(module=module_name)
            current_config["submodule_name"] = current_config["submodule_name"].format(module=module_name)
            current_config["short_submodule_name"] = current_config["short_submodule_name"].format(module=module_name)
            if benchmark in {"lzp", "mat_mult"}:
                continue
                current_config["hex_payload"] = f"benchmarks/{benchmark}/{benchmark}.hex"
            else:
                current_config["hex_payload"] = current_config["hex_payload"].format(benchmark=benchmark)
            current_config["output_dir"] = current_config["output_dir"].format(benchmark=benchmark, module=module_name)
            current_config["ecc_on"] = 0 
            with open(f"configs/beeps/{benchmark}_{module_name}.dict", "w") as fp:
                json.dump(current_config, fp, indent=4)
            if module_name == "cpuregs" or module_name == "register":
                ecc_config = current_config.copy() # Doesn't matter whether shallow or deep copy, as we will not reuse currrent_config anyway
                ecc_config["ecc_on"] = 1
                new_module_name = module_name + "_ecc"
                ecc_config["output_dir"] = base_config_ibex["output_dir"].format(benchmark=benchmark, module=new_module_name)
                with open(f"configs/beeps/{benchmark}_{new_module_name}.dict", "w") as fp:
                    json.dump(ecc_config, fp, indent=4)
            #fit_reduction_analyzer = calculateFitDecreaseNew.FitReductionAnalyzer(current_config)
            #fit_reduction_analyzer.analyze_results()
    #for 
            
            
            
            
    
    
if __name__=="__main__":
    main()
