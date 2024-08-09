from vcdvcd import VCDVCD

class Trace:

    def __init__(self, tracePath, dutPath, clkPath):
        self.vcd = VCDVCD(tracePath)
        self.dutPath = dutPath

        self.clk_freq = self.vcd[clkPath].tv[2][0]- self.vcd[clkPath].tv[0][0]

    def getTimeFromCycle(self, cycle):
        return cycle * self.clk_freq

    def getFullPath(self, name):
        return self.dutPath + name

    def getFlopStates(self, flops, internal_names, cycle):
        states = dict()
        for i,flop in enumerate(flops):
            val = self.vcd[self.getFullPath(flop)][self.getTimeFromCycle(cycle)]
            if val is None or val == 'X':
                val = 0
            states[internal_names[i]] = val

        return states
