import sys

outputs = []

with open(sys.argv[1]) as f:
    decl_line = 0
    module_line = 0
    for i, line in enumerate(f.readlines()):
        if "output " in line:
            split = line.split(" ")[3]
            outputs.append(split.replace("\n","").replace(";", ""))

        if "wire" in line or "output" in line:
            decl_line = i
        if "endmodule" in line:
            module_line = i
               
print(outputs)
print(decl_line)
print(module_line)
   
with open(sys.argv[2], 'w') as f:
    with open(sys.argv[1]) as g:

        for x in range(decl_line+1):
            f.write(g.readline())

        for i, output in enumerate(outputs):
            f.write("wire " + output + "_pre ;\n")
            f.write("wire _qn_" + str(i) + " ;\n")

        for i,output in enumerate(outputs):
            f.write("  DFFRQ_X1 \_"+output.replace("\\", "")+"_ (\n")
            f.write(".CLK(!"+sys.argv[3]+"),\n")
            f.write(".RN(1'b1),\n")
            f.write(".D(" + output + "_pre ),\n")
            f.write(".Q(" + output + " ),\n")
            f.write(".QN(_qn_" + str(i) + " )\n")
            f.write(");\n")

        for x in range(module_line-decl_line+1):
            line = g.readline()
            for output in outputs:
                if output in line:
                    # Don't overwrite in cases where we're instantiating a submodule, since the pin name doensn't change!
                    if "."+output in line and line.count(output) == 1: continue
                    line = (output+"_pre ").join(line.rsplit(output, 1))
            f.write(line)
