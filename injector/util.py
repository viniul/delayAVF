import random
import networkx as nx
import matplotlib.pyplot as plt
from injector import params
from injector import vcdTrace
import re
import typing
from injector import custom_types
#from injector import plotErrors
import json
import pandas as pd
import subprocess
import os
import shutil
import collections
import datetime
import numpy as np
import scipy
import scipy.stats
import math
import tqdm

#def invoke_verilator(verilator_path, args):
#    pass    

def get_timing_metadata_path_from_config_dict(config_dict):
    return os.path.join(config_dict["output_dir"], "timing_metadata.json")

def get_circuit_out_path_from_config_dict(config_dict):
    return os.path.join(config_dict["output_dir"], "circuit_out.json")

def get_json_vcdtrace_path_from_config_dict(config_dict):
    return os.path.join(config_dict["output_dir"], "dump_vcdtrace.json")

def get_testbench_vcdtrace_path_from_config_dict(config_dict):
    return os.path.join(config_dict["output_dir"], "testbench_trace.vcd")
    
def get_protection_rates_path(config_dict):
    return os.path.join(config_dict["output_dir"], "protection_rates.json")

def get_delay_injection_results_path(config_dict):
    return os.path.join(config_dict["output_dir"], "delay_injection_res.json")
    
def get_verilator_path_from_config_dict(config_dict):
    return os.path.join(config_dict["output_dir"], "testbench_library.so")

def get_metadata_path_from_config_dict(config_dict):
    return os.path.join(config_dict["output_dir"], "metadata.json")

def get_aceness_cache_dir(config_dict):
    return os.path.join(config_dict["output_dir"], "aceness_results_cache")
    
def retain_strings_below_max_length(strings, max_length):
    retained_strings = []
    total_length = 0

    for string in strings:
        if total_length + len(string) <= max_length:
            retained_strings.append(string)
            total_length += len(string)
        else:
            break

    return retained_strings    
    
def get_fanout_for_input_flops(flops, paths, interesting_flops):
    """
    :flops: The list of flops as retrieved by circuit_out.json
    :paths: The list of paths
    """
    input_flops_to_out_flops = {}
    for flop_dict in flops:
        flop_name = None

        if "pins" in flop_dict:
            flop_name = flop_dict["pins"]["Q"]
        else:
            if flop_dict["direction"]=="IN":
                flop_name = flop_dict["name"]
        if flop_name is not None:
            #print("flop_name", process_flop_name(flop_name),process_flop_name(flop_name) in interesting_flops )
            #if process_flop_name(flop_name) in interesting_flops:
            input_flops_to_out_flops[flop_name] = set()
            #circuit.add_node(pin["Q"].to_string(), CellType::InFlop);
    #print(input_flops_to_out_flops)
    #print("Interesting flops", interesting_flops)
    for path in paths:
        if path[0] in input_flops_to_out_flops:
            processed_out_flop_name = process_flop_name(path[1])
            if processed_out_flop_name in interesting_flops:
                input_flops_to_out_flops[path[0]].add(processed_out_flop_name)
    #print("Aggregated inputs", input_flops_to_out_flops)
    print("Vincent: ### Warning: Remove all in-out mappings with len>8000")
    for in_flop in list(input_flops_to_out_flops.keys()):
        if len(",".join(input_flops_to_out_flops[in_flop]))>7000:
            print(f"Vincent: Chopped  fan_out of {in_flop} because fan_out is too large")
            input_flops_to_out_flops[in_flop] = retain_strings_below_max_length(input_flops_to_out_flops[in_flop], 7000)
            #print(f"Vincent: Removing {in_flop} because fan_out is too lrage")
            #del input_flops_to_out_flops[in_flop]
    return input_flops_to_out_flops
            
            

def return_key_to_sorted_index_dict(input_list):
    # Sort the dictionary items by their values
    sotred_list = sorted(enumerate(input_list), key=lambda item: item[1])
    # Create a new dictionary mapping the keys to their positions in the sorted list
    result_dict = {item[0]: index for index, item in enumerate(sotred_list)}

    return result_dict

def rank_order(list1, list2): 
    idx_to_rank_list1 = return_key_to_sorted_index_dict(list1)
    idx_to_rank_list2 = return_key_to_sorted_index_dict(list2)
    result_sum = 0
    for idx in range(len(list1)):
        result_sum += abs(idx_to_rank_list1[idx]-idx_to_rank_list2[idx])
    #Now, need to norm. 
    #Let N=len(list1), then maximum is: 1/2 (N^2-1) if N odd and 1/2 N^2 if N even (see: https://escholarship.org/uc/item/1qc66618#main)
    #On a Distance Function for Ordered Lists by     Siklossy, Laurent 
    max_value = 0
    if len(list1) % 2 == 1:
        max_value = (1/2) * (len(list1)**2-1)
    else:
        max_value = (1/2) * (len(list1)**2)
    return 1-(result_sum/max_value)

