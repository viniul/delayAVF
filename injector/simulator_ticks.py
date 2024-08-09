from liberty.parser import parse_liberty
import circuitgraph as cg
import networkx as nx
import re
import numpy as np
import collections
import copy
import sys
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx
import params
import math
import circuit
import tqdm
import logic
import simulation_base



class TickBasedSimulator(simulation_base.BaseSimulator):

    def __init__(self, circuit: circuit.delayCircuit,  delays=None, assign=True):
        """
        :param circuit: Circuit 
        :param delays: A dictionary of mappping in edges to step-delays
        """
        super().__init__(circuit,delays,assign)

    def copy(self):
        #return copy.deepcopy(self, copy.deepcopy(self.edge_delay_dict))
        sim = copy.copy(self)
        sim.circuit = copy.copy(self.circuit) 
        return sim

    def simulateCircuitOneCycle(self, inputDict, for_flops=None):
        self.setInputValues(inputDict, init_rest_to_X=False)
        for step in range(self.max_steps):
            self.simulateOneTick(curTick=step)

    def set_initial_flop_value(self, flop, value, step=None):
        if "__QN" in flop:
            # Don't invert QN twice!
            value = logic.bit_flip(value)

        flop_pins = self.circuit.get_flop(flop)
        Q = flop_pins["Q"]
       
        dff_has_qn = 0
        if "QN" in flop_pins.keys():
            dff_has_qn = 1
            QN = flop_pins["QN"]

        for e in self.circuit.c.graph.out_edges(Q):
            if params.SIMULATION_DEBUG:
                print("Setting flop edge", e, "to", value)
            #nx.set_edge_attributes(self.circuit.c.graph, {
            #                        e: {"valCorrect": value}})
            edge_delay = self.circuit.c.graph.get_edge_data(*e)[params.delayStepAttributeString]#nx.get_edge_attributes(
                #self.circuit.c.graph, params.delayStepAttributeString)[e]
            nx.set_edge_attributes(self.circuit.c.graph, {
                e: {"val": [params.FLOP_INITIAL_VALUE]*edge_delay+[value]*(self.max_steps-edge_delay)}})
        
        if dff_has_qn:
            for e in self.circuit.c.graph.out_edges(QN):
                if params.SIMULATION_DEBUG:
                    print("Setting flop edge", e, "to value", logic.bit_flip(value))
                #nx.set_edge_attributes(self.circuit.c.graph, {
                #                        e: {"valCorrect": logic.bit_flip(value)}})
                edge_delay = self.circuit.c.graph.get_edge_data(*e)[params.delayStepAttributeString]#nx.get_edge_attributes(
                    #self.circuit.c.graph, params.delayStepAttributeString)[e]
                nx.set_edge_attributes(self.circuit.c.graph, {
                    e: {"val": [params.FLOP_INITIAL_VALUE]*edge_delay+[logic.bit_flip(value)]*(self.max_steps-edge_delay)}})
            #

    def setInputValues(self, inputDict, init_rest_to_X=False):
        """
        :param: A input dictionary mapping flops to values
        """
        if init_rest_to_X:
            for key in self.circuit.c.inputs():
                if params.SIMULATION_DEBUG:
                    print("Initializing", key, "to X")
                for e in self.circuit.c.graph.out_edges(key):
                    if params.SIMULATION_DEBUG:
                        print("Setting edge", e, " to X")
                    nx.set_edge_attributes(self.circuit.c.graph, {
                                           e: {"valCorrect": "X"}})
                    nx.set_edge_attributes(self.circuit.c.graph, {
                        e: {"val": ["X"]*self.max_steps}})
            for key in self.circuit.c.outputs():
                for e in self.circuit.c.graph.in_edges(key):
                    if params.SIMULATION_DEBUG:
                        print("Setting edge", e, " to X")
                    nx.set_edge_attributes(self.circuit.c.graph, {
                                           e: {"valCorrect": "X"}})
                    nx.set_edge_attributes(self.circuit.c.graph, {
                        e: {"val": ["X"]*self.max_steps}})

        valueDict = {}
        for key, value in inputDict.items():
            if key not in self.circuit.flop_mapping:
                valueDict[key] = value
            else:
                valueDict[self.circuit.flop_mapping[key]["Q"]] = value
                if "QN" in self.circuit.flop_mapping[key]:
                    valueDict[self.circuit.flop_mapping[key]
                              ["QN"]] = logic.bit_flip(value)
        #if "tie_0" not in valueDict:
            # tie_0 seems to be constant 0 in circuitgraph
        valueDict["tie_0"] = 0
        #if "tie_1" not in valueDict:
            # tie_0 seems to be constant 1 in circuitgraph
        valueDict["tie_1"] = 1
        #if "decode_tie_0" not in valueDict:
        valueDict["decode_tie_0"] = 0
        #sif "decode_tie_1" not in valueDict:
            # tie_0 seems to be constant 1 in circuitgraph
        valueDict["decode_tie_1"] = 1
        #for node in self.circuit.c.graph.nodes(): #This is super flow
        #    if "tie_0" in node:
        #        valueDict[node] = 0
        #    if "tie_1" in node:
        #        valueDict[node] = 1

        for key, value in valueDict.items():
            if params.SIMULATION_DEBUG:
                print("Setting input value for ", key)
            for e in self.circuit.c.graph.out_edges(key):
                if params.SIMULATION_DEBUG:
                    print("Setting ", e, "to", value)
                edge_delay = self.circuit.c.graph.get_edge_data(*e)[params.delayStepAttributeString]#nx.get_edge_attributes(
                    #self.circuit.c.graph, params.delayStepAttributeString)[e]
                if params.SIMULATION_DEBUG: print("With delay: ", edge_delay) 
                initialVal = self.circuit.c.graph.get_edge_data(*e)["val"][self.max_steps-1]#nx.get_edge_attributes(
                    #self.circuit.c.graph, "val")[e][self.max_steps-1]
                if params.SIMULATION_DEBUG: print("With initial value: ", initialVal)
                
                nx.set_edge_attributes(self.circuit.c.graph, {
                                       e: {"val": [initialVal]*edge_delay+[value]*(self.max_steps-edge_delay)}})
                nx.set_edge_attributes(self.circuit.c.graph, {
                                       e: {"valCorrect": value}})
            if self.circuit.get_flop(key) is not None:
                self.set_initial_flop_value(key, value)

                # self.circuit.c.graph[key].out
        if params.SIMULATION_DEBUG:
            print("Setting input values done!")

    def simulateOneTick(self, curTick=0):
        if params.SIMULATION_DEBUG: print("SIMULATING TICK ", curTick) 
        for node in self.topo_sort:
            #inputValues = [self.circuit.c.graph.edges()[x]["val"][curTick]
            #               for x in self.circuit.c.graph.in_edges(node)]

            inputValues = [self.circuit.c.graph.get_edge_data(*x)["val"][curTick] for x in self.circuit.c.graph.in_edges(node)]
            if self.circuit.c.type(node) == "input":
                newVal = 0 # TODO: This variable is never used, why is it here?
            elif self.circuit.c.type(node) == "dff":
                # Do nothing for flops
                continue
            elif len(self.circuit.c.graph.in_edges(node)) == 0:
                # Ignore dangling nodes
                continue
            else:
                newVal = self.circuit.c.graph.nodes()[
                    node]["func"](*inputValues) 
                if params.SIMULATION_DEBUG: print("NewVal for", node, "input values",
                      *inputValues, "newVal", newVal, "func", self.circuit.c.graph.nodes()[node]["func"])
                for child in self.circuit.c.graph.out_edges(node):
                    delay_step = self.circuit.c.graph.get_edge_data(*child)[params.delayStepAttributeString] #self.delay_mapping[child] #nx.get_edge_attributes(
                        #self.circuit.c.graph, delayStepString)[child]
                    if params.SIMULATION_DEBUG and curTick == self.max_steps: 
                        print("Cur tick plus delay_step ", curTick+delay_step, "curTick", curTick,
                          "delayStep", delay_step, "maxStep", self.max_steps, child, "input node", node)
                    if curTick+delay_step < self.max_steps:
                        self.circuit.c.graph.get_edge_data(*child)["val"][curTick+delay_step] = newVal
                        #self.circuit.c.graph.edges(
                        #)[child]["val"][curTick+delay_step] = newVal
                        #self.val_mapping[child][curTick+delay_step] = newVal
                    #delayTick = self.getTicks(self.circuit.c.graph.edges()[child]["weight"])
                    #self.circuit.c.graph.edges()[child]["val"][delayTick] = newVal



    def getFlopValues(self, attribute="val", for_flops=None):
        output_mapping = {}
        if for_flops is None:
            for_flops = self.circuit.c.outputs()
        for output_node in for_flops:
            if attribute == "val":
                inputValues = [self.circuit.c.graph.get_edge_data(*x)[attribute][self.max_steps-1]
                               for x in self.circuit.c.graph.in_edges(output_node)]
            else:
                inputValues = [self.circuit.c.graph.edges()[x][attribute]
                               for x in self.circuit.c.graph.in_edges(output_node)]
            if len(inputValues) > 1:
                # print("Output", output_node, "has more than 1 input value",
                #      self.circuit.c.graph.in_edges(output_node))
                pass
            assert(len(inputValues) == 1)
            # print("Value at ", output_node, "is ",
            #      inputValues, "after", self.max_steps, "in edges", self.circuit.c.graph.in_edges(output_node))
            output_mapping[output_node] = inputValues[0]
        return output_mapping
