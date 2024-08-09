import os
from vcdvcd import VCDVCD
import sys
import json
import tqdm

class vcdTrace:

    def __init__(self, tracePath, dutPath, clkPath):
        print("Loading vcdTrace..")
        self.vcd = VCDVCD(tracePath)
        print("Loading vcdTrace done")
        self.dutPath = dutPath
        #print("Clock path", self.vcd[clkPath])
        self.clk_freq = self.vcd[clkPath].tv[2][0]- self.vcd[clkPath].tv[0][0]
        self.cached_flop_states = {}

    def getTimeFromCycle(self, cycle):
        # Return the negative edge
        return int((cycle+0.5) * self.clk_freq)

    def getCycleFromTime(self, time):
        return int(time /self.clk_freq) #Round Down

    def getFullPath(self, name):
        #print("Getting full path", self.dutPath + name)
        return self.dutPath + name

    def getFlopStates(self, flops, internal_names, cycle):
        #print("Vcd signals", self.vcd.signals)
        states = dict()
        for i,flop in enumerate(flops):
            #print("Getting value for flop", flop)
            if internal_names is not None and internal_names[i] in self.cached_flop_states:
                if cycle in self.cached_flop_states[internal_names[i]]:
                    states[internal_names[i]] = self.cached_flop_states[internal_names[i]][cycle]
                    continue
            #print("Getting flop state for", flop, flush=True)
            val = self.vcd[self.getFullPath(flop)][self.getTimeFromCycle(cycle)]
            if val is None or val == 'X':
                val = 0
            if internal_names is not None:
                states[internal_names[i]] = val
            if internal_names is not None and internal_names[i] not in self.cached_flop_states:
                self.cached_flop_states[internal_names[i]] = {}
            if internal_names is not None:
                self.cached_flop_states[internal_names[i]][cycle] = val
        return states

    def compareWith(self, other_trace):
        for cycle in range(61810,self.getNumCycles()):
            print(f"\r At cycle {cycle}", end="")
            for i,flop in enumerate(self.vcd.signals):
                val_this = self.vcd[flop][self.getTimeFromCycle(cycle)]
                val_other = other_trace.vcd[flop][self.getTimeFromCycle(cycle)]
                if val_this != val_other:
                    print(f"\nValue at {flop} is {val_this} but {val_other} in compare trace, cycle {cycle}")

    def getNumCycles(self):
        #print("Endtime", self.vcd.endtime)
        return self.getCycleFromTime(self.vcd.endtime)
    
    def timeout(self):
        return self.vcd.endtime
    
    def get_toggle_rate(self, flop):
        count = 0
        val_before = None
        for cycle in range(0,self.getNumCycles()):
            val_this = self.vcd[self.getFullPath(flop)][self.getTimeFromCycle(cycle)]
            if val_before is None:
                count += 1
                val_before = val_this
            elif val_before != val_this:
                count += 1
                val_before = val_this
        #print("Toggle rate for", flop, "is ", count, "total toggles", "and", count/self.getNumCycles())
        return count/self.getNumCycles()

                #if val_this != val_other:
                #    print(f"\nValue at {flop} is {val_this} but {val_other} in compare trace, cycle {cycle}")

            

if __name__ == "__main__":
    with open(sys.argv[1]) as fp:
        config_dict = json.load(fp)
    synth_file = config_dict["synth_file"]
    sub_synth_file = config_dict.get("sub_synth_file", None)
    submodule_name = config_dict.get("submodule_name", None)
    short_submodule_name = config_dict.get("short_submodule_name", None)
    pdk_path = config_dict["pdk_path"]
    #trace_path = config_dict["trace_path"]
    trace_path = os.path.join(config_dict["output_dir"], "testbench_trace.vcd")
    top_path = config_dict["top_path"]
    clk_path = config_dict["clk_path"]
    outfile_path = config_dict.get("out", "fault_scenarios.json")
    add_global_delay = config_dict.get("add_global_delay", True) # False to add relative delay
    delay_min = float(config_dict.get("delay_min", 0.1))
    delay_max = float(config_dict.get("delay_max", 1))
    #t = vcdTrace(trace_path,top_path,clk_path)
    
    this_trace = vcdTrace(trace_path, top_path, clk_path) #vcdTrace("data/waveforms/hello_vincent.vcd")
    print("Num Cycles", this_trace.getNumCycles())
    #print("value", this_trace.getFlopStates(["o_dbus_sel[2]"], ["o_dbus_sel[2]"], 0))
    #vcdTrace("multi_bit_fault_decode.vcd", top_path, clk_path)
    #this_trace.compareWith(vcdTrace("no_bit_fault.vcd", top_path, clk_path))
    #For ['decode__199_', 'decode__193_', 'decode__188_', 'decode__191_', 'decode__197_'] cycle 61825 or ace true, groupAce false
    #trace_path = 'trace.vcd'
    #top_path = "TOP.servant_sim.dut."
    #clkPath = "TOP.servant_sim.dut.cpu.cpu.clk"
    #print("Reading first trace")
    #t = VcdTrace(trace_path,top_path,clkPath)
    #print("Reading Compare trace")
    #other_trace = VcdTrace("trace_bad.vcd",top_path,clkPath)
    #print("Now comparing traces")
    #t.compareWith(other_trace,10)
    #print("Comparing trace")
    #t.compareWith(other_trace,500)
    #t.getFlopStates(flops=["o_rreg1[3]"],internal_names="test",cycle=1)