def calculate_pairwise_corr(corr_df, method, without_zero=True):
    corr_np = corr_df.to_numpy()  
    correlations_dict = collections.defaultdict(dict)
    #print('{} - Calculating Correlation'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    for col_1 in range(corr_np.shape[-1]):
        for col_2 in range(corr_np.shape[-1]):
            if col_2 >= col_1: #to not calculate duplicates, eg. (A, G) (G, A)
                # to remove rows when both are 0, eg. (0, 0)
                if without_zero is True:
                    numpy_col_1 = corr_np[~((corr_np[:,col_1]==.0) & (corr_np[:,col_2]==.0)),col_1]
                    numpy_col_2 = corr_np[~((corr_np[:,col_1]==.0) & (corr_np[:,col_2]==.0)),col_2]
                else:
                    numpy_col_1 = corr_np[:, col_1]
                    numpy_col_2 = corr_np[:, col_2]
                #print("Numpy col 1", numpy_col_1,"Numpy col 2", numpy_col_2)
                if method=='kendall':
                    cor = scipy.stats.kendalltau(numpy_col_1, numpy_col_2).correlation#.statistic#[-1,0]
                elif method=="rank_order":
                    cor = rank_order(numpy_col_1, numpy_col_2)
                else:
                    if len(numpy_col_1)<=2 or len(numpy_col_2)<=2:
                        cor = float("nan")
                    else:
                        #print("Columns", corr_df.columns[col_1], corr_df.columns[col_2])
                        #print("Numpy col 1", numpy_col_1,"Numpy col 2", numpy_col_2)
                        cor = scipy.stats.pearsonr(numpy_col_1, numpy_col_2).correlation
                #print(cor)
                correlations_dict[corr_df.columns[col_1]][corr_df.columns[col_2]] = cor
                correlations_dict[corr_df.columns[col_2]][corr_df.columns[col_1]] = cor
    res_df = pd.DataFrame([[correlations_dict[col_A][col_B] for col_A in corr_df.columns] for col_B in corr_df.columns], columns=corr_df.columns, index=corr_df.columns)

    #print('{} -\t Finished'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    return res_df

