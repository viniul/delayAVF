import collections
import json
import pandas
SimulationResult = collections.namedtuple('SimulationResult', [
                                          'edge', 'delay', 'num_faults_per_cycle', 'model_correct_total', 'model_incorrect_total', 'faulting_flops', 'faulting_flops_per_cycle', 'affected_flops'])

class EdgeSimResult:
    def __init__(self, edge, delay, fan_out, static_reachable, dynamically_reachable_per_cycle):
        self.edge = edge
        self.delay = delay
        self.fan_out = fan_out
        self.static_reachable = static_reachable
        self.dynamically_reachable_per_cycle = dynamically_reachable_per_cycle
        for cycle in self.dynamically_reachable_per_cycle.keys():
            dynamically_reachable_this_cycle = self.dynamically_reachable_per_cycle[cycle]
            self.dynamically_reachable_per_cycle[cycle] = set(dynamically_reachable_this_cycle)
            

class DelayFaultResults:
    def __init__(self, result_dict):
        self.num_cycles = result_dict["num_cycles"]
        self.analysis_result_dict = result_dict["analysis_results"]
        self.all_edges = set()
        self.all_delays = [str(x) for x in result_dict["all_delays"]]
        #self.paths = result_dict["path_distribution"]
        #self.max_steps = result_dict["max_steps"]
        self.per_delay_per_edge_result = {}
        for delay in self.all_delays:
            self.per_delay_per_edge_result[delay]  = {}
            analysis_result_dict_this_delay = self.analysis_result_dict[str(delay)]
            for sim_result in analysis_result_dict_this_delay:
                edge = tuple(sim_result["edge"])
                self.all_edges.add(edge)
                edge_sim_result = EdgeSimResult(edge, delay, sim_result["fan_out"], sim_result["static_reachable"], sim_result["dynamically_reachable_per_cycle"])
                self.per_delay_per_edge_result[delay][edge] = edge_sim_result
        self.all_edges = list(self.all_edges)
        
    def get_edge_results_for_delay(self, delay):
        return self.per_delay_per_edge_result[delay]   
        
    def get_edge_results_for_max_delay(self):
        delay = str(max([int(x) for x in self.all_delays]))
        return get_edge_results_for_delay(delay)
        




    @classmethod
    def from_json_path(cls, file_path):
        with open(file_path) as fp:
            result_dict = json.load(fp)
        return cls(result_dict)
