from liberty.parser import parse_liberty
import circuitgraph as cg
import networkx as nx
import re
import numpy as np
import collections
from injector import params
from injector import logic
from pqdm.processes import pqdm
import pickle
import tqdm
import copy
import json
from injector import util
from multiprocessing.pool import ThreadPool
import concurrent.futures
#import graphblas_algorithms as ga

cg.addable_types.append("dff")
cg.supported_types.append("dff")

class delayCircuit:

    def __init__(self, topVerilogPath, libertyPath, submoduleVerilogPath = None, submoduleName = None, simulate_all=True, just_dump=False):

        # Construct a circuit element
        self.c = cg.Circuit()

        self.dff_capacitance = 0
        self.buf_capacitance = 0
        self.dff_delay_model = None
        self.buf_delay_model = None
        self.dff_has_qn = 0
        self.paths_dict = None
        self.edge_to_path = None
        self.flop_mapping = {}
        self.flop_groups = collections.defaultdict(list)
        self.submodule_name = submoduleName
        self.just_dump =  just_dump
        self.TR = None
        # Read the liberty file
        # Populate circuit black-boxes from library file
        blackboxList = []
        cellList = []
    
        self.library = parse_liberty(open(libertyPath).read())
        for cell_group in self.library.get_groups('cell'):
            name = cell_group.args[0]
            print("Parsing cell group", name, flush=True)
            in_list = []
            out_list = []
            for pin_group in cell_group.get_groups('pin'):
                pin_name = pin_group.args[0]
                if pin_group['direction'] == "output":
                    out_list.append(pin_name)
                elif pin_group['direction'] == "input":
                    in_list.append(pin_name)

            blackboxList.append(cg.BlackBox(name, inputs=in_list, outputs=out_list))

        if submoduleName != None:
            print("Submodule name: ", submoduleName)
            print("Blackboxlist", blackboxList)
            subcircuit = cg.from_file(submoduleVerilogPath, blackboxes=blackboxList)
            subcircuit_bb = cg.BlackBox(submoduleName, inputs=subcircuit.inputs(), outputs=subcircuit.outputs())
            print("BBINPUTS: ", subcircuit_bb.inputs())

            # Mark all nodes in the submodule as part of the region of interest
            for node in subcircuit.graph.nodes():
                subcircuit.graph.nodes[node]["externInterestNode"] = 0
                subcircuit.graph.nodes[node]["interestNode"] = 1
                subcircuit.graph.nodes[node]["simuReq"] = 1

            for edge in subcircuit.graph.edges():
                subcircuit.graph.edges[edge]["interestEdge"] = 1

            blackboxList.append(subcircuit_bb)
        
        # Construct the circuit from synthesized module
        self.c = cg.from_file(topVerilogPath, blackboxes=blackboxList)
        print("Output", self.c.outputs())

        if submoduleName != None:
            # Set all non-submodule nodes as "uninteresting" for now
            for node in self.c.graph.nodes():
                self.c.graph.nodes[node]["externInterestNode"] = 0
                self.c.graph.nodes[node]["interestNode"] = 0
                self.c.graph.nodes[node]["simuReq"] = 0

            for edge in self.c.graph.edges():
                self.c.graph.edges[edge]["interestEdge"] = 0

            #TODO: This is a bit hardcoded for SERV atm
            #print(self.c.blackboxes)
            self.c.fill_blackbox(submoduleName.split("_")[-1], subcircuit)
        #if simulate_all is True:
        if not submoduleName: 
            #Mark all nodes as interesting
            print("Marking all nodes as interesting")
            for node in self.c.graph.nodes():
                self.c.graph.nodes[node]["externInterestNode"] = 1
                self.c.graph.nodes[node]["interestNode"] = 1
                self.c.graph.nodes[node]["simuReq"] = 1
            for edge in self.c.graph.edges():
                self.c.graph.edges[edge]["interestEdge"] = 1

        # Replace black-box circuit elements with logical elements
        # This also takes the timing information from the liberty file
        for cell_group in self.library.get_groups('cell'):
            name = cell_group.args[0]
            print("Processing cell group", name, flush=True)
            m = cg.Circuit(cell_group.args[0])
            logic_type = re.search(r"[a-zA-Z]*",name).group()

            if name == params.DFF_REPLACE:
                for pin_group in cell_group.get_groups('pin'):
                    if pin_group['direction'] == "input":
                        self.dff_capacitance = pin_group['capacitance']
                    if pin_group['direction'] == "output":
                        self.dff_delay_model = pin_group.get_groups("timing")[0].get_groups("cell_rise")[0] 
                    if "QN" in pin_group.args[0]:
                        self.dff_has_qn = 1

            if name == params.BUF_REPLACE:
                for pin_group in cell_group.get_groups('pin'):
                    if pin_group['direction'] == "input":
                        self.buf_capacitance = pin_group['capacitance']
                        print("SETCAP:")
                        print(self.buf_capacitance)
                    if pin_group['direction'] == "output":
                        self.buf_delay_model = pin_group.get_groups("timing")[0].get_groups("cell_rise")[0] 
                
            # TODO: Support more gates (these are sufficient for now)
            if logic_type not in ["BUF", "INV", "AND", "OAI", "NOR", "NAND", "OR", "AOI", "AND", "OAI", "MUX", "XNOR", "XOR"]: 
                continue
            if logic_type == "INV":
                logic_type = "NOT"

            in_list = []
            out_list = []
            
            # First, add all of the input pins
            for pin_group in cell_group.get_groups('pin'):
                pin_name = pin_group.args[0]
                if pin_group['direction'] == "input":
                    in_list.append(m.add(pin_name, "input"))
                    m.graph.nodes()[pin_name]["capacitance"] = pin_group['capacitance']
                    if params.CIRCUIT_BUILD_DEBUG: print("Debug Capacitance Pin Name", pin_name, m.graph.nodes()[pin_name]["capacitance"]) 
            print("Adding output pins now", flush=True)
            # Then, add the output pin 
            onlyOne = False
            for pin_group in cell_group.get_groups('pin'):
                pin_name = pin_group.args[0]
                if pin_group['direction'] == "output":
                    assert(onlyOne == False)
                    onlyOne = True
                    m.add(pin_name, logic_type.lower(), output=True, fanin=in_list)
                    m.graph.nodes()[pin_name]["delay_model"] = pin_group.get_groups("timing")[0].get_groups("cell_rise")[0]
                    #print("Pin name", pin_name, in_list)

            print("Replacing all blackbox instances", flush=True)
            # Replace all blackbox instances with this new subcircuit 
            for key,value in list(self.c.blackboxes.items()):
                if value.name == name:
                    interestList = []
                    for x in value.io():
                        if self.c.graph.nodes[key + "." + x]["interestNode"]:
                            interestList.append(x)

                    self.c.fill_blackbox(key, m)

                    for x in interestList:
                        self.c.graph.nodes[key + "_" + x]["interestNode"] = 1
        print("Computing transitive reduction", flush=True)
        #self.TR = nx.transitive_reduction(self.c.graph)
        # Explicitly convert to ga.Graph
        #self.ga_rep = ga.Graph.from_networkx(self.c.graph)
        print("Mapping out region of interest", flush=True)
        interesting_nodes = [node for node in self.c.graph.nodes if self.c.graph.nodes[node]["interestNode"] == 1]
        fanout_nodes = {child for parent, child, _ in nx.edge_bfs(self.c.graph, interesting_nodes, orientation="original")}
        #print("Fanout nodes", fanout_nodes)
        fanin_nodes = {parent for parent, child, _ in nx.edge_bfs(self.c.graph, interesting_nodes, orientation="reverse")}
        for node in fanin_nodes.union(fanout_nodes):
            #print("fanout nodes", fanout_nodes)
            self.c.graph.nodes[node]["externInterestNode"] = 1
            self.c.graph.nodes[node]["simuReq"] = 1
        #for node in tqdm.tqdm(self.c.nodes()):
            
            #if params.CIRCUIT_BUILD_DEBUG: print("NODE:", node)
        #    if self.c.graph.nodes[node]["interestNode"] == 1:
        #        for faninNode in self.c.transitive_fanin(node):
        #            if params.CIRCUIT_BUILD_DEBUG: print("faninNode", faninNode)
        #            self.c.graph.nodes[faninNode]["externInterestNode"] = 1
        #            self.c.graph.nodes[faninNode]["simuReq"] = 1
        #        for fanoutNode in self.c.transitive_fanout(node):
        #            if params.CIRCUIT_BUILD_DEBUG: print("fanoutNode", fanoutNode)
        #            self.c.graph.nodes[fanoutNode]["externInterestNode"] = 1
        #            self.c.graph.nodes[fanoutNode]["simuReq"] = 1    
        #fanoutNodes = {child for parent, child in nx.edge_bfs(self.c.graph, interesting_nodes, orientation='original')}
        
        #def mark_as_extern_interesting(node_arg):
        #    if self.c.graph.nodes[node_arg]["interestNode"] == 1:
        #        for faninNode in self.transitive_fanin(node_arg):
        #            if params.CIRCUIT_BUILD_DEBUG: print(faninNode)
        #            self.c.graph.nodes[faninNode]["externInterestNode"] = 1
        #            self.c.graph.nodes[faninNode]["simuReq"] = 1
        #        for fanoutNode in self.transitive_fanout(node_arg):
        #            if params.CIRCUIT_BUILD_DEBUG: print(fanoutNode)
        #            self.c.graph.nodes[fanoutNode]["externInterestNode"] = 1
        #            self.c.graph.nodes[fanoutNode]["simuReq"] = 1
        # Finally, mark all nodes which are connected to the region of interest 
        #with concurrent.futures.ThreadPoolExecutor() as executor:
        #    _ = list(tqdm(executor.map(mark_as_extern_interesting, self.c.nodes()), total=len(self.c.nodes())))
            #futures = []
            #for node in tqdm.tqdm(self.c.nodes()):
            #    futures.append(executor.submit(mark_as_extern_interesting, node))
            #concurrent.futures.wait(futures) 
        #for node in tqdm.tqdm(self.c.nodes()):
            #if params.CIRCUIT_BUILD_DEBUG: print("NODE:", node)
        #    if self.c.graph.nodes[node]["interestNode"] == 1:
        #        for faninNode in self.transitive_fanin(node):
        #            if params.CIRCUIT_BUILD_DEBUG: print(faninNode)
        #            self.c.graph.nodes[faninNode]["externInterestNode"] = 1
        #            self.c.graph.nodes[faninNode]["simuReq"] = 1
        #        for fanoutNode in self.transitive_fanout(node):
        #            if params.CIRCUIT_BUILD_DEBUG: print(fanoutNode)
        #            self.c.graph.nodes[fanoutNode]["externInterestNode"] = 1
        #            self.c.graph.nodes[fanoutNode]["simuReq"] = 1
        
        #print("Mapping out external region of interest", flush=True)

        #def mark_with_simureq(node, c):
        #    if self.c.graph.nodes[node]["externInterestNode"] == 1:
        #        for faninNode in self.transitive_fanin(node):
        #            self.c.graph.nodes[faninNode]["simuReq"] = 1
        extern_interested_nodes = [node for node in self.c.graph.nodes if self.c.graph.nodes[node]["externInterestNode"] == 1]
        fanin_nodes = {parent for parent, child, _ in nx.edge_bfs(self.c.graph, extern_interested_nodes, orientation="reverse")}
        for node in fanin_nodes:
            self.c.graph.nodes[node]["simuReq"] = 1
            
        #with concurrent.futures.ThreadPoolExecutor() as executor:
        #    _ = list(tqdm(executor.map(mark_with_simureq, self.c.nodes()), total=len(self.c.nodes())))
            #futures = []
            #for node in tqdm.tqdm(self.c.nodes()):
            #    futures.append(executor.submit(mark_with_simureq, node))
            #concurrent.futures.wait(futures)

        #for node in tqdm.tqdm(self.c.nodes()):
        #    if self.c.graph.nodes[node]["externInterestNode"] == 1:
        #        for faninNode in self.c.transitive_fanin(node):
        #            print("faninNode", faninNode, "of ", node)
        #            self.c.graph.nodes[faninNode]["simuReq"] = 1
        
        #if True: #params.CIRCUIT_BUILD_DEBUG: 
        #    for node in self.c.nodes():
        #        print("Node: %s, interninteresting: %d, externinteresting: %d" %(node, self.c.graph.nodes()[node]["interestNode"], self.c.graph.nodes()[node]["externInterestNode"]))
        
        print("Mapping out edge region of interest", flush=True)
        for edge in self.c.graph.edges():
            if not self.submodule_name:
                self.c.graph.edges[edge]["interestEdge"] = 1
            if "interestEdge" not in self.c.graph.edges[edge].keys() : 
                self.c.graph.edges[edge]["interestEdge"] = 0

        #print("Preparing flop groups")
        for node in self.c.outputs():
            #print("Preparing node", node)
            self.flop_groups[util.get_group_for_flop(node)].append(node)
        
        #for node in sorted(self.c.graph.nodes()):
        #    for fanout in sorted(self.c.fanout(node)):
        #        if ("capacitance" in self.c.graph.nodes()[fanout]):
        #            print("Node", node, "Fanout", fanout, self.c.graph.nodes()[fanout]["capacitance"])

    def transitive_fanin(self, node):
        #if self.TR is None:
        #    self.TR = nx.transitive_reduction(self.c.graph)
        #return nx.ancestors(node)
        return nx.ancestors(self.ga_rep, node)
    
    def transitive_fanout(self, node):
        #if self.TR is None:
        #    self.TR = nx.transitive_reduction(self.c.graph)
        #return nx.descendants(node)
        return nx.descendants(self.ga_rep, node)
    

    def copy(self):
        newCircuit = copy.deepcopy(self)

        #newCircuit.c.graph = self.c.graph.deepcopy()
        return newCircuit

    def prepare(self, remove_nodes=False):
        
        for _ in range(5):
            self.simplifyBufs()
        
        for b in self.c.blackboxes:
            self.convert_blackbox_to_dff(b)
        
        for edge in self.c.graph.edges():
            print("FINAL EDGE: ", edge, flush=True)
            nx.set_edge_attributes(self.c.graph, {edge: {params.WEIGHT_ATTRIBUTE: 0}})

        print("Applying DFF Output Capacitances...", flush=True)
        self.applyDFFOutputCaps()
        
        if self.just_dump is False:
            # We just dump the circuit - we can skip this step
            print("Applying Value Arrays...", flush=True)
            self.applyValueArrays()
            print("Assigning Logic...", flush=True)
            self.assignLogic()
        print("Computing Delay Weights...", flush=True)
        self.computeDelayWeights()
        self.calculate_interesting_flops()
        #if self.submodule_name:
        #    print("Pruning External Nodes...", flush=True)
        #    self.pruneExternalNodes()
   
        #self.dumpInterestingNodes()
        #print("Flop groups", [(key, len(value)) for key, value in self.flop_groups.items()])
        #for edge in self.c.graph.edges():
        #    print("Interesting?", edge, self.c.graph.edges()[edge]["interestEdge"])

    def calculate_interesting_flops(self):
        self.interesting_flops = []
        self.extern_interesting_flops = []
        for node in self.c.graph.nodes():
            if self.c.graph.nodes[node].get("interestNode", None) == 1 and self.c.is_output(node):
                processed_flop_name = util.process_flop_name(node)
                self.interesting_flops.append(processed_flop_name)
                self.extern_interesting_flops.append(processed_flop_name)
            elif "externInterestNode" in self.c.graph.nodes()[node].keys() and self.c.graph.nodes()[node]["externInterestNode"] == 1 and self.c.is_output(node): 
                processed_flop_name = util.process_flop_name(node)
                self.extern_interesting_flops.append(processed_flop_name)

    def dumpInterestingNodes(self):
        self.interesting_flops = []
        with open("interesting_flops.txt", "w") as interesting_f:
            for node in self.c.graph.nodes():
                if "externInterestNode" in self.c.graph.nodes()[node].keys() and self.c.graph.nodes()[node]["externInterestNode"] == 1 and self.c.is_output(node):
                    processed_flop_name = util.process_flop_name(node)
                    #print("Node before", node)
                    #print("Writing to interesting_flops.txt", processed_flop_name)#node.replace("\\","").replace("dff_", "").replace("_in", ""))
                    interesting_f.write(processed_flop_name+"\n")#node.replace("\\","").replace("dff_", "").replace("_in", "")+"\n")
                    self.interesting_flops.append(processed_flop_name)#node.replace("\\","").replace("dff_", "").replace("_in", ""))
                                                                        

    # Prunes nodes not combinatorially connected to the submodule under test
    def pruneExternalNodes(self):
        removeNodes = []
        for node in self.c.graph.nodes():
            if "simuReq" in self.c.graph.nodes[node] and self.c.graph.nodes[node]["simuReq"] == 0:
                removeNodes.append(node)          
                for g in self.flop_groups.keys():
                    if node in self.flop_groups[g]:
                        self.flop_groups[g].remove(node)

        if params.CIRCUIT_BUILD_DEBUG: print("Pruning irrelevant nodes: ", removeNodes) 
        self.c.remove(removeNodes)

    # Removes all buffers (e.g. circuit elements with fanin==fanout==1) to simplify analysis
    # 
    def simplifyBufs(self):
        for node in list(self.c.nodes()):
            if self.c.is_output(node):
                # Don't simplify outputs 
                continue
            if self.c.type(node) == "buf" and len(self.c.fanin(node)) == 1 and len(self.c.fanout(node)) == 1:
                if "capacitance" not in self.c.graph.nodes()[node]:
                    self.c.graph.nodes()[node]["capacitance"] = self.buf_capacitance

                fanin = self.c.fanin(node).pop()
                fanout = self.c.fanout(node).pop()

                if self.c.type(fanin) == "bb_output":
                    continue

                interestEdge = self.c.graph[fanin][node]["interestEdge"] | self.c.graph[node][fanout]["interestEdge"] 

                #if self.c.type(fanin) == "buf":
                #    raise Exception("Two sequential buffers")
                #print("BUFFCAP:", self.buf_capacitance)
                # Propagate capacitance values to merged cell
                if("capacitance" in self.c.graph.nodes()[fanout]):
                    self.c.graph.nodes()[fanout]["capacitance"] += self.c.graph.nodes()[node]["capacitance"] # node["capacitance"] #self.buf_capacitance 
                else:
                    self.c.graph.nodes()[fanout]["capacitance"] = self.c.graph.nodes()[node]["capacitance"] #node["capacitance"] #self.buf_capacitance 

                if params.CIRCUIT_BUILD_DEBUG: print("REMOVING %s" %(node))
                if params.CIRCUIT_BUILD_DEBUG: print("BRIDGING %s:%s" %(fanin, fanout))
                self.c.remove(node)
                self.c.connect(fanin,fanout)
                self.c.graph[fanin][fanout]["interestEdge"] = interestEdge
                assert(self.c.graph.get_edge_data(*(fanin, fanout))["interestEdge"] == interestEdge)
                #result_dict["injectIntoEdges"].append((edge[0],edge[1])))


    def applyDFFOutputCaps(self):
        for node in list(self.c.nodes()):
            if self.c.is_output(node):
                self.c.graph.nodes[node]["capacitance"] = self.dff_capacitance
    
    def applyValueArrays(self,):
        for edge in list(self.c.edges()):
            self.c.graph.edges()[edge]["val"] = [0] * 100000
            self.c.graph.edges()[edge]["nominalVal"] = [0] * 100000

    def assignLogic(self):
        for node in list(self.c.nodes()):
            cell_type = self.c.type(node)
            if cell_type == "buf":
                self.c.graph.nodes[node]["func"] = logic.func_buf
            elif cell_type == "not":
                self.c.graph.nodes[node]["func"] = logic.func_inv
            elif cell_type == "and":
                self.c.graph.nodes[node]["func"] = logic.func_and
            elif cell_type == "nor":
                self.c.graph.nodes[node]["func"] = logic.func_nor
            elif cell_type == "nand":
                self.c.graph.nodes[node]["func"] = logic.func_nand
            elif cell_type == "or":
                self.c.graph.nodes[node]["func"] = logic.func_or
            elif cell_type == "and":
                self.c.graph.nodes[node]["func"] = logic.func_and
            elif cell_type == "xnor":
                self.c.graph.nodes[node]["func"] = logic.func_xnor
            elif cell_type == "xor":
                self.c.graph.nodes[node]["func"] = logic.func_xor
            elif cell_type == "0":
                self.c.graph.nodes[node]["func"] = logic.func_tie_0
            elif cell_type == "1":
                self.c.graph.nodes[node]["func"] = logic.func_tie_1
            elif cell_type in {"input", "dff"}:
                pass #No logic assigned
            elif cell_type in {"x"}:
                pass #No logic assigned
            else:
                raise Exception(f"Cell type {cell_type} not handled for {node}?")


    def computeDelayWeights(self):
        for node in sorted(list(self.c.nodes())):
            delay_model = None

            if params.PATH_DEBUG: print("Computing delay weights for node: ", node)

            if "delay_model" not in self.c.graph.nodes()[node].keys():
                if self.c.graph.nodes[node]["type"] == "input":
                    delay_model = self.dff_delay_model
                elif self.c.graph.nodes[node]["type"] == "buf":
                    delay_model = self.buf_delay_model
                else:
                    if params.PATH_DEBUG: print("Missing delay model for:")
                    if params.PATH_DEBUG: print(self.c.graph.nodes()[node])
                    continue

            total_cap = 0

            if self.c.is_output(node):
                if params.PATH_DEBUG: print("Output node, no fanout delays required")
                continue

            if len(self.c.fanout(node)) == 0:
                if params.PATH_DEBUG: print("Node has no fanout, ignoring")
                continue

            for fanout in self.c.fanout(node):
                if ("capacitance" in self.c.graph.nodes()[fanout]):
                    fan_cap = self.c.graph.nodes()[fanout]["capacitance"]
                    if params.PATH_DEBUG: print("Adding capacitive fanout for node ", fanout, ": ", fan_cap)
                    total_cap += fan_cap
            
            if total_cap == 0:
                if params.PATH_DEBUG: 
                    print("Warning: 0 capacitance node!")
                
                continue

            #TODO: Assume lowest transition time for now
            if delay_model == None:
                delay_model = self.c.graph.nodes()[node]["delay_model"] 

            index1 = np.array(delay_model.get_array("index_1").flatten())
            index2 = np.array(delay_model.get_array("index_2").flatten())

            values = np.array(delay_model.get_array("values"))
            if params.PATH_DEBUG: print("Node ", node, "gets index2", index2, "values", values[0].flatten(), "evaluate at ", total_cap)
            delay = np.interp(total_cap, index2, values[0].flatten())
            if params.PATH_DEBUG: print("Node ", node, "gets delay", delay)
            #print("Node ", node, "gets delay", delay)
            for edge in self.c.graph.out_edges(node):
                nx.set_edge_attributes(self.c.graph, {edge: {params.WEIGHT_ATTRIBUTE: delay}})

    def calculate_paths(self, xin_arg=None, xout_arg=None):
        if self.paths_dict == None:
            if params.PATH_DEBUG: print("Calculating paths")
            self.paths_dict = collections.defaultdict(dict)
            self.edge_to_path = collections.defaultdict(list)
            for xin in self.c.inputs():
                for xout in self.c.outputs():
                    paths = list(nx.all_simple_paths(self.c.graph, xin, xout))
                    self.paths_dict[xin][xout] = paths
                    for p in paths:
                        for edge in nx.utils.pairwise(p):
                            self.edge_to_path[edge].append(p)
        if xin_arg is not None:
            return self.paths_dict[xin_arg][xout_arg]

    def get_affected_paths(self, edges):
        """
        For a given set of edges, get the paths those edges are on
        """
        paths = []
        if self.edge_to_path is None:
            self.calculate_paths()
        for e in edges:
            paths += self.edge_to_path[e]
        return paths


    def calculate_path_lengths(self, graph=None, edges=None, weightAttr=params.WEIGHT_ATTRIBUTE):
        """
        :param circuit: A weighted circuit
        :return: A dictionary that for each input-output combination 
        lists all paths including their length 
        """
        paths_weight_dict = collections.defaultdict(lambda: collections.defaultdict(dict))
        self.paths_weight_dict_flat = {}
        longest_path = ("", 0)
        if graph is None:
            graph = self.c.graph
        if edges is None:
            edges = graph.edges()
        #for xin in self.c.inputs():
        #    for xout in self.c.outputs():
        #print("Edges", edges, "Self.get_affected_paths", self.get_affected_paths(edges))
        for p in self.get_affected_paths(edges):
            xin = p[0]
            xout = p[-1]
            #print("Inputs", self.c.inputs())
            #paths = list(self.calculate_paths(xin, xout))
            #for p in paths:
            weight = nx.classes.function.path_weight(
                graph, p, weight=weightAttr)
            if params.LONGEST_PATH_DEBUG: print("Path", p, weightAttr, weight)
            path_identifier = "-->".join([str(e) for e in p])
            paths_weight_dict[xin][xout][path_identifier] = weight
            self.paths_weight_dict_flat[path_identifier] = weight
            if weight > longest_path[1]:
                longest_path = (path_identifier, weight)
        if params.LONGEST_PATH_DEBUG: print("Longest path in circuit", longest_path)
        return paths_weight_dict, longest_path
    
    def trace_delay_defect(self, delay_defects, ASSUMED_CLOCK_PERIOD=0.5, weightAttr=params.WEIGHT_ATTRIBUTE):
        """
        Trace the effect of a given set of delay defects on a circuit
        :param delay_defects: A dictionary mapping gates and their added delay
        """
        self.calculate_paths()

        if params.TRACE_DEBUG: print('\n\n+++ Tracing effects of delay defect: ', delay_defects, ' +++')

        edges = list(delay_defects.keys())
        old_weight_mapping = {}
        paths_normal_circuit,_ = self.calculate_path_lengths(graph=self.c.graph,edges=edges, weightAttr=weightAttr)
        for edge, added_delay in delay_defects.items():
            oldWeight = nx.get_edge_attributes(self.c.graph, weightAttr)[edge]
            nx.set_edge_attributes(self.c.graph, {edge: {weightAttr: added_delay + oldWeight}})
            old_weight_mapping[edge] = oldWeight
        paths_delayed_circuit,_ = self.calculate_path_lengths(graph=self.c.graph, edges=edges, weightAttr=weightAttr)
        for edge, old_weight in old_weight_mapping.items():
            nx.set_edge_attributes(self.c.graph, {edge: {weightAttr: old_weight}})
        delayed_flip_flops = set()
        #print("Affected paths", self.get_affected_paths(edges))
        for p in self.get_affected_paths(edges):
            xin = p[0]
            xout = p[-1]
            for p_identifier, normal_weight in paths_normal_circuit[xin][xout].items():
                delayed_weight = paths_delayed_circuit[xin][xout][p_identifier]
                if params.TRACE_DEBUG: print("Delayed weight", delayed_weight, "normal_weight", normal_weight, "path", p_identifier)
                if delayed_weight > normal_weight:
                    if params.TRACE_DEBUG:
                        print("#### Delayed path found ####")
                        print(f"Path between {xin} and {xout} delayed")
                        print(f"Weight before {normal_weight}, weight after {delayed_weight} through delaying edge {delay_defects}")
                        print(f"Path identifer {p_identifier}")
                        print("### ####")
                    if delayed_weight > ASSUMED_CLOCK_PERIOD:
                        if params.TRACE_DEBUG: print(f"    !! Flip-flop {xout} received its data too late")
                        delayed_flip_flops.add(xout)

        return delayed_flip_flops

    def get_flop(self, flop):
        if flop in self.flop_mapping:
            return self.flop_mapping[flop]
        return None
        for key, value in self.flop_mapping.items():
            if flop in value.values():
                return value
        #assert 0, f"for flop {flop}"
        return None

    def validate_correctness(self):
        for node in self.c.nodes():
            if node not in self.c.inputs():
                if len(self.c.graph.in_edges(node))==0 and self.c.graph.nodes()[node]["type"] not in {"0","1"}:
                    raise Exception(f"Node {node} is not an input but has no in edges {self.c.graph.nodes()[node]}")
                    

    def convert_blackbox_to_dff(self, name):
        if params.CIRCUIT_BUILD_DEBUG: print("convert_blackbox_to_dff Name:", name) 
        circuit = self.c
        blackbox = circuit.blackboxes[name]
        blackbox_node_name_out_Q = f"dff_{name}_Q_out"
        blackbox_node_name_out_QN = f"dff_{name}_QN_out"
        blackbox_node_name_in = f"dff_{name}_in"
        circuit.add(blackbox_node_name_out_Q, "input")
        print("HASQN: \n", self.dff_has_qn)
        #raise Exception("")
        if self.dff_has_qn: 
            circuit.add(blackbox_node_name_out_QN, "input")
            flop_dict = {"IN": blackbox_node_name_in,"Q":blackbox_node_name_out_Q, "QN": blackbox_node_name_out_QN}
        else:
            flop_dict = {"IN": blackbox_node_name_in,"Q":blackbox_node_name_out_Q}

        self.flop_mapping[f"dff_{name}"] = flop_dict
        self.flop_mapping[blackbox_node_name_in] = flop_dict
        self.flop_mapping[blackbox_node_name_out_Q] = flop_dict
        if self.dff_has_qn: 
            self.flop_mapping[blackbox_node_name_out_QN] = flop_dict
        #[TODO VU I hardcoded a capacitawnce for 1.148038, actual we need to get capacitance for blackbox.name]
        circuit.graph.nodes()[blackbox_node_name_out_Q]["capacitance"] = 1.148034 #TODO: Get capacitance for cell group blackbox.name
        if self.dff_has_qn: 
            circuit.graph.nodes()[blackbox_node_name_out_QN]["capacitance"] = 1.148034 #TODO: Get capacitance for cell group blackbox.name
        circuit.add(blackbox_node_name_in, "dff", output=True)
        for bb_input in blackbox.inputs():
            if bb_input == "CLK": # Ignore clock
                circuit.remove(f"{name}.CLK")
                continue
            elif bb_input == "CK": 
                circuit.remove(f"{name}.CK")
                continue
            elif bb_input == "RN": 
                circuit.remove(f"{name}.RN")
                continue
            elif bb_input == "R": 
                circuit.remove(f"{name}.R")
                continue
            else:
                for x in circuit.graph.in_edges(f"{name}.{bb_input}"):
                    print("ATTACHING:", x, flush=True)
                    circuit.connect(x[0], f"{blackbox_node_name_in}")

                circuit.graph.nodes()[f"{blackbox_node_name_in}"]["interestNode"] = circuit.graph.nodes()[f"{name}.{bb_input}"]["interestNode"] 
                circuit.graph.nodes()[f"{blackbox_node_name_in}"]["externInterestNode"] = circuit.graph.nodes()[f"{name}.{bb_input}"]["externInterestNode"] 
                circuit.graph.nodes()[f"{blackbox_node_name_in}"]["simuReq"] = circuit.graph.nodes()[f"{name}.{bb_input}"]["simuReq"] 

                for x in circuit.graph.in_edges(f"{name}.{bb_input}"):
                    circuit.graph[x[0]][f"{blackbox_node_name_in}"]["interestEdge"] = circuit.graph.edges()[x]["interestEdge"]

                circuit.remove(f"{name}.{bb_input}")
        for bb_output in blackbox.outputs():
            if bb_output not in ["Q", "QN"]:
                circuit.remove(f"{name}.{bb_output}")
                continue
            else:
                flop_out_pin_name = blackbox_node_name_out_Q if bb_output == "Q" else blackbox_node_name_out_QN
                out_nodes = list(circuit.graph.neighbors(f"{name}.{bb_output}"))
                #print(out_nodes)
                for x in out_nodes:
                    #print(x, flush=True)
                    interestEdge = circuit.graph[f"{name}.{bb_output}"][x]["interestEdge"]
                    circuit.disconnect(f"{name}.{bb_output}", x)
                    #print("Connecting: ", f"{flop_out_pin_name}",x)
                    circuit.connect(f"{flop_out_pin_name}", x)
                    self.flop_groups[util.get_group_for_flop(x)].append(f"{name}") # For blackboxes, we group the flops according to their Q pin
                    circuit.graph[f"{flop_out_pin_name}"][x]["interestEdge"] = interestEdge

                    if params.CIRCUIT_BUILD_DEBUG:  print("Connecting: ",f"{flop_out_pin_name}", x)

                circuit.graph.nodes()[f"{flop_out_pin_name}"]["interestNode"] = circuit.graph.nodes()[f"{name}.{bb_output}"]["interestNode"] 
                circuit.graph.nodes()[f"{flop_out_pin_name}"]["externInterestNode"] = circuit.graph.nodes()[f"{name}.{bb_output}"]["externInterestNode"] 
                circuit.graph.nodes()[f"{flop_out_pin_name}"]["simuReq"] = circuit.graph.nodes()[f"{name}.{bb_output}"]["simuReq"] 

                

                circuit.remove(f"{name}.{bb_output}")
    
    def path_length_distribution(self, longest_path_weight):
        path_weight_dict, _ = self.calculate_path_lengths()