class AnalysisResult():
    def __init__(self, all_delays, all_flops, all_edges, num_cycles, result_dict=None) -> None:
        self.all_delays = all_delays
        self.all_flops = all_flops
        self.edge_list = list(set(all_edges))
        self.num_cycles = num_cycles
        self.static_analysis_res = None
        self.logical_masking_res = None
        self.group_ace_res = None
        self.unique_ace_res = None
        self.uniform_fi_res = None
        self.independent_individual_ace = None
        self.group_sdc = None
        self.unique_sdc = None
        self.edge_avf_per_delay = None
        self.dyn_set_per_edge = {} #Map wires to their dynamically reachable set, ordered by the number of times the flop is dyn reachable
        self.sim_result_per_edge =  collections.defaultdict(lambda: collections.defaultdict(lambda: list))
        self.result_dict = result_dict

    def add_results(self, static_analysis, logical_masking, group_ace, unique_ace, unique_exclusive_ace, or_ace=None, group_sdc=None, unique_sdc=None, union_per_delay_per_flop=None, edge_avf_per_delay=None, per_flop_per_edge_per_delay_count=None):
        self.static_analysis_res = static_analysis
        self.logical_masking_res = logical_masking
        self.group_ace_res = group_ace
        self.unique_ace_res = unique_ace
        self.unique_exclusive_ace = unique_exclusive_ace
        self.or_ace = or_ace
        self.group_sdc = group_sdc
        self.unique_sdc = unique_sdc
        self.union_per_delay_per_flop = union_per_delay_per_flop
        self.edge_avf_per_delay = edge_avf_per_delay
        self.per_flop_per_edge_per_delay_count = per_flop_per_edge_per_delay_count

    def parse_uniform_result_json_to_dict(self, uniform_file_path):
        print("Loading from", uniform_file_path)
        with open(uniform_file_path) as fp:
            result_dict = json.load(fp)
        count_ace_flop = {}
        for delay in result_dict["analysis_results"].keys():
            #count_ace_flop[f] = 0
            for result in result_dict["analysis_results"][delay]:
                for cycle, res in result["dynamically_reachable_per_cycle"].items():
                    if res["ace"] is True:
                        flop = res["dynamically_reachable"][0]
                        if flop not in count_ace_flop:
                            #print("Adding flop", flop)
                            count_ace_flop[flop] = 0
                        count_ace_flop[flop] += 1
        print("Length of uniform_fi_res after parsing", len(count_ace_flop))
        self.uniform_fi_res = count_ace_flop
    
    def get_static_reachability_per_edge(self, delay):
        res_dict = {}
        analysis_result_dict =  self.result_dict["analysis_results"]
        print(analysis_result_dict.keys())
        for sim_result in analysis_result_dict[delay]:
            edge = tuple(sim_result["edge"])
            #ll_edges.append(edge)
            #print("Sim result", sim_result)
            #for cycle, result in sim_result["static_reachable"].items():
            #    if result["ace"]:
            #        edge_avf_per_delay[delay][edge] += 1
            #edge_avf_per_delay[delay][edge] /= params.NUM_SIM_CYCLES
            res_dict[edge] = sim_result["static_reachable"]
            #print("Edge avf per delay", edge_avf_per_delay[delay][edge])
        return res_dict
    

    def normalize_uniform_res(self):
        for flop in self.uniform_fi_res.keys():
            self.uniform_fi_res[flop] /= params.NUM_SIM_CYCLES

    def normalize_delay_results(self):
        for delay in self.all_delays:
            for flop in self.all_flops:
                self.static_analysis_res[delay][flop] /= len(self.edge_list)
                self.logical_masking_res[delay][flop] /= (len(self.edge_list)*self.num_cycles)
                self.group_ace_res[delay][flop] /= (len(self.edge_list)*self.num_cycles)
                self.unique_ace_res[delay][flop] /= (len(self.edge_list)*self.num_cycles)
                self.unique_exclusive_ace[delay][flop] /= (len(self.edge_list)*self.num_cycles)
                for res_dict in [self.or_ace, self.group_sdc, self.unique_sdc]:
                    if res_dict:
                        res_dict[delay][flop] /= (len(self.edge_list)*self.num_cycles)
            for edge in self.edge_list:
                self.per_flop_per_edge_per_delay_count[delay][edge][flop] /= self.num_cycles

    def remove_missing_flops(self):
        for missing_flop in set(self.all_flops).symmetric_difference(self.uniform_fi_res.keys()): #set(self.all_flops)-(set(self.all_flops).intersection(self.uniform_fi_res.keys())):
            for delay in self.all_delays:
                for iter_dict in [self.unique_exclusive_ace[delay], self.static_analysis_res[delay], self.logical_masking_res[delay], self.group_ace_res[delay], self.unique_ace_res[delay], self.or_ace[delay], self.uniform_fi_res, self.unique_sdc[delay], self.group_sdc[delay]]:
                    if iter_dict:
                        if missing_flop in iter_dict:
                            iter_dict.pop(missing_flop)
        #print("Gorup ace keys", self.group_ace_res[delay].keys())
        print("Length of uniform fault injection", len(self.uniform_fi_res.keys()), flush=True)
        print("uniform keys", "pcpi_rs2[16]" in self.uniform_fi_res.keys())
        self.all_flops = list(set(self.all_flops).intersection(self.uniform_fi_res.keys()))
        #print("self all flps", self.all_flops)


    def get_structure_score(self, delay):
        score = 0.0
        for edge, edge_avf in self.edge_avf_per_delay[delay].items():
            #print("Edge", edge, "edge_avf", edge_avf)
            score += edge_avf
        return score

    def get_structure_fit(self, delay, protected_edges=None):
        if protected_edges is None:
            protected_edges = set()
        wire_delay_structure_fit = 0.0
        for edge, edge_avf in self.edge_avf_per_delay[delay].items():
            #print("Get edge avf", edge, edge_avf)
            if edge not in set(protected_edges):
                wire_delay_structure_fit += edge_avf*params.EDGE_FIT
        return wire_delay_structure_fit

    def get_x_highest_flops_according_to_edge_avf(self, delay, num_flops):
        #We do the following: We first rank each edge, then, in this order, fro each edge, 
        #we take it's dynamically reachable set and starting protecting flops from there 
        #until we reached our budget.
        wire_list = list(self.edge_avf_per_delay[delay].keys())
        wire_list = sorted(wire_list, key=lambda x: self.edge_avf_per_delay[delay][x], reverse=True) # Sort descending
        protect_flops = set()
        for wire in wire_list:
            for flop in self.dyn_set_per_edge[delay][wire]:
                if len(protect_flops)>=num_flops:
                    return list(protect_flops)
                protect_flops.add(flop)
        return list(protect_flops)




    def get_x_highest_flops_for_delay(self, delay, num_flops, method='DelayFaultFlopAVF'):
        flop_list = list(self.group_ace_res[delay].keys())
        if method in {'DelayFaultFlopAVF', "DelayFaultFlopAVFOrAceApprox", "DelayFaultFlopAVFMaxAVFApprox", "DelayFaultFlopAVFStaticReachability", "Uniform"}: 
            ranking_dict = None #Which dict do we use to rank flops?
            if method=="DelayFaultFlopAVF": #Group-Ace
                ranking_dict = self.group_ace_res[delay]
            elif method=="DelayFaultFlopAVFStaticReachability":
                ranking_dict = self.static_analysis_res[delay]
            elif method=="Uniform":
                ranking_dict = self.uniform_fi_res
            elif method=="DelayFaultFlopAVFOrAceApprox":
                ranking_dict = self.or_ace[delay]
            elif method=="DelayFaultFlopAVFMaxAVFApprox":
                ranking_dict = self.independent_or_ace[delay]
            flop_list = sorted(flop_list, key=lambda flop: ranking_dict[flop], reverse=True) # Sort descending
            if method=="Uniform":
                print([(f, ranking_dict[f]) for f in flop_list])
        elif method=='Random':
            random.seed(1)
            return random.sample(flop_list, num_flops)
            #random.seed(0)
            #flop_list = 
        else:
            raise Exception(f"Invalid Method selected {method}")
        #print([(f, self.group_ace_res[delay][f]) for f in flop_list])
        return flop_list[:num_flops]

    def get_x_highest_wires_for_delay(self, delay, num_wires, method="WireAVF"):
        wire_list = list(self.edge_avf_per_delay[delay].keys())
        if method=="WireAVF":
            wire_list = sorted(wire_list, key=lambda x: self.edge_avf_per_delay[delay][x], reverse=True) # Sort descending
        elif method=="WireStaticReachability":
            wire_list = sorted(wire_list, key=lambda edge: len(self.result_dict["analysis_results"][edge][delay]["affected_flops"]), reverse=True) # Sort descending
        return wire_list[:num_wires]

    def calculate_independent_individual_ace(self):
        self.independent_individual_ace = {}
        for delay in self.all_delays:
            self.independent_individual_ace[delay] = {}
            for flop in (set(self.all_flops).intersection(self.uniform_fi_res.keys())):
                #print("Flop here", self.logical_masking_res[delay][flop])
                self.independent_individual_ace[delay][flop] = self.logical_masking_res[delay][flop]*self.uniform_fi_res[flop]

                #.pop(missing_flop)
                #self.logical_masking_res[delay].pop(missing_flop)
                #self.group_ace_res[delay].pop(missing_flop)
                #self.unique_ace_res[delay].pop(missing_flop)
                #if self.or_ace:
                #    self.or_ace[delay].pop(missing_flop)

    def calculate_independent_or_ace(self):
        self.independent_or_ace = {}
        for delay in self.all_delays:
            self.independent_or_ace[delay] = {}
            for flop in (set(self.all_flops)):#.intersection(self.uniform_fi_res.keys())):
                aggregate_score = aggregate_orace_scores([self.uniform_fi_res[or_flop] for or_flop in self.union_per_delay_per_flop[delay][flop]], method='max')
                self.independent_or_ace[delay][flop] = self.logical_masking_res[delay][flop]*aggregate_score
                #print("Independent or ace", flop)

                #self.logical_masking_res[delay][flop]
    
    def toggle_rate(self, trace_object: vcdTrace.vcdTrace, submodule_name): 
        self.toggle_rate_dict = {}
        print("Getting toggle rates")
        for flop in tqdm.tqdm((set(self.all_flops).intersection(self.uniform_fi_res.keys()))):
            #print(trace_object.vcd.signals)
            flop_name_to_query = flop
            #print("Is ", flop_name_to_query+"_Q", "in all_flops?", (flop_name_to_query+"_Q") in set(self.all_flops))
            if (flop_name_to_query+"_Q") in set(self.all_flops):
                flop_name_to_query = flop_name_to_query+".Q"
            elif (flop_name_to_query+"_QN") in set(self.all_flops):
                flop_name_to_query = flop_name_to_query+".QN"
            if re.match(re.escape(submodule_name)+"_", flop_name_to_query):
                flop_name_to_query = flop_name_to_query.replace(submodule_name+"_", submodule_name+".")
            self.toggle_rate_dict[flop] = trace_object.get_toggle_rate(flop_name_to_query)

    def calc_independent_toggle_rate(self):
        self.independent_toggle_rate = {}
        for delay in self.all_delays:
            self.independent_toggle_rate[delay] = {}
            for flop in set(self.all_flops).intersection(self.uniform_fi_res.keys()):
                self.independent_toggle_rate[delay][flop] = self.static_analysis_res[delay][flop]*self.toggle_rate_dict[flop]

    def get_multi_bit_flip_statistics(self):
        dyn_group_size_count_per_delay = collections.defaultdict(lambda: collections.defaultdict(int))
        dyn_group_size_count_per_delay_ace = collections.defaultdict(lambda: collections.defaultdict(int))
        diff_between_dyn_and_static = collections.defaultdict(lambda: collections.defaultdict(int))
        analysis_result_dict = self.result_dict["analysis_results"]
        for delay in self.all_delays:
            for edge_result in analysis_result_dict[delay]:
                self.sim_result_per_edge[delay][tuple(edge_result["edge"])] = edge_result
                #for delay, edge_result in edge_result_per_delay.items():
                for cycle, result in edge_result["dynamically_reachable_per_cycle"].items():
                    dyn_group_size_count_per_delay[delay][len(result["dynamically_reachable"])] += 1
                    if result["ace"]:
                        dyn_group_size_count_per_delay_ace[delay][len(result["dynamically_reachable"])] += 1
                    diff_between_dyn_and_static[delay][len(set(edge_result["static_reachable"])-set(result["dynamically_reachable"]))] += 1
        self.dyn_group_size_count_per_delay= dyn_group_size_count_per_delay
        self.diff_between_dyn_and_static = diff_between_dyn_and_static
        self.dyn_group_size_count_per_delay_ace = dyn_group_size_count_per_delay_ace
        return dyn_group_size_count_per_delay, diff_between_dyn_and_static, dyn_group_size_count_per_delay_ace
            

            


