from injector import custom_types
import tqdm
from multiprocessing.pool import ThreadPool
from injector import params
import collections
import itertools
import functools
from injector import util
import sys
#import cProfile

class AVFCalculator:
    def __init__(self, delay_fault_results: dict, aceness_analyser, all_flops, relevant_wires, inject_into_cycles_delay, inject_into_cycles_particle):
        self.thread_pool = None
        self.delay_fault_results = delay_fault_results
        self.aceness_analyser = aceness_analyser
        self.all_flops = all_flops
        self.relevant_wires = relevant_wires
        if self.relevant_wires is not None and type(self.relevant_wires[0]) is not tuple:
            raise Exception("I expect the wires as tuples")
        self.inject_into_cycles_delay = inject_into_cycles_delay
        self.inject_into_cycles_particle = inject_into_cycles_particle
        self.thread_pool = ThreadPool(params.NJOBS)
        self.protected_flops = set()    
        self.aceness_analyser.set_protected_flops(set(()))
    
    def __del__(self):
        if self.thread_pool:
            self.thread_pool.close()
            del self.thread_pool
         
    def precompute_flop_to_edge_mapping(self):
        self.flop_to_edge_mapping = {}
        for f in self.all_flops:
            self.flop_to_edge_mapping[f] = set()
        for edge, edge_res in self.delay_fault_results.items():
            for cycle, dynamically_reachable_flops in edge_res.dynamically_reachable_per_cycle.items():
                for f in dynamically_reachable_flops:
                    self.flop_to_edge_mapping[f].add(edge)
            

    def set_protected_flops(self, flops):
        return
        self.protected_flops = flops
        self.aceness_analyser.set_protected_flops(set(flops))

    def ace_compounding_rate(self):
        strong_ace_compounding = 0
        weak_ace_compounding = 0
        ace_interference = 0
        or_ace_matching = 0
        total_dyn_reachable = 0
        total_num_ace = 0
        total_num_non_ace = 0
        counts = dict()
        for edge, edge_res in self.delay_fault_results.items():
            if len(edge_res.static_reachable)>0:
                #divisor += 1
                for cycle, dynamically_reachable_flops in edge_res.dynamically_reachable_per_cycle.items():
                    ace = self.aceness_analyser.get_ace_ness(set(dynamically_reachable_flops), str(int(cycle)+1))
                    total_dyn_reachable += 1
                    is_or_ace = False
                    ace_flop = None
                    for f in dynamically_reachable_flops:
                        if self.aceness_analyser.get_ace_ness(set([f]), str(int(cycle)+1)):
                            is_or_ace = True
                            ace_flop = f
                            break
                    if ace is True:
                        total_num_ace += 1
                        idx = len(dynamically_reachable_flops)
                        counts[idx] = counts.get(idx, 0) + 1
                    if ace is False:
                        total_num_non_ace += 1
                    if is_or_ace is False and ace is True:
                        strong_ace_compounding += 1
                    if is_or_ace is True and ace is True:
                        weak_ace_compounding += 1
                    if is_or_ace is True and ace is False:
                        ace_interference += 1
                        #print("Set", dynamically_reachable_flops)
                        #print("Is ACE flop because", ace_flop)
                        #self.aceness_analyser.calculate_aceness(dynamically_reachable_flops, str(int(cycle)+1), True)
                    if or_ace_matching == ace:
                        or_ace_matching += 1
        #print("ACE distribution", counts)
        #return (strong_ace_compounding / max(total_num_ace,1)), (weak_ace_compounding / max(total_num_ace,1)), (ace_interference / max(total_num_non_ace,1))
        return (strong_ace_compounding / max(total_dyn_reachable,1)), (weak_ace_compounding / max(total_dyn_reachable,1)), (ace_interference / max(total_dyn_reachable,1))
        #return (strong_ace_compounding / max(total_dyn_reachable,1)), (weak_ace_compounding / max(total_dyn_reachable,1)), (ace_interference / max(total_dyn_reachable,1))

                        #if ace is True:
                        #    ace = self.aceness_analyser.get_ace_ness(set(dynamically_reachable_flops), cycle)

                        

    def get_group_avf(self, group: [str, [str]]):# avf_type="particle"):
        """
        :param group: A tuple (group_name, flops)
        """
        avf = 0
        divisor = 0
        group_name = group[0]
        flops = group[1]
        #self.aceness_analyser.set_protected_flops(flops)
        for edge, edge_res in self.delay_fault_results.items():
            if len(set(flops).intersection(edge_res.static_reachable))>0:
                divisor += 1
                for cycle, dynamically_reachable_flops in edge_res.dynamically_reachable_per_cycle.items():
                    #ace = ace = self.aceness_analyser.get_ace_ness(set(result["dynamically_reachable"])-set(flops), cycle)
                    if True: #len(set(flops).intersection(set(dynamically_reachable_flops)))>0:
                        #if avf_type == "particle":
                        ace = self.aceness_analyser.get_ace_ness(set(dynamically_reachable_flops), str(int(cycle)+1))
                        #elif avf_type == "delay":
                        #    ace = self.aceness_analyser.get_delay_ace_ness(set(dynamically_reachable_flops), str(int(cycle)+1))
                        #else:
                        #    raise Exception(f"avf type {avf_type} not implemented")
                        if ace is True:
                            avf += 1
                    #if result["ace"]: #If result is not ace, we can ignore
                        #print("Result is ace ", set(flops), "dynamically reachable", set(result["dynamically_reachable"]))
                    #    if len(set(flops).intersection(set(dynamically_reachable_flops)))>0:
                    #        ace = self.aceness_analyser.get_ace_ness(set(result["dynamically_reachable"])-set(flops), cycle)
                    #        if ace is True:
                    #            self.per_group_avf[group] += 1
        self.aceness_analyser.set_protected_flops(set())
        return group_name, avf
        #if divisor == 0:
        #    return 0
        #else:
        #    avf /= (divisor*len(self.inject_into_cycles))
        #    return avf
        #return avf/divisor

    def get_avf_for_groups(self, groups, avf_type="wireavf"):
        
        if avf_type == "wireavf":
            self.per_group_wireavf_avf = {}
            avf_dict = self.per_group_wireavf_avf
            get_group_avf_func = self.get_group_avf
        elif avf_type == "fan_out_micro_approx":
            self.per_group_delay_avf = {}
            avf_dict = self.per_group_delay_avf
            get_group_avf_func = self.get_delay_avf_for_single_flop_or_group
        else:
            raise Exception(f"avf type {avf_type} not implemented")
        self.aceness_analyser.set_protected_flops(set())
        
        global pbar
        pbar = tqdm.tqdm(total=len(groups))
       
        with ThreadPool(params.NJOBS) as pool:
            res = list(pool.map(get_group_avf_func, groups.items()))
        for group, avf in res: 
            avf_dict[group] = avf   
        
        #for group, flops in tqdm.tqdm(groups.items()):
        #    avf_dict[group] = self.get_group_avf(flops)   
        self.aceness_analyser.set_protected_flops(set())
        return avf_dict

    def get_avf_for_flop(self, flop):
        avf = 0
        for cycle in self.inject_into_cycles_particle:
            if self.aceness_analyser.get_ace_ness([flop], str(cycle)):
                #print(f"{flop} is ace in {cycle}")
                avf += 1
        avf /= len(self.inject_into_cycles_particle)
        pbar.update(1)
        return (flop, avf)

    def get_particle_strike_avf_per_flop(self, flop_list=None):
        self.particle_strike_avf = {}
        if flop_list is None:
            jobs = self.all_flops  
        else:
            jobs = flop_list
        global pbar
        pbar = tqdm.tqdm(total=len(jobs))  
        #for f in tqdm.tqdm(self.all_flops):
        all_flops = self.all_flops
        #cProfile.runctx('for f in all_flops[:50]: self.get_avf_for_flop(f) ',globals(), locals())
        #for f in all_flops: print(self.get_avf_for_flop(f))
        

        #with ThreadPool(params.NJOBS) as pool:
        #res = list(self.thread_pool.map(self.get_avf_for_flop, jobs))
        #res = list(self.thread_pool.map(self.get_avf_for_flop, jobs))
        for flop, avf in self.thread_pool.imap(self.get_avf_for_flop, jobs):
            #print("Assinging flop", flop, "avf", avf)
            self.particle_strike_avf[flop] = avf   
        return self.particle_strike_avf
    
    def get_micro_arch_wire_avf_approximation(self, approx_type="single_flops", flops_list=None, paths=None):
        """
        Get a micro arch approximation for wireavf. Function supports two ways currently.
        single_flops: We approximate wireavf as: 
        \sum_{f \in flops, i \in cycles} getDelayACE(f,i) / #flops * #cycles
        fan_out: We approximate wireavf as: 
        \sum_{f \in in_flops, i \in cycles} getDelayGroupACE(fanOut(in_flops),i) / #in_flops * #cycles       
        """
        if approx_type=="single_flops":
            self.get_delay_avf_for_all_flops()
            avf = 0
            for flop in self.all_flops:
                avf += self.delay_avf_per_flop[flop]
            avf /= len(self.all_flops)
            return avf
        if approx_type=="fan_out":
            input_to_fanout_mapping = util.get_fanout_for_input_flops(flops_list, paths, self.all_flops)
            avf_dict = self.get_avf_for_groups(input_to_fanout_mapping, "fan_out_micro_approx")
            #print("avf_dict", avf_dict)
            avf = 0
            for fanin in avf_dict.keys():
                avf += avf_dict[fanin]
            avf /= len(avf_dict)
            return avf
        

    def get_delay_avf_for_single_flop_or_group(self, flop):
        """
        Call either with:
        single-string: Get delay avf for flop
        tuple(str, [str]): Get delay avf for group of flops 
        [str]: Get delay for the group of flops, return list
        """
        if type(flop) == str:
            return_name = flop
            get_aceness_arg = [flop]
        elif type(flop) == tuple:
            return_name = flop[0]
            get_aceness_arg = list(flop[1])
            #print(get_aceness_arg)
        elif type(flop) == list:
            return_name = "".join(flop)
            get_aceness_arg = flop
        else:
            raise Exception(f"Type {type(flop)} not implemented!")
        #print("Aceness arg", get_aceness_arg)
        avf = 0
        for cycle in self.inject_into_cycles_particle:
            if self.aceness_analyser.get_delay_ace_ness(get_aceness_arg, str(cycle)):
                #print(f"{flop} is delay avf in {cycle}")
                avf += 1
        avf /= len(self.inject_into_cycles_particle)
        pbar.update(1)
        return (return_name, avf)

    def get_delay_avf_for_all_flops(self):
        """
        Calculate the delay avf per flop.
        Delay avf is saying: If in cycle i, flop f would actually get value of cycle i-1, 
        what would be the consequences?
        """
        self.delay_avf_per_flop = {}
        global pbar
        pbar = tqdm.tqdm(total=len(self.all_flops))  
        #with ThreadPool(params.NJOBS) as pool:
        res = list(self.thread_pool.map(self.get_delay_avf_for_single_flop_or_group, self.all_flops))
        for flop, avf in res:
            self.delay_avf_per_flop[flop] = avf   
        return self.delay_avf_per_flop        

    def get_delay_fault_impact_score_per_flop(self):
        self.delay_fault_impact_score = {}
        for f in self.all_flops:
            self.delay_fault_impact_score[f] = 0
        for edge, edge_res in self.delay_fault_results.items():
            #print("Getting edge", edge)
            for cycle, dynamically_reachable_this_cycle in edge_res.dynamically_reachable_per_cycle.items():
                ace = self.aceness_analyser.get_ace_ness(dynamically_reachable_this_cycle, str(int(cycle)+1))
                if ace: #If result is not ace, we can ignore
                    failing_flops = dynamically_reachable_this_cycle
                    for f in failing_flops:
                        if f in self.delay_fault_impact_score:
                            self.delay_fault_impact_score[f] += 1
        return self.delay_fault_impact_score
    
    def get_wire_avf_for_wire(self, edge_res, protected_flops=None):
        avf = 0
        #print("Getting avf for", edge_res.edge)
        arg_list = []
        if len(edge_res.dynamically_reachable_per_cycle.items()) == 0:
            pbar.update(1)
            return (edge_res.edge, avf)
        if protected_flops is not None:
            protected_flops = set(protected_flops)
        else:
            protected_flops = set()
        for cycle, dynamically_reachable_flops in edge_res.dynamically_reachable_per_cycle.items():#sim_result["dynamically_reachable_per_cycle"].items():
            dynamically_reachable_flops = dynamically_reachable_flops-protected_flops
            arg_list.append((dynamically_reachable_flops, str(int(cycle)+1)))
        #with ThreadPool(int(params.NJOBS /2)) as pool:
        for ace in self.thread_pool.imap(lambda args: self.aceness_analyser.get_ace_ness(*args), arg_list):
            if ace:
                avf += 1
            pbar.update(1)  
        #res = self.thread_pool.starmap(self.aceness_analyser.get_ace_ness, arg_list)
        #for ace in res:
        #    if ace:
        #        avf += 1
        #for cycle, dynamically_reachable_flops in edge_res.dynamically_reachable_per_cycle.items():#sim_result["dynamically_reachable_per_cycle"].items():
        #    if True: #len(set(dynamically_reachable_flops).intersection(set(self.all_flops)))>=1:
        #            ace = self.aceness_analyser.get_ace_ness(dynamically_reachable_flops, str(int(cycle)+1))
                    #print("Getting aceness", dynamically_reachable_flops,"ace", ace)
        #            if ace:
                        #print("Increasing wireavf for edge",edge)
        #                avf += 1
        avf /= len(self.inject_into_cycles_delay)
       
        return (edge_res.edge, avf)

    def get_wire_avf(self):
        print("Getting wireavf now", flush=True)
        self.wire_avf = {}
        for edge in self.relevant_wires:
            self.wire_avf[tuple(edge)] = 0 
        #jobs = self.relevant_wires
        jobs = []
        total_num_aceness = 0
        for edge, edge_res in self.delay_fault_results.items():
            #print("Getting edge", edge, edge in self.relevant_wires)
            if edge not in self.relevant_wires:
                continue
            #print("Edge", edge)
            jobs.append(edge_res)
            total_num_aceness += max(len(edge_res.dynamically_reachable_per_cycle),1) #If no dyn reachable sets, just one  function call
        global pbar
        pbar = tqdm.tqdm(total=total_num_aceness)  
        with ThreadPool(params.NJOBS) as pool:
            res = pool.map(self.get_wire_avf_for_wire, jobs)
        #res = list(map(self.get_wire_avf_for_wire, jobs))
        #res = list(self.thread_pool.map(self.get_wire_avf_for_wire, jobs))
        pbar.close()
        for edge, avf in res:
            #print("\r Setting", edge, "to ", avf, flush=True, end="")
            self.wire_avf[edge] = avf   
        #print("")
        return self.wire_avf
    
    def get_wire_avf_for_wire_or_ace(self, edge_res):
        avf = 0
        #print("Getting avf for", edge_res.edge)
        arg_list = []
        if len(edge_res.dynamically_reachable_per_cycle.items()) == 0:
            pbar.update(1)
            return (edge_res.edge, avf)
        #if protected_flops is not None:
        #    protected_flops = set(protected_flops)
        #else:
        #    protected_flops = set()
        for cycle, dynamically_reachable_flops in edge_res.dynamically_reachable_per_cycle.items():#sim_result["dynamically_reachable_per_cycle"].items():
            dynamically_reachable_flops = dynamically_reachable_flops#-protected_flops
            arg_list.append((dynamically_reachable_flops, str(int(cycle)+1)))
        #with ThreadPool(int(params.NJOBS /2)) as pool:
        for ace in self.thread_pool.imap(lambda args: self.aceness_analyser.get_or_ace_ness(*args), arg_list):
            if ace:
                avf += 1
            pbar.update(1)  
        #res = self.thread_pool.starmap(self.aceness_analyser.get_ace_ness, arg_list)
        #for ace in res:
        #    if ace:
        #        avf += 1
        #for cycle, dynamically_reachable_flops in edge_res.dynamically_reachable_per_cycle.items():#sim_result["dynamically_reachable_per_cycle"].items():
        #    if True: #len(set(dynamically_reachable_flops).intersection(set(self.all_flops)))>=1:
        #            ace = self.aceness_analyser.get_ace_ness(dynamically_reachable_flops, str(int(cycle)+1))
                    #print("Getting aceness", dynamically_reachable_flops,"ace", ace)
        #            if ace:
                        #print("Increasing wireavf for edge",edge)
        #                avf += 1
        avf /= len(self.inject_into_cycles_delay)
       
        return (edge_res.edge, avf)
        
        
    
    def adjust_structure_delay_avf_with_flop_protection(self, protected_flops):
        edges_to_recompute = set()
        new_score = self.wire_avf_sum
        #print("New score before recomputing", new_score)
        for f in protected_flops:
            edges_to_recompute.update(self.flop_to_edge_mapping[f])
        #print("Need to recompute edges", edges_to_recompute)
        for e in edges_to_recompute:
            new_score -= self.wire_avf[e]
        #print("New score after substraction ", new_score, flush=True)
        for e in edges_to_recompute:
            new_score += self.get_wire_avf_for_wire(self.delay_fault_results[e],protected_flops)[1]
        #print("New score after adding", new_score, "sys float", sys.float_info.epsilon, flush=True)
        if new_score < 0:
            if new_score < (0-sys.float_info.epsilon*50):
                pass
                #raise Exception("Score decreased below 0?")
            else:
                new_score = 0
    
        return (new_score / len(self.relevant_wires))

    
    def recompute_wire_avf_with_protection(self, old_wire_avf, additional_protected_flops=None):
        print("Recomputing wireavf now", flush=True)
        if additional_protected_flops is not None:
            protected_flops = set(additional_protected_flops)
        protected_flops = protected_flops.union(self.protected_flops)
        wire_avf = {}
        for edge in self.relevant_wires:
            wire_avf[tuple(edge)] = old_wire_avf[tuple(edge)]
        #jobs = self.relevant_wires
        jobs = []
       
        #for edge, edge_res in tqdm.tqdm(self.delay_fault_results.items()):
            #print("Getting edge", edge, edge in self.relevant_wires)
        #    if edge not in self.relevant_wires:
        #        continue
        #    if len(set(edge_res.static_reachable).intersection(set(protected_flops)))==0:
        #        continue

            #print("Edge", edge)
        #    jobs.append((edge_res, protected_flops))
        edges_to_recompute = set()
        for f in protected_flops:
            edges_to_recompute = edges_to_recompute.union(set(self.flop_to_edge_mapping[f]))
        for edge in edges_to_recompute:
            jobs.append((self.delay_fault_results[edge], protected_flops))
            
            
        #global pbar
        #pbar = tqdm.tqdm(total=len(jobs))  
            #lambda args: self.aceness_analyser.get_ace_ness(*args), arg_list
        print("Recomputing edges", jobs)
        for edge,avf in map(lambda args: self.get_wire_avf_for_wire(*args), jobs):
            wire_avf[edge] = avf
        #res = list(self.thread_pool.map(self.get_wire_avf_for_wire, jobs))
        #for edge, avf in res:
            #print("Setting", edge, "to ", avf)
        #    wire_avf[edge] = avf   
        return wire_avf
        
    
    def get_x_highest_flops(self, num_flops, method='DelayFaultImpactScore'):
        flop_list = self.all_flops
        if method in {'DelayFaultImpactScore', "ParticleStrikeAVF"}: 
            ranking_dict = None #Which dict do we use to rank flops?
            if method=="DelayFaultImpactScore": #DelayFaultImpactScore
                ranking_dict = self.delay_fault_impact_score
            elif method=="ParticleStrikeAVF":
                ranking_dict = self.particle_strike_avf
            flop_list = sorted(flop_list, key=lambda flop
            : ranking_dict[flop], reverse=True) # Sort descending
        elif method=='Random':
            random.seed(1)
            return random.sample(flop_list, num_flops)
        else:
            raise Exception(f"Invalid Method selected {method}")
        return flop_list[:num_flops]

    def get_x_highest_wires(self, num_wires, method="WireAVF"):
        wire_list = list(self.wire_avf.keys())
        if method=="WireAVF":
            wire_list = sorted(wire_list, key=lambda x: self.wire_avf[x], reverse=True) # Sort descending
        return wire_list[:num_wires]


    def get_structure_fit(self, protected_edges=None):
        if protected_edges is None:
            protected_edges = set()
        wire_delay_structure_fit = 0.0
        for edge, edge_avf in self.wire_avf.items():
            #print("Get edge avf", edge, edge_avf)
            if edge not in set(protected_edges):
                wire_delay_structure_fit += edge_avf*params.EDGE_FIT
        return wire_delay_structure_fit

    def get_structure_delay_avf(self, protected_edges=None):
        raise Exception("Dont call this method")
        num_ace_edges_per_cycles = collections.defaultdict(int)
        if protected_edges is None:
            protected_edges = set()
        for edge, edge_res in self.delay_fault_results.items():
            if edge not in self.relevant_wires:
                continue
            if edge in protected_edges:
                continue
            for cycle, dynamically_reachable_this_cycle in edge_res.dynamically_reachable_per_cycle.items():
                #print("Cycle", type(cycle))
                if True: #len(set(dynamically_reachable_this_cycle).intersection(set(self.all_flops)))>=1:
                    ace = self.aceness_analyser.get_ace_ness(dynamically_reachable_this_cycle, str(int(cycle)+1))
                    if ace: #If result is not ace, we can ignore
                        num_ace_edges_per_cycles[cycle] += 1
        ret_avf = 0
        for cycle, num_ace_edges in num_ace_edges_per_cycles.items():
            ret_avf += num_ace_edges
        ret_avf /= (len(self.relevant_wires)*len(self.inject_into_cycles_delay))
        return ret_avf
    
    def recompute_structue_delay_avf_with_protected_edges(self, protected_edges):
        ret_avf = self.wire_avf_sum
        for e in protected_edges:
            ret_avf -= self.wire_avf[e]
        return (ret_avf / len(self.relevant_wires))
    
    def get_wire_avf_dict_or_ace(self):
        #print("Getting wireavf now", flush=True)
        wire_avf_or_ace = {}
        for edge in self.relevant_wires:
            wire_avf_or_ace[tuple(edge)] = 0 
        #jobs = self.relevant_wires
        jobs = []
        total_num_aceness = 0
        for edge, edge_res in self.delay_fault_results.items():
            #print("Getting edge", edge, edge in self.relevant_wires)
            if edge not in self.relevant_wires:
                continue
            #print("Edge", edge)
            jobs.append(edge_res)
            total_num_aceness += max(len(edge_res.dynamically_reachable_per_cycle),1) #If no dyn reachable sets, just one  function call
        global pbar
        pbar = tqdm.tqdm(total=total_num_aceness)  
        with ThreadPool(params.NJOBS) as pool:
            res = pool.map(self.get_wire_avf_for_wire_or_ace, jobs)
        #res = list(map(self.get_wire_avf_for_wire, jobs))
        #res = list(self.thread_pool.map(self.get_wire_avf_for_wire, jobs))
        pbar.close()
        for edge, avf in res:
            #print("\r Setting", edge, "to ", avf, flush=True, end="")
            wire_avf_or_ace[edge] = avf   
        #print("")
        return wire_avf_or_ace
    
    def get_structure_delay_avf_savf_approx(self):
        ret_avf = 0
        reachable_flops = set()
        for edge, edge_res in self.delay_fault_results.items():
            for cycle, dynamically_reachable_this_cycle in edge_res.dynamically_reachable_per_cycle.items():
                reachable_flops.update(set(dynamically_reachable_this_cycle))
        self.get_particle_strike_avf_per_flop(list(reachable_flops))
        for edge, edge_res in self.delay_fault_results.items():
            for cycle, dynamically_reachable_this_cycle in edge_res.dynamically_reachable_per_cycle.items():
                avf_increase = 0
                for f in dynamically_reachable_this_cycle:
                    avf_increase = max(avf_increase, self.particle_strike_avf[f])
                ret_avf += avf_increase
        #wire_avf_savf_approx = self.get_wire_avf_dict_or_ace()
        #for edge, edge_res in self.delay_fault_results.items():
        #   ret_avf += wire_avf_or_ace[edge]
        ret_avf /= (len(self.relevant_wires)*len(self.inject_into_cycles_delay))
        return ret_avf        
    
    def get_structure_delay_avf_independent_approx(self):
        #Calculate a DelayAVF_d(H) ~= (% of delay faults of delay d that result in at least one state element error) * sAVF(H).
        injections_with_at_least_one_state_element_error = 0
        total_num_injections = (len(self.relevant_wires)*len(self.inject_into_cycles_delay))
        for edge, edge_res in self.delay_fault_results.items():
            for cycle, dynamically_reachable_this_cycle in edge_res.dynamically_reachable_per_cycle.items():
                if len(dynamically_reachable_this_cycle)>0:
                    injections_with_at_least_one_state_element_error += 1
        percent_at_least_one_state_element_error = injections_with_at_least_one_state_element_error / total_num_injections
        savf_structure = self.get_structure_particle_strike_avf()
        #wire_avf_savf_approx = self.get_wire_avf_dict_or_ace()
        #for edge, edge_res in self.delay_fault_results.items():
        #   ret_avf += wire_avf_or_ace[edge]
        ret_avf = percent_at_least_one_state_element_error * savf_structure
        return ret_avf        
    
    def get_structure_delay_avf_or_ace(self):
        ret_avf = 0
        wire_avf_or_ace = self.get_wire_avf_dict_or_ace()
        for edge, edge_res in self.delay_fault_results.items():
            ret_avf += wire_avf_or_ace[edge]
        ret_avf /= len(self.relevant_wires) #*len(self.inject_into_cycles))
        return ret_avf        
    
    def get_structure_delay_avf_through_sum(self, protected_edges=None, provided_wire_avf=None):
        if protected_edges is None:
            protected_edges = set()
        if provided_wire_avf is None:
            wire_avf = self.wire_avf
        else:
            wire_avf = provided_wire_avf
        num_ace_edges_per_cycles = collections.defaultdict(int)
        ret_avf = 0
        for edge, edge_res in self.delay_fault_results.items():
            #print("Getting first wireavf for",edge)
            if edge not in self.relevant_wires:
                #print("Edge not in relevant wires", edge)
                continue
            if edge in protected_edges:
                continue
            #print("Getting wireavf for",edge)
            ret_avf += wire_avf[edge]
            #for cycle, dynamically_reachable_this_cycle in edge_res.dynamically_reachable_per_cycle.items():
                #print("Cycle", type(cycle))
            #    ace = self.aceness_analyser.get_ace_ness(dynamically_reachable_this_cycle, cycle)
            #    if ace: #If result is not ace, we can ignore
            #       num_ace_edges_per_cycles[cycle] += 1
        #ret_avf = 0
        #for cycle, num_ace_edges in num_ace_edges_per_cycles.items():
        #    ret_avf += num_ace_edges
        self.wire_avf_sum = ret_avf
        ret_avf /= len(self.relevant_wires) #*len(self.inject_into_cycles))
        return ret_avf
    

    def get_structure_particle_strike_avf(self):
        avf = 0
        for flop in self.all_flops:
            ##print(f"Avf of {flop} is {self.particle_strike_avf[flop]}")
            avf += self.particle_strike_avf[flop]
        avf /= max(len(self.all_flops),1)
        return avf
        #avf = 0
        #for cycle in self.inject_into_cycles_particle:
        #    for flop in self.all_flops:
        #        #print("Cycle", type(cycle))
        #        if self.aceness_analyser.get_ace_ness([flop], str(cycle)):
        #            avf += 1
        #avf /= len(self.inject_into_cycles_particle)*len(self.all_flops)
        #return avf


