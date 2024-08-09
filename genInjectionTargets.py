import sys
import os
from injector import util
import json
#from suffix_trees import STree

outputs = []

dut_lines = []
arg_lines = []
print("Injectring into ", sys.argv[1])
print("Current workdir", os.getcwd())
with open(sys.argv[4]) as fp:
    circuit_out = json.load(fp)
all_flops = [util.process_flop_name(x["name"]) for x in circuit_out["flops"]]
with open(sys.argv[1]) as f:    
    for i, line in enumerate(f.readlines()):
        #print("line", line)
        #if "___DOT__Q" in line:
        if "___DOT__QN" in line:
            dut_line = line.replace("\n", "").split("CData/*0:0*/ ")[1]
            arg_line = dut_line.replace("__05b", "[").replace("__05d", "]").replace('cpu__DOT__cpu__DOT__', '').replace('__DOT__','_').replace(';', '').replace('_Q', '').replace('uut_picorv32_core_','')
            arg_line = arg_line.replace("sim_top_", "")
            #print("arg", arg_line)
            # TODO: This doesn't work for IBEX 
            #if '_o_' in arg_line:
            #    arg_line = arg_line.replace('_o_','o_').replace('__Q', '')[:-1]
            dut_lines.append(dut_line)
            arg_lines.append(arg_line)

file_string = ""
dump_string = ""

#print("ALLFLOPS", all_flops)

injected_flops = set()
for i in range(len(dut_lines)):
    #print("ARG", arg_lines[i])
    #if arg_lines[i].endswith("_N"):
    #    continue
    flop = util.process_flop_name(arg_lines[i])
    #print("flop", arg_lines[i])
    if flop not in all_flops:
        #best_match_size = 0
        #best_match_flop = ""
        found_match = False
        for potential_matching_flop in all_flops:
            if potential_matching_flop.replace("\\", "") in flop:
                print(f"Matching {flop} to {potential_matching_flop}")
                flop = potential_matching_flop
                found_match = True
                break
        if found_match is False:
            print(f"Could not find match for {flop}, ignoring!")
            pass

            #st = STree.STree([flop, potential_matching_flop])
            #lcs = st.lcs() # "abc"
            #match = SequenceMatcher(None, flop, potential_matching_flop).find_longest_match()
            #if len(lcs) > best_match_size:
            #    best_match_size = len(lcs)
            #    best_match_flop = potential_matching_flop
    injected_flops.add(flop)
    file_string += ("case hash_string(\"" + flop + "\"):\n")
    file_string += ("Q = &(dut->" + dut_lines[i][:-2] + ");\n")
    file_string += ("QN = &(dut->" + dut_lines[i][:-1] + ");\n")
    file_string += ("break;\n")
    if "cpuregs" in dut_lines[i][:-1]:
        dump_string += ("fprintf(stdout, \"" + flop + ": %d\\n\", " + "(top->picorv32_wrapper->" + dut_lines[i][:-1] + "));\n")

for f in circuit_out["interesting_flops"]:
    if f not in injected_flops:
        raise Exception(f"Interesting flop {f} does not have matching injection switch case statement!")
        #print(f"Interesting flop {f} does not have matching injection switch case statement!")

f = open("interesting_flops.txt", "w")
f.write('\n'.join(arg_lines))
f.close()

f = open(sys.argv[2]) 
data = f.read()
f.close()

newdata = data.replace("/*REPLACE*/", file_string)
newdata = newdata.replace("/*REPLACEREAD*/", file_string)
newdata = newdata.replace("/*REPLACEWRITE*/", file_string)
# If architecture check is enabled...
#if (sys.argv[5] == "1"):
#    newdata = newdata.replace("/*REPLACEDUMP*/", dump_string)

f = open(sys.argv[3], 'w')
f.write(newdata)
f.close()