def aggregate_orace_scores(flop_avf_scores, method):
    if len(flop_avf_scores) == 0:
        return 0
    if method == 'exp':
        res_sum = 0 
        for score in flop_avf_scores:
            res_sum += score
        if res_sum > 0:
            res_sum = 1/(math.e**(1/(1+res_sum))) #Monotically increasing function, normed to 1
        return res_sum
    elif method == 'max':
        return max(flop_avf_scores)




def generate_trace_with_verilator_subcall(hex_payload_path, trace_path, timeout, use_fuse_soc):
    if use_fuse_soc: 
        subprocess_args = ["fusesoc", "run", "--target=verilator_tb", "servant","--vcd=1","--uart_baudrate=57600", f"--timeout={timeout}"]
        subprocess_args += [f"--firmware={os.path.abspath(hex_payload_path)}","--verilator_options=--trace-underscore","--memsize=262144"]
        subprocess.run(subprocess_args)
        shutil.copy("./build/servant_1.2.1/verilator_tb/trace.vcd", trace_path)
    else:
        print("Current working directory", os.path.join(os.getcwd(), "run_gen_verilator_trace.sh"))
        subprocess_args = [os.path.abspath("run_gen_verilator_trace.sh"), os.path.abspath(str(hex_payload_path)), str(timeout)]
        subprocess.run(subprocess_args)
        print("Invoking", " ".join(subprocess_args))
        if os.path.exists("./build_tmp/testbench.vcd"):
            shutil.copy("./build_tmp/testbench.vcd", trace_path)
        elif os.path.exists(trace_path):
            pass
        else:
           raise Exception("Tesbench generation failed!")

    #subprocess_args += [f'--output_dir={os.path.abspath(result_cache_dir)}'] #We do not need the output