#        with open("out.pickle", "wb") as fp:
#            pickle.dump(dict(path_weight_dict), fp)
        #exit(0)
        weights_flat = []
        edge_to_path_dict = collections.defaultdict(list)
        for xin in path_weight_dict.keys():
            for xout in path_weight_dict[xin].keys():
                for _, weight in path_weight_dict[xin][xout].items():
                    weights_flat.append(weight)
        for edge in self.c.edges():
            for p in self.edge_to_path[edge]:
                path_identifier = "-->".join([str(node) for node in p])
                #if self.paths_weight_dict_flat[path_identifier] >= 0.9 * longest_path_weight:
                edge_to_path_dict[edge].append((path_identifier, self.paths_weight_dict_flat[path_identifier]))
        #print(edge_to_critical_path_count)
        #for edge in self.c.edges():
        #    if edge_to_path_count[edge] > 1:
        #        print(f"Edge {edge} is involved in {edge_to_critical_path_count[edge] } near critical paths")
        return weights_flat, edge_to_path_dict

    def dump_circuit_to_json(self, out_path):
        #elements = list(self.c.outputs()) + list(self.c.inputs())
        print("Dumping circuit to json", flush=True)
        result_dict = {}
        result_dict["gates"] = []
        result_dict["flops"] = []
        result_dict["edges"] = []
        result_dict["inject_into_edges"] = []
        result_dict["flop_groups"] = self.flop_groups
        result_dict["interesting_flops"] = self.interesting_flops
        result_dict["extern_interesting_flops"] = self.extern_interesting_flops
        #print("Interesting flops", self.interesting_flops)
        input_nodes = set(self.c.inputs())
        output_nodes = set(self.c.outputs())
        for node in self.c.graph.nodes():
            #print("Node is ", node, "in input nodes", (node in input_nodes))
            node_object = {}
            node_object["name"] = node
            cell_type = self.c.type(node)
            node_object["cell_type"] = cell_type
            if node in input_nodes or node in output_nodes:
                node_object["direction"] = "IN" if (node in input_nodes) else "OUT"
                pins = self.get_flop(node)
                if pins:
                    continue
                    #node_object["pins"] = pins
                #print("Getting node", node, "pins", pins)
                result_dict["flops"].append(node_object)
                #print("Getting node", node)
            #if cell_type in {"dff"}:
            #    if self.get_flop(node) is None:
            #        result_dict["flops"].append(node_object)
                #continue #TODO: Ignore dff types because anyway we will ontice them in the output pins?
                #, "input"}:
            #elif cell_type=="input":
            #    pins = self.get_flop(node)
            #    if pins:
            #        node_object["pins"] = pins
            #    result_dict["flops"].append(node_object)
            else:
                result_dict["gates"].append(node_object)
        for node, pins in self.flop_mapping.items():
            if node in pins.values():
                #We ignore those nodes, as we will add them later anyway
                continue
            node_object = {}
            node_object["name"] = node
            node_object["pins"] = pins
            result_dict["flops"].append(node_object)
        for edge in self.c.graph.edges():
            edge_object = {}    
            edge_object["from"] = edge[0]
            edge_object["to"] = edge[1]
            edge_object["weight"] = self.c.graph.get_edge_data(*edge)[params.WEIGHT_ATTRIBUTE] #nx.get_edge_attributes(self.c.graph, params.WEIGHT_ATTRIBUTE)[edge]
            result_dict["edges"].append(edge_object)
            if self.c.graph.get_edge_data(*edge)["interestEdge"] == 1:
                fan_out_edge = set(self.c.transitive_fanout(edge[1]))
                intersect_with_output = fan_out_edge.intersection(set(self.c.outputs()))
                if len(intersect_with_output)>0:
                    result_dict["inject_into_edges"].append((edge[0],edge[1]))
                else:
                    print(f"Ignoring wire {edge}, no fan out!", fan_out_edge,intersect_with_output )
                    
        #print("Circuit inputs", self.c.inputs())
        #print("Circuit outputs", self.c.outputs())
        #print(json.dumps(result_dict, indent=2))
        #result_dict["interesting_flops"] = list({util.process_flop_name(node["name"]) for node in result_dict["flops"]})
        with open(out_path, "w") as fp:
            json.dump(result_dict, fp)



def single_trace(circuit, edge, delay, cycle_time, weightAttr=params.WEIGHT_ATTRIBUTE):
    
    if params.DELAY_AT_GATE_OUTPUT:
        delay_dict = {}
        for edge in circuit.c.graph.out_edges(edge):
            delay_dict[edge] = delay

    else:
        delay_dict = {edge: delay} 
    
    delayed_flip_flops = circuit.trace_delay_defect(delay_dict, cycle_time, weightAttr)

    return delayed_flip_flops



