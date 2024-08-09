import hashlib
import tqdm
import json
import collections
import sys
import injector.params
import matplotlib.pyplot as plt
import csv
import pandas as pd
from injector import util
from injector import vcdTrace
from injector.aceNessAnalyser import AceNessAnalyser
import os
import argparse
from injector.avfCalculator import AVFCalculator
from injector import custom_types
import itertools
from multiprocessing.pool import ThreadPool
import multiprocessing
from injector import params



PLOT_DELAY = '15'

def dict_to_csv(data_dict, csv_file):
    # Extract headers from the dictionary
    headers = ["FlopName", "EdgeInducedFault"]
    #headers = list(data_dict.keys())

    # Extract values from the dictionary
    #values = list(data_dict.values())

    # Create a list of dictionaries with key-value pairs
    #rows = {}
    #print("Ros", rows)
    rows = [{"FlopName": key, "EdgeInducedFault": value} for (key, value) in data_dict.items()]

    # Write dictionary data to CSV file
    with open(csv_file, 'w', newline='\n') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print("Conversion completed successfully!")

class FitReductionAnalyzer():
    def __init__(self, config_dict):
        self.config_dict = config_dict
        #self.fault_injection_result_file_path = fault_injection_result_file_path
        #self.uniform_file_path = uniform_file_path
        self.aceness_analyser = AceNessAnalyser.from_config_dict(config_dict)
        circuit_out_fp = util.get_circuit_out_path_from_config_dict(config_dict)#self.config_dict["circuit_out_fp"]
        with open(circuit_out_fp) as fp:
            self.circuit_out = json.load(fp)
        vcdtrace_fp = util.get_json_vcdtrace_path_from_config_dict(config_dict)
        with open(vcdtrace_fp) as fp:
            ret_dict = json.load(fp)
            self.inject_into_cycles_delay = [str(x) for x in ret_dict["inject_into_cycles"]]
            total_cycles = ret_dict["total_cycles"]
        precent_cycles_particle = float(config_dict["percent_sampled_cycles_particle"]) / 1000.0
        
        #percent_cycles_particle = float(config_dict["percent_sampled_cycles_particle"]) / 1000.0
        fault_cadence = int(total_cycles / (total_cycles * precent_cycles_particle))
        self.inject_into_cycles_particle = list(range(1,total_cycles,fault_cadence))
        timing_metadata_path = util.get_timing_metadata_path_from_config_dict(config_dict)
        with open(timing_metadata_path) as fp:
            self.timing_metadata = json.load(fp)
        self.thread_pool = ThreadPool(params.NJOBS)

    def __del__(self):
        if self.thread_pool:
            self.thread_pool.close()
            del self.thread_pool

    def recalculate_aceness_with_flop_protection(self,protected_flops):
        #self.aceness_analyser.set_protected_flops(protected_flops)
        self.aceness_analyser.run_analysis()
        res = self.aceness_analyser.get_result()
        return res
        #print("Dumping result to", outfile)
        #self.aceness_analyser.dump_result(outfile)
        #exit(0)

    def get_structure_avf_with_flops_protected(self, protected_flops):
        #outfile_path = config_dict["out"]
        #flop_list_sorted = ",".join(sorted(protected_flops))
        #res = self.recalculate_aceness_with_flop_protection(protected_flops)
        #delay_fault_results = custom_types.DelayFaultResults(res)
        #print("Recaculating structure")
        avf_calculator: AVFCalculator = self.avf_calculator #AVFCalculator(delay_fault_results, self.aceness_analyser, self.interesting_flops, self.relevant_wires, self.inject_into_cycles_delay, self.inject_into_cycles_particle)
        #avf_calculator.set_protected_flops(protected_flops)
        #avf_calculator.set_protected_flops(set(()))
        #new_wire_avf = avf_calculator.recompute_wire_avf_with_protection(original_wire_avf, protected_flops)
        #structure_avf = avf_calculator.get_structure_delay_avf_through_sum(provided_wire_avf=new_wire_avf)
        #avf_calculator.set_protected_flops(set(()))
       
        structure_avf = avf_calculator.adjust_structure_delay_avf_with_flop_protection(protected_flops)
        #print("Relcaulting with", protected_flops, "avf", structure_avf)
        return protected_flops, structure_avf
        #if len(flop_list_sorted)>=os.pathconf('/', 'PC_NAME_MAX'):
        #hash_digest = hashlib.sha256(flop_list_sorted.encode("utf-8")).hexdigest()
        #results_path = outfile_path+"_results_protected_flops_"+str(len(protected_flops))+"_protected_"+hash_digest+".json"
        #if not os.path.exists(results_path) or retry:
        #    self.recalculate_aceness_with_flop_protection(results_path, protected_flops)
        #print("Getting results ", results_path)
        #analysis_result_protected_flops: util.AnalysisResult = util.parse_result_json_to_dict_only_wire_avf(results_path) # we need only to compute the edge AVF
        #analysis_result_protected_flops.parse_uniform_result_json_to_dict(uniform_file_path)
        #analysis_result_protected_flops.normalize_delay_results()
        #analysis_result_protected_flops.normalize_uniform_res()
        #analysis_result_protected_flops.calculate_independent_individual_ace()
        #analysis_result_protected_flops.calculate_independent_or_ace()
        #analysis_result_protected_flops.remove_missing_flops()
        #delay = str(max([int(x) for x in analysis_result_protected_flops.all_delays]))
        #new_structure_fit_rate = analysis_result_protected_flops.get_structure_fit(delay)
        #return new_structure_fit_rate

    def get_new_avf_for_each_single_flop(self, flops, protected_so_far=None):
        #raise Exception("Do not call this method")
        if protected_so_far is None:
            protected_so_far = set()
        new_avf = {}
        jobs = [protected_so_far.union({f}) for f in flops if f not in protected_so_far]
        
        #with self.
        #res = 
        for ret_flops, structure_avf in tqdm.tqdm(self.thread_pool.imap(self.get_structure_avf_with_flops_protected, jobs)): #self.thread_pool.imap(lambda f: self.get_structure_avf_with_flops_protected(protected_so_far.union({f})),[f for f in flops if f not in protected_so_far]):
            #f = flops.pop()
            f = ret_flops.pop()
            new_avf[f] = structure_avf
            
        #for f in flops:
        #    new_avf[f] = self.get_structure_avf_with_flops_protected([f], delay_fault_results,original_wire_avf)
        return new_avf
    

    def get_next_best_flop(self, protected_so_far):
        avf_per_protected_flop = self.get_new_avf_for_each_single_flop(self.interesting_flops, protected_so_far)
        #print(avf_per_protected_flop)
        min_flop = min(avf_per_protected_flop, key=avf_per_protected_flop.get)
        #print("max_flop", max_flop, avf_per_protected_flop[max_flop])
        return min_flop #max(avf_per_protected_flop, key=avf_per_protected_flop.get)
    
    def get_fit_reduction_data(self):
        result = {}
        #print("Getting original fit rate", flush=True)
        #original_fit_rate = self.avf_calculator.get_structure_delay_avf_through_sum()
        #percent = 0
        #protected_wires =  self.avf_calculator.get_x_highest_wires(int(len(self.relevant_wires)*(percent/100)), method='WireAVF')
        #print("Protected wires", protected_wires)
        #new_fit_rate =  self.avf_calculator.get_structure_delay_avf_through_sum(protected_wires)
        #print("New avf rate", new_fit_rate, "original", original_fit_rate)
        #exit(0)
        #print("Orignial fit rate", original_fit_rate)
        #print("Getting wireavf done")

        #exit(0)
        #print("GEtting particle strike AVF")
        #self.avf_calculator.get_particle_strike_avf_per_flop()
        #self.avf_calculator.get_particle_strike_avf()
        #original_particle_strike_structure_avf = self.avf_calculator.get_structure_particle_strike_avf()
        #print("Particle strike avf", original_particle_strike_structure_avf)
        #single_flop_micro_arch_approx_avf = 0 # self.avf_calculator.get_micro_arch_wire_avf_approximation(approx_type="single_flops")
        #print("Single flop single_flop_micro_arch_approx", single_flop_micro_arch_approx_avf)
        #print("fan_out_micro_arch_approx_avf", fan_out_micro_arch_approx_avf)
        #exit(0)
        #flop_groups = self.circuit_out["flop_groups"]
        #for g in flop_groups:
            #print("Intersection, ", set(flop_groups[g]), self.interesting_flops)
        #    flop_groups[g] = list(set(flop_groups[g]).intersection(self.interesting_flops)) 
        #print("Getting group avf")
        #per_group_avf = self.avf_calculator.get_avf_for_groups(flop_groups)
        #self.avf_calculator.get_delay_fault_impact_score_per_flop()

        #sorted_group_list = sorted(per_group_avf.keys(), key=lambda x: per_group_avf[x], reverse=True) # Sort descending
        #flops_list_sorted_according_to_micro_groups = [util.process_flop_name(x) for x in itertools.chain(*[flop_groups[group] for group in sorted_group_list])]
      
        #print("Flop list len", len(flops_list_sorted_according_to_micro_groups))
        #print("Getting original fit rate", flush=True)
        #original_fit_rate = self.avf_calculator.get_structure_delay_avf_through_sum()
        #print("Orignial fit rate", original_fit_rate, flush=True)
        #original_particle_strike_structure_avf =  self.avf_calculator.get_structure_particle_strike_avf()
        #result = {"original":  original_fit_rate}
        #result["original_avf_particle_strike_structure"] =  original_particle_strike_structure_avf
        #result["single_flop_micro_arch_approx_avf"] = single_flop_micro_arch_approx_avf
        #result["fan_out_micro_arch_approx_avf"] = fan_out_micro_arch_approx_avf
        if params.SKIP_FIT_REDUCTION == False:
            result["fit_reduction"] = {}
            methods = ["WireAVF", "DelayFaultImpactScore", "ParticleStrikeAVF", "FitReduction"] #["WireAVF", "DelayFaultImpactScore", "ParticleStrikeAVF"]
            DO_AVF_REDUCTION = False
        
            print("Calculate avf per protected flop", flush=True)
            avf_per_protected_flop = self.get_new_avf_for_each_single_flop(self.interesting_flops)
            print("Calculate avf per protected flop done", flush=True)
            flops_ranked_according_to_avf_reduction = sorted(self.interesting_flops, key=lambda flop: avf_per_protected_flop[flop], reverse=False) # Sort ascending
            for method in methods: #"MicroAVF", "FitReduction"]:
                print("Doing Method", method, flush=True)
                result["fit_reduction"][method] = {}
                max_loop_iter = 100
                #protect_flops = self.avf_calculator.get_x_highest_flops(int(len(self.interesting_flops)*(percent/100)), method)
                for percent_int in tqdm.tqdm(range(0,max_loop_iter+1,10)):
                    
                #for percent in tqdm.tqdm(range(0,len(self.interesting_flops))):
                    percent = percent_int/max_loop_iter
                    print("At percent", percent)
                    if method in {"WireAVF"}:
                        #continue
                        protected_wires =  self.avf_calculator.get_x_highest_wires(int(len(self.relevant_wires)*percent), method=method)
                        #print("Protected wires", protected_wires)
                        new_fit_rate =  self.avf_calculator.recompute_structue_delay_avf_with_protected_edges(protected_wires)
                        print("New fit rate", new_fit_rate)
                    elif method in {"DelayFaultImpactScore", "Random", "ParticleStrikeAVF"}:
                        protect_flops = self.avf_calculator.get_x_highest_flops(int(len(self.interesting_flops)*percent), method)
                        #protect_flops = self.avf_calculator.get_x_highest_flops(int(percent), method)
                        _, new_fit_rate = self.get_structure_avf_with_flops_protected(protect_flops )
                    elif method in {"MicroAVF"}:
                        protect_flops = flops_list_sorted_according_to_micro_groups[:int(len(self.interesting_flops)*percent)]
                        #print("Flops protected", protect_flops)
                        _, new_fit_rate = self.get_structure_avf_with_flops_protected(protect_flops  )
                    elif method in {"FitReduction"}:
                        #raise Exception("Not implemented right now!")
                        protect_flops = flops_ranked_according_to_avf_reduction[:int(len(self.interesting_flops)*(percent))]
                        _, new_fit_rate = self.get_structure_avf_with_flops_protected(protect_flops )
                    else:
                        raise Exception(f"Method {method} not implemented")
                    result["fit_reduction"][method][percent] = new_fit_rate
                    print("At percent", percent, "method", method, "num protected flops", int(len(self.interesting_flops)*percent), "avf", new_fit_rate)
                    if new_fit_rate <= 0+sys.float_info.epsilon:
                        break
            
            greedy_algorithm_result = []
            if DO_AVF_REDUCTION == True:
                result["fit_reduction"]["AvfReductionGreedy"] = {}
                idx = 0
                protected_flops_so_far = set()
                remaining_flops = set(self.interesting_flops)
                current_avf = original_fit_rate
                result["fit_reduction"]["AvfReductionGreedy"][idx / len(self.interesting_flops)] = current_avf
                pbar = tqdm.tqdm(total=len(self.interesting_flops))
                while current_avf >= 0+sys.float_info.epsilon:
                    next_flop = self.get_next_best_flop(protected_flops_so_far)
                    protected_flops_so_far.add(next_flop)
                    next_flop = self.get_next_best_flop(remaining_flops, protected_flops_so_far)
                    protected_flops_so_far.add(next_flop)
                    print("Protected flops so far", protected_flops_so_far)
                    _, current_avf = self.get_structure_avf_with_flops_protected(protected_flops_so_far)
                    greedy_algorithm_result.append((next_flop, current_avf))
                    idx += 1
                    print("current_avf", current_avf)
                    result["fit_reduction"]["AvfReductionGreedy"][idx / len(self.interesting_flops)] = current_avf
                    remaining_flops.remove(next_flop)
                    pbar.update(1)
                pbar.close()
            result["flop_lists"] = {}
            for method in  ["DelayFaultImpactScore", "ParticleStrikeAVF", "AvfReductionGreedy"]:# "MicroAVF", "FitReduction"]: #["DelayFaultFlopAVF", "Random", "WireAVFProtectFlops", "DelayFaultFlopAVFStaticReachability", "Uniform"]: #Also do a static analysis but protecting wires according to the static analysis
                percent = 100
                if method in {"DelayFaultImpactScore", "Random", "ParticleStrikeAVF"}:
                    protect_flops = self.avf_calculator.get_x_highest_flops(int(len(self.interesting_flops)*(percent/100)), method)
                    if method=="Random":
                        continue
                    ranking_dict = None #Which dict do we use to rank flops?
                    if method=="DelayFaultImpactScore": #Group-Ace
                        ranking_dict = self.avf_calculator.delay_fault_impact_score
                        
                    elif method=="ParticleStrikeAVF":
                        ranking_dict = self.avf_calculator.particle_strike_avf
                    protect_flops = [(f, ranking_dict[f]) for f in protect_flops]
                elif method == "MicroAVF":
                    protect_flops = {"Groups": [(g, per_group_avf[g]) for g in sorted_group_list], "FlopsList": flops_list_sorted_according_to_micro_groups}
                elif method == "AvfReductionGreedy":
                    #raise Exception("Not implemented right now!")
                    protect_flops = greedy_algorithm_result#[(f, fit_per_protected_flop[f]) for f in flops_ranked_according_to_avf_reduction]
                else:
                    raise Exception(f"Method {method} not implemented")
                result["flop_lists"][method] = protect_flops
        #print("Calculating ACE compounding rates", flush=True)
        
        #strong_ace_compounding, weak_ace_compounding, ace_interference = self.avf_calculator.ace_compounding_rate()
        #result["strong_ace_compounding"] = strong_ace_compounding
        #result["weak_ace_compounding"] = weak_ace_compounding
        #result["ace_interference"] = ace_interference
        return result

    def analyze_results_for_delay(self, delay: int):
        delay_results_for_delay = self.delay_fault_results.get_edge_results_for_delay(delay)
        self.avf_calculator: AVFCalculator = AVFCalculator(delay_results_for_delay, self.aceness_analyser, self.interesting_flops, self.relevant_wires, self.inject_into_cycles_delay, self.inject_into_cycles_particle)
        #self.avf_calculator.get_particle_strike_avf_per_flop()
        print(f"Getting AVFs for delay {delay}", flush=True)
        #fan_out_micro_arch_approx_avf = 0 #self.avf_calculator.get_micro_arch_wire_avf_approximation(approx_type="fan_out", flops_list=self.circuit_out["flops"], paths=delay_fault_results.paths)
        #print("fan_out_micro_arch_approx_avf", fan_out_micro_arch_approx_avf)
        original_wire_avf_dict = self.avf_calculator.get_wire_avf()
        wire_avf_scalar = self.avf_calculator.get_structure_delay_avf_through_sum()
        wire_avf_or_ace_scalar = self.avf_calculator.get_structure_delay_avf_or_ace()
        wire_avf_savf_approx = self.avf_calculator.get_structure_delay_avf_savf_approx()
        wire_avf_independent_approx = None #self.avf_calculator.get_structure_delay_avf_independent_approx()
        result = {}
        result["delayAVF"] = wire_avf_scalar
        result["delayAVFOrAce"] = wire_avf_or_ace_scalar
        result["delayAVFSAVFApprox"] = wire_avf_savf_approx
        result["delayAVFIndependentApprox"] = wire_avf_independent_approx
        strong_ace_compounding, weak_ace_compounding, ace_interference = self.avf_calculator.ace_compounding_rate()
        result["strong_ace_compounding"] = strong_ace_compounding
        result["weak_ace_compounding"] = weak_ace_compounding
        result["ace_interference"] = ace_interference
        return result


    # def get_next_best_flop(self, out_of_flops, protected_so_far):
    #    #jobs = [(f, protected_so_far.union({f}) for f in out_of_flops]
    #     min_so_far = None
    #     for (flop, ret_val) in self.thread_pool.imap(lambda f: (f, self.get_structure_avf_with_flops_protected(protected_so_far.union({f}))), out_of_flops):
    #         #print(ret_val)
    #         ret_flops, structure_avf = ret_val
    #         if min_so_far is None:
    #             min_so_far = structure_avf
    #         if structure_avf < min_so_far:
    #             min_so_far = structure_avf
    #             min_flop = flop #ret_flops.pop()
    #     #avf_per_protected_flop = self.get_new_avf_for_each_single_flop(self.interesting_flops, protected_so_far)
    #     #print(avf_per_protected_flop)
    #     #min_flop = min(avf_per_protected_flop, key=avf_per_protected_flop.get)
    #     print("min_flop", min_flop, min_so_far)
    #     return min_flop #max(avf_per_protected_flop, key=avf_per_protected_flop.get)

    def compute_particle_strike_avf(self):
        print("Getting particle strike AVF")
        avf_calculator: AVFCalculator = AVFCalculator(None, self.aceness_analyser, self.interesting_flops, None, None, self.inject_into_cycles_particle)
        avf_calculator.get_particle_strike_avf_per_flop()
        original_particle_strike_structure_avf = avf_calculator.get_structure_particle_strike_avf()
        #avf_calculator_extern: AVFCalculator = AVFCalculator(None, self.aceness_analyser, self.extern_interesting_flops, None, None, self.inject_into_cycles_particle)
        #avf_calculator_extern.get_particle_strike_avf_per_flop()
        extern_particle_strike_structure_avf = None #avf_calculator_extern.get_structure_particle_strike_avf()
        print("Particle strike avf intern", original_particle_strike_structure_avf, "extern", extern_particle_strike_structure_avf)
        return original_particle_strike_structure_avf, extern_particle_strike_structure_avf
        

    def analyze_results(self, retry=True):
        delay_fi_outfile_path = config_dict.get("delay_injection_results", None)
        if delay_fi_outfile_path is None:
            delay_fi_outfile_path = os.path.join(config_dict["output_dir"], "delay_injection_res.json")
        self.delay_fault_results = custom_types.DelayFaultResults.from_json_path(delay_fi_outfile_path)
        self.interesting_flops = self.circuit_out["interesting_flops"]
        self.extern_interesting_flops = self.circuit_out["extern_interesting_flops"]
        print("Interesting flops", len(self.interesting_flops))
        print("extern Interesting flops", len(self.extern_interesting_flops))
        self.relevant_wires = [(edge[0], edge[1]) for edge in self.circuit_out["inject_into_edges"]]
        
        #self.relevant_wires = []
        #for wire in self.circuit_out["edges"]:
        #    self.relevant_wires.append((wire["from"], wire["to"]))
        print("Number of relevant wires", len(self.relevant_wires))
        print("Number of overall wires", len(self.circuit_out["edges"]))
        result = {}
        result["delayavf_per_delay"] = {}
        for delay in self.delay_fault_results.all_delays:
            result["delayavf_per_delay"][delay] = self.analyze_results_for_delay(delay)
        result["clk_period"] = self.timing_metadata["clk_period"]
        particle_strike_avf_intern, particle_strike_avf_extern = self.compute_particle_strike_avf()
        result["particle_strike_avf_intern"] = particle_strike_avf_intern
        result["particle_strike_avf_extern"] = particle_strike_avf_extern
        
        protection_rates_path = util.get_protection_rates_path(config_dict)
        with open(protection_rates_path, "w") as fp:
            json.dump(result, fp)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to process a file with optional retry.')

    # Positional argument for the filename
    parser.add_argument('config_filename', help='The name of the file to process')
    # Optional argument for retry
    parser.add_argument('--retry', action='store_true', help='Enable retry option')

    args = parser.parse_args()

    # Access the arguments
    config_filename = args.config_filename
    retry = args.retry

    with open(config_filename) as fp:
        config_dict = json.load(fp)
    #uniform_fault_result = config_dict["uniform_out"]
    fit_reduction_analyzer = FitReductionAnalyzer(config_dict)
    fit_reduction_analyzer.analyze_results()