def circuitgraph_to_vcd_flop_name(circuit_element_name, submodule_name):
    #print("Submodule name", submodule_name)
    if params.SIMULATION_DEBUG:
        pass
        #print("FLOP:", circuit_element_name)
    flop_name = circuit_element_name.replace('\\', '')

    # Special mapping code for DFFs
    
    if re.match(r"dff__\w+__in", flop_name):
        ffnum = flop_name.split("__")[1]
        flop_name = "_" + ffnum + "_.D"
    elif submodule_name and re.match(r"dff_"+re.escape(submodule_name)+r"_\w+__in", flop_name):
        ffnum = flop_name.split("_")[3]
        flop_name = submodule_name+"._" + ffnum + "_.D"

    if re.match(r"dff__\w+__\w+_out", flop_name):
        ffnum = flop_name.split("__")[1]
        if flop_name.split("__")[2] == "QN_out":
            flop_name = "_" + ffnum + "_.QN"
        else:
            flop_name = "_" + ffnum + "_.Q"
    elif submodule_name and re.match(r"dff_"+re.escape(submodule_name) +r"__\w+_out", flop_name):
        ffnum = flop_name.split("_")[3]
        if flop_name.split("__")[2] == "QN_out":
            flop_name = submodule_name + "._" + ffnum + "_.QN"
        else:
            flop_name = submodule_name + "._" + ffnum + "_.Q"
    #print("flop name", flop_name)
    return flop_name


def analyze_simulation_results(results: typing.Iterable[custom_types.SimulationResult]):
    """
    Except a list of SimulationResults and prints some statistics
    """
    model_correct_total = 0
    model_incorrect_total = 0
    multi_bit_errors_total = 0
    single_bit_errors_total = 0
    for sim_result in results:
        for cycle in range(len(sim_result.num_faults_per_cycle)):
            if sim_result.num_faults_per_cycle[cycle] > 1:
                print(
                    f"Multi-bit error detected at cycle {cycle} with delay on {sim_result.edge}!")
                multi_bit_errors_total += 1
            elif sim_result.num_faults_per_cycle[cycle]==1:
                single_bit_errors_total += 1
        model_correct_total += sim_result.model_correct_total
        model_incorrect_total += sim_result.model_incorrect_total
    print(
        f"Model is correct in {model_correct_total} cases and incorrect in {model_incorrect_total} cases and a total of {multi_bit_errors_total} mulit-bit faults, {single_bit_errors_total} single-bit faults")

def process_flop_name(x):
    # PWD: the replacement of __in has incorrect behaviour when dealing with the IBEX core 
    #new_name = x.replace('dff_', '').replace('Q_out', 'Q').replace('QN_out', 'QN').replace('\\', '').replace('__in', '_')
    new_name = x.replace('dff_', '').replace('Q_out', 'Q').replace('QN_out', 'QN').replace('\\', '')
    if new_name.endswith('__in'):
        new_name = '_'.join(new_name.rsplit('__in', 1))
    #if new_name == "_221" or "_221" in x:
        #print("Replacing name", x, "with ", new_name)
    return new_name

