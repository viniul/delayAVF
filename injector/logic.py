
def bit_flip(x: int):
    return int(not(int(x)))

def func_tie_0(*args):
    assert (len(args) == 0)
    return int(0)

def func_tie_1(*args):
    assert (len(args)==0)
    return int(1)

def func_buf(*args):
    assert (len(args) == 1)
    if "X" in args: return "X"
    return int(args[0])


def func_inv(*args):
    assert (len(args) == 1)
    if "X" in args: return "X"
    return bit_flip(int(args[0]))


def func_and(*args):
    assert(len(args) > 1)
    if "X" in args: return "X"
    result = int(args[0])
    for arg in args[1:]:
        result = result & int(arg)
    return result

def func_nor(*args):
    assert(len(args) > 1)
    if "X" in args: return "X"
    result = int(args[0])
    for arg in args[1:]:
        result = result | int(arg)
    return bit_flip(int(result))

def func_nand(*args):
    assert(len(args) > 1)
    if "X" in args: return "X"
    result = int(args[0])
    for arg in args[1:]:
        result = result & int(arg)
    return bit_flip(result)

def func_or(*args):
    assert(len(args) > 1)
    if "X" in args: return "X"
    res = int(args[0])
    for val in args[1:]:
        res |= int(val) #args[i]
    return res
    # return args[0] | args[1]

def func_xnor(*args):
    assert(len(args) > 1)
    if "X" in args: return "X"
    return bit_flip(func_xor(*args))

def func_xor(*args):
    assert(len(args) > 1)
    if "X" in args: return "X"
    # By Chatgpt!
    result = int(args[0])
    for arg in args[1:]:
        result = result ^ int(arg)
    return result