def dump_results(results: typing.List[custom_types.SimulationResult], args, experiments, int_to_flop_map, numCycles, delay_range, delay_range_print, outfile_path: str):
    bad_set = set()
    bad_flops = []
       
    for i, arg in enumerate(args):
            #print("Results", results[i])
            #if results[i].total_num_faults >0:
            #    print("Faulting flops", results[i].faulting_flops)
            bad_flops.append([int_to_flop_map[idx] for idx in results[i].faulting_flops])
            for flop in results[i].faulting_flops:
                bad_set.add(int_to_flop_map[flop])
    analyze_simulation_results(results)

    if params.PLOT_ENABLED:
        plotErrors.plotErrorDist("Ground Truth Analysis (# of Violating Flops across %d Cycles)" % numCycles, experiments, bad_flops, delay_range, delay_range_print)

    if params.DUMP_RESULTS:
        all_delays = set()
        with open('faulting_flops.txt', 'w', newline='') as f:
            for flop in bad_set:
                f.write(flop + ",")

        #TODO: Support multiple failures

        resultsDict = {}

        for i, arg in enumerate(args):
            if str(results[i].edge) not in resultsDict.keys():
                resultsDict[str(results[i].edge)] = {}
            all_delays.add(results[i].delay)
            if results[i].delay not in resultsDict[str(results[i].edge)].keys():
                resultsDict[str(results[i].edge)][results[i].delay] = {}
                resultsDict[str(results[i].edge)][results[i].delay]["sim_results"] = {}
            for cycle in results[i].faulting_flops_per_cycle.keys():
                if cycle not in resultsDict[str(results[i].edge)][results[i].delay]["sim_results"].keys():
                    resultsDict[str(results[i].edge)][results[i].delay]["sim_results"][cycle]= []

                for flop_idx in results[i].faulting_flops_per_cycle[cycle]:
                #if len(results[i].faulting_flops_per_cycle[cycle]) == 1:
                   
                    flop_name = process_flop_name(int_to_flop_map[flop_idx]) #.replace('dff_', '').replace('Q_out', 'Q').replace('QN_out', 'QN').replace('\\', '').replace('__in', '_')

                    print("Flop", flop_name, "cycle", cycle, flush=True)
                    dumped_flop = flop_name
                    
                    resultsDict[str(results[i].edge)][results[i].delay]["sim_results"][cycle].append(str(dumped_flop))
            resultsDict[str(results[i].edge)][results[i].delay]["affected_flops"] = [process_flop_name(str(int_to_flop_map[idx])) for idx in results[i].affected_flops]
        faultScenarioJson = {}
        faultScenarioJson["all_flops"] = [process_flop_name(flop) for flop in int_to_flop_map.values()]
        faultScenarioJson["analysis_results"] = resultsDict
        faultScenarioJson["all_delays"] = list(all_delays)
        faultScenarioJson["num_cycles"] = numCycles

        with open(outfile_path, "w") as outfile_pointer:
            json.dump(faultScenarioJson, outfile_pointer, indent=2)


def draw_graph(graph: nx.Graph):
    pos = nx.spring_layout(graph)
    nx.draw(graph, with_labels=True, node_color='skyblue', node_size=1000, font_size=12, font_weight='bold')
    edge_labels = nx.get_edge_attributes(graph, params.delayStepAttributeString)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10)
    plt.show()

def calculate_flop_states(delay_circuit,tr: vcdTrace, submodule_name):
        # self.tr = trace.Trace("verilator_simulation/trace.vcd",
        #                      "TOP.servant_sim.dut.cpu.cpu.decode.", "TOP.servant_sim.dut.cpu.cpu.clk")
        elements = list(delay_circuit.c.outputs()) + \
            list(delay_circuit.c.inputs())
        flops = []
        
        if params.SIMULATION_DEBUG:
            print("STARTING")
        
        # Map the elements in our circuit to those in the vcd trace 
        for flop in elements:
            if params.SIMULATION_DEBUG:
                print("FLOP:", flop)
            flop_name = flop.replace('\\', '')

            # Special mapping code for DFFs
            
            if re.match(r"dff__\w+__in", flop_name):
                ffnum = flop_name.split("__")[1]
                flop_name = "_" + ffnum + "_.D"
            elif re.match(r"dff_"+re.escape(submodule_name)+r"_\w+__in", flop_name):
                ffnum = flop_name.split("_")[3]
                flop_name = submodule_name+"._" + ffnum + "_.D"

            if re.match(r"dff__\w+__\w+_out", flop_name):
                ffnum = flop_name.split("__")[1]
                if flop_name.split("__")[2] == "QN_out":
                    flop_name = "_" + ffnum + "_.QN"
                else:
                    flop_name = "_" + ffnum + "_.Q"
            elif re.match(r"dff_"+re.escape(submodule_name) +r"__\w+_out", flop_name):
                ffnum = flop_name.split("_")[3]
                if flop_name.split("__")[2] == "QN_out":
                    flop_name = submodule_name + "._" + ffnum + "_.QN"
                else:
                    flop_name = submodule_name + "._" + ffnum + "_.Q"
            flops.append(flop_name)
        #print("Set of flops", flops, flush=True)
        flopStates = [dict(tr.getFlopStates(flops, elements, x))
                      for x in range(tr.getNumCycles())]
        missing_inputs = [x for x in delay_circuit.c.inputs(
        )-flopStates[0].keys() if "_out" not in x]
        assert len(
            missing_inputs) == 0, f"There are missing inputs {missing_inputs}"
        return flopStates

def parse_result_json_to_dict_only_wire_avf(file_path):
    all_edges = []
    with open(file_path) as fp:
        result_dict = json.load(fp)
    all_delays = [str(x) for x in result_dict["all_delays"]]
    analysis_result_dict = result_dict["analysis_results"]
    edge_avf_per_delay = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.0))
    for delay in all_delays:
        for sim_result in analysis_result_dict[delay]:
            edge = tuple(sim_result["edge"])
            all_edges.append(edge)
            #print("Sim result", sim_result)
            for cycle, result in sim_result["dynamically_reachable_per_cycle"].items():
                if result["ace"]:
                    edge_avf_per_delay[delay][edge] += 1
            edge_avf_per_delay[delay][edge] /= params.NUM_SIM_CYCLES
            #print("Edge avf per delay", edge_avf_per_delay[delay][edge])
    
    res = AnalysisResult(all_delays, result_dict["all_flops"], all_edges, result_dict)
    res.add_results(static_analysis=None,
                    logical_masking = None,
                    group_ace = None,
                    unique_ace = None,
                    unique_exclusive_ace = None,
                    or_ace = None,
                    group_sdc=None,
                    unique_sdc=None,
                    union_per_delay_per_flop = None,
                    edge_avf_per_delay = edge_avf_per_delay,
                    per_flop_per_edge_per_delay_count = None,
                    )
    return res

def parse_result_json_to_dict(file_path):
    with open(file_path) as fp:
        result_dict = json.load(fp)
    num_cycles = result_dict["num_cycles"]
    analysis_result_dict = result_dict["analysis_results"]
    
    count_affected_per_flop_per_delay = {}
    count_non_masked_flop_per_cycle_per_delay = {}
    count_ace_flop_per_cycle_per_delay = {}
    count_ace_flop_unique_per_cycle_per_delay = {}
    
    count_or_ace_per_delay = collections.defaultdict(lambda: collections.defaultdict(int))
    count_group_sdc_ace_per_delay = collections.defaultdict(lambda: collections.defaultdict(int))
    count_unique_sdc_ace_per_delay = collections.defaultdict(lambda: collections.defaultdict(int))
    count_per_flop_per_edge_per_delay_fault = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(int)))
    count_ace_flop_exlusive_unique_per_cycle_per_delay = collections.defaultdict(lambda: collections.defaultdict(int))
    
    all_edges = []
    all_delays = [str(x) for x in result_dict["all_delays"]]
    
    total_ace_per_delay = collections.defaultdict(int)
    total_sdc_per_delay = collections.defaultdict(int)
    total_injections_per_delay = collections.defaultdict(int)
    edge_avf_per_delay = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.0))
    union_per_delay_per_flop = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
    edge_to_dyn_reachable_set = collections.defaultdict(lambda: collections.defaultdict(list))
    
    for delay in all_delays:
        count_affected_per_flop_per_delay[str(delay)] = {}
        count_non_masked_flop_per_cycle_per_delay[str(delay)] = {}
        count_ace_flop_per_cycle_per_delay[str(delay)] = {}
        count_ace_flop_unique_per_cycle_per_delay[str(delay)] = {}
        
        for res_dict in [count_group_sdc_ace_per_delay, count_unique_sdc_ace_per_delay]:
            res_dict[str(delay)] = {}
        
        for f in result_dict["all_flops"]:
            count_affected_per_flop_per_delay[str(delay)][f] = 0
            count_non_masked_flop_per_cycle_per_delay[str(delay)][f] = 0
            count_ace_flop_per_cycle_per_delay[str(delay)][f] = 0
            count_ace_flop_unique_per_cycle_per_delay[str(delay)][f] = 0
            for res_dict in [count_group_sdc_ace_per_delay, count_unique_sdc_ace_per_delay]:
                res_dict[str(delay)][f] = 0
        analysis_result_dict_this_delay =analysis_result_dict[str(delay)]
        
        for sim_result in analysis_result_dict_this_delay:
            edge = tuple(sim_result["edge"])
            all_edges.append(edge)
            #if edge=="all_flops":
            #    continue
            #print("edge", edge, "Edge results per delay", edge_result_per_delay)
            #exit(0)
            flop_to_count_mapping = collections.defaultdict(lambda: collections.defaultdict(int))

            #print("affected flops", edge_result["affected_flops"])
            for f in sim_result["static_reachable"]:
                if delay not in count_affected_per_flop_per_delay:
                    count_affected_per_flop_per_delay[delay] = {}
                if f not in count_affected_per_flop_per_delay[delay]:
                    count_affected_per_flop_per_delay[delay][f] = 0
                count_affected_per_flop_per_delay[delay][f] += 1
            
            for cycle, result in sim_result["dynamically_reachable_per_cycle"].items():
                #print("What is the result Result", result, flush=True)
                failing_flops = result["dynamically_reachable"]
                is_or_ace = False
                
                for f in failing_flops:
                    flop_to_count_mapping[delay][f] += 1
                    if result["per_flop_aceness"][f]["uniqueAce"]:
                        is_or_ace = True
                    union_per_delay_per_flop[delay][f].update(failing_flops)
                
                for f in failing_flops:
                    if delay not in count_non_masked_flop_per_cycle_per_delay:
                        count_non_masked_flop_per_cycle_per_delay[delay] = {}
                    if delay not in count_ace_flop_per_cycle_per_delay:
                        count_ace_flop_per_cycle_per_delay[delay] = {}
                    if delay not in count_ace_flop_unique_per_cycle_per_delay:
                        count_ace_flop_unique_per_cycle_per_delay[delay] = {}
                    if f not in count_non_masked_flop_per_cycle_per_delay[delay]:
                        count_non_masked_flop_per_cycle_per_delay[delay][f] = 0
                    if f not in count_non_masked_flop_per_cycle_per_delay[delay]:
                        count_ace_flop_per_cycle_per_delay[delay][f] = 0
                    if f not in count_ace_flop_unique_per_cycle_per_delay[delay]:
                        count_ace_flop_unique_per_cycle_per_delay[delay][f] = 0
                    count_non_masked_flop_per_cycle_per_delay[delay][f] += 1
                    
                    if result["ace"]:
                        count_ace_flop_per_cycle_per_delay[delay][f] += 1
                        count_per_flop_per_edge_per_delay_fault[delay][edge][f] += 1
                        total_ace_per_delay[delay] += 1
                        
                        if not result["per_flop_aceness"][f]["groupAceWithoutFlop"]:
                            count_ace_flop_exlusive_unique_per_cycle_per_delay[delay][f] += 1
                        else:
                            pass#print("Is reslt this ace? for flop", "delay", delay, "flop", f, result["per_flop_aceness"][f]["groupAceWithouFlop"], "group", failing_flops)

                    if result["per_flop_aceness"][f]["uniqueAce"]:
                        count_ace_flop_unique_per_cycle_per_delay[delay][f] += 1

                    if is_or_ace:
                        count_or_ace_per_delay[delay][f] += 1
                    if "sdc" in result and result["sdc"]:
                        count_group_sdc_ace_per_delay[delay][f] += 1
                    if "per_flop_sdcness" in result and result["per_flop_sdcness"][f]:
                        count_unique_sdc_ace_per_delay[delay][f] += 1
                if "sdc" in result and result["sdc"]:
                    total_sdc_per_delay[delay] += 1
                if  result["ace"]:
                    total_ace_per_delay[delay] += 1
                    edge_avf_per_delay[delay][edge] += 1

                    '''
                    if is_or_ace and not result["ace"]:
                        print(f"For {failing_flops} cycle {cycle} or ace true, groupAce false, per flop aceness {result['per_flop_aceness']}")
                    if result["ace"] and not is_or_ace:
                        print(f"For {failing_flops} cycle {cycle} or ace false, groupAce true, per flop aceness  {result['per_flop_aceness']}")
                    if is_or_ace and result["ace"]:
                        print("Both true")
                    '''
                    #if not result["sdc"] and result["ace"]:
                    #    print(f"For {failing_flops} cycle {cycle}  groupAce true, but groupSdc false, filename {','.join(sorted(failing_flops))+'_'+cycle}")
                    #elif result["sdc"] and result["ace"]:
                    #    print(f"For {failing_flops} cycle {cycle}  groupAce true, and groupSdc true, filename {','.join(sorted(failing_flops))+'_'+cycle}")

            edge_avf_per_delay[delay][edge] /= params.NUM_SIM_CYCLES
            edge_to_dyn_reachable_set[delay][edge] = sorted(flop_to_count_mapping[delay].keys(), key=lambda x: flop_to_count_mapping[delay][x], reverse=True)

                    
                    
    #print("All flops",  result_dict["all_flops"])
    #print("Edge avf per delay", edge_avf_per_delay)

    res = AnalysisResult(all_delays, result_dict["all_flops"], all_edges, num_cycles, result_dict)
    res.add_results(static_analysis=count_affected_per_flop_per_delay,
                    logical_masking = count_non_masked_flop_per_cycle_per_delay,
                    group_ace = count_ace_flop_per_cycle_per_delay,
                    unique_ace = count_ace_flop_unique_per_cycle_per_delay,
                    unique_exclusive_ace = count_ace_flop_exlusive_unique_per_cycle_per_delay,
                    or_ace = count_or_ace_per_delay,
                    group_sdc=count_group_sdc_ace_per_delay,
                    unique_sdc=count_unique_sdc_ace_per_delay,
                    union_per_delay_per_flop = union_per_delay_per_flop,
                    edge_avf_per_delay = edge_avf_per_delay,
                    per_flop_per_edge_per_delay_count = count_per_flop_per_edge_per_delay_fault,
                    )
    res.total_ace_per_delay = total_ace_per_delay
    res.total_sdc_per_delay = total_sdc_per_delay
    res.dyn_set_per_edge = edge_to_dyn_reachable_set
    return res

def remove_digit_part(input_string):
    # Define the regular expression pattern to match the [digit] part
    pattern = r'\[\d+\]$'
    # Use re.sub to replace the matched pattern with an empty string
    result = re.sub(pattern, '', input_string)
    return result

def match_register_pattern(input_string):
    pattern = r'.*\[\d+\]$'
    return re.match(pattern, input_string)

def get_group_for_flop(input_string):
    if match_register_pattern(input_string):
        return remove_digit_part(input_string)
    else:
        return input_string
        

def parse_uniform_results(uniform_file_path):
    df = pd.read_csv(uniform_file_path)
    result = {}
    for index, row in df.iterrows():
        key = row["flop"]
        value = row["count"]
        result[key] = value
    return result

def get_groups(flop_list):
    groups = collections.defaultdict(list)
    for f in flop_list:
        print("Flop ", f)
        pattern = r'.*\[\d+\]$'
        if re.match(pattern, f):
            print("Flops", f)
            groups[remove_digit_part(f)].append(f)
        #else:
        #    groups[f].append(f)
    return groups
