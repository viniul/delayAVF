from injector import params
import sys
import json
import subprocess
import os
import numpy
from multiprocessing.pool import ThreadPool
import tqdm
import tempfile
import threading
import queue
import collections
import hashlib
from injector import vcdTrace
from injector import util
import sqlitedict
import itertools
import pathlib
import ctypes
import lmdb
import pickle
import hashlib
#import dbm

global_result_cache_dir = "results_cache"
VERILATOR_PATH = os.path.abspath("./build/servant_1.2.1/verilator_tb/Vservant_sim")

protection_scenarios_file = "protection_scenarios.json"



namespace_lock = threading.Lock()
namespace = {}
counters = {}

def aquire_lock(value):
    with namespace_lock:
        if value in namespace:
            counters[value] += 1
        else:
            namespace[value] = threading.Lock()
            counters[value] = 1
    namespace[value].acquire()

def release_lock(value):
    with namespace_lock:
        if counters[value] == 1:
            del counters[value]
            lock = namespace.pop(value)
        else:
            counters[value] -= 1
            lock = namespace[value]
    lock.release()


class VerilatorRunnerThread(threading.Thread):

    def __init__(self,  queue,  *args, **kwargs):
        self.queue = queue
        self.work_dir = tempfile.TemporaryDirectory()
        super().__init__(*args, **kwargs)
        
    def run(self):
        while True:
            try:
                work = self.queue.get(timeout=5) # 5s timeout
            except queue.Empty:
                return
            self.queue.task_done()


 
def compress_JSON(data):
    # Convert serializable data to JSON string
    json_data = json.dumps(data, indent=2)
    # Convert JSON string to bytes
    encoded = json_data.encode("utf-8")
    # Compress
    compressed = gzip.compress(encoded)
    return compressed

class AceNessAnalyser():
    def __init__(self, delay_injection_results_path, hex_payload_path, verilator_timeout, use_fuse_soc, verilator_path, aceness_cache_dir=None, custom_verilator_args=None) -> None:
        self.ace_ness_dict = {} #2d array mapping [flop-list][cycle] to either None aceness answer
        self.delay_ace_ness_dict = {} #2d array mapping [flop-list][cycle] to either None aceness answer
        self.hex_payload_path = hex_payload_path
        if not os.path.exists(self.hex_payload_path):
            raise FileNotFoundError(f"Could not find {os.path.abspath(self.hex_payload_path)}")
        self.verilator_timeout = int(verilator_timeout*1.1) #params.VERILATOR_MAX_TIMEOUT # None #verilator_timeout
        self.use_fuse_soc = use_fuse_soc
        self.ground_truth = ""
        if aceness_cache_dir is None:
            raise Exception("This is not implemented anymore!")
            #local_result_cache_dir = global_result_cache_dir + "_" + hex_shortname + "_" + short_submodule_name
            
        else:
            local_result_cache_dir = aceness_cache_dir
        self.result_cache_dir = local_result_cache_dir #os.path.join(local_result_cache_dir, os.path.splitext(os.path.basename(self.hex_payload_path))[0])

        self.verilator_path = verilator_path
        if self.verilator_path.endswith(".so"):
            print("Self verilator path", self.verilator_path)
            self.libpath = str((pathlib.Path().absolute() / self.verilator_path))
            self.c_lib = ctypes.CDLL(self.libpath)
            self.c_lib.main.restype = ctypes.c_int
            self.use_verilator_library = True
        else:
            self.use_verilator_library = False
        self.fault_scenario_file_path = delay_injection_results_path
        self.protected_flops = None
        if custom_verilator_args is None:
            self.custom_verilator_args = {}
        else:
            self.custom_verilator_args = custom_verilator_args
        
        self.generate_ground_truth()
        #print("Creating aceness db")
        #dbm = tkrzw.DBM()
        #self.ace_ness_db  = dbm.open(os.path.join(self.result_cache_dir, "aceness_results_dbm"), 'c') #dbm.Open(os.path.join(self.result_cache_dir, "aceness_results.db"), True, truncate=True, num_buckets=100)
        #self.ace_ness_db = sqlitedict.SqliteDict(os.path.join(self.result_cache_dir, "aceness_results.db"),  outer_stack=False)
        self.lmdb_env = lmdb.open(str(os.path.join(self.result_cache_dir, "aceness_results_lmdb")), map_size=2485760000*4, subdir=True, max_readers=params.NJOBS*params.NJOBS+100)
    
    #def __del__(self):
        #print("Closing aceness db")
        #self.ace_ness_db.close()
        #print("Closing done")

    def set_protected_flops(self, protected_flops):
        self.protected_flops = set(protected_flops)
    
    def generate_ground_truth(self):
        os.makedirs(self.result_cache_dir, exist_ok=True)
        #if self.use_fuse_soc:
        #    subprocess_args = ["fusesoc", "run", "--target=verilator_tb", "servant", "--uart_baudrate=57600", f"--timeout={self.verilator_timeout}"]
        #    subprocess_args += [f"--firmware={self.hex_payload_path}","--verilator_options=--trace-underscore","--memsize=262144"]
        #    subprocess_args += [f'--output_dir={os.path.abspath(self.result_cache_dir)}']
        #    print(" ".join(subprocess_args))
        #else:
        #    subprocess_args = ["./run_groundtruth_benchmark.sh", os.path.abspath(self.hex_payload_path), str(self.verilator_timeout), os.path.abspath(self.result_cache_dir)]

        #print("Invoking", " ".join(subprocess_args))
        #subprocess.run(subprocess_args)
        if self.use_fuse_soc:
            raise Exception("Not implemented anymore")
        else:
            args_dict = collections.OrderedDict([("timeout", self.verilator_timeout), ("firmware", self.hex_payload_path)]) #("trace-underscore", None),
                         #("output_dir", os.path.abspath(self.result_cache_dir))])
            for key, arg in self.custom_verilator_args.items():
            #    print("Adding arg", key, arg)
                args_dict[key] = arg
        outfilepath = os.path.join(self.result_cache_dir, "output.txt")
        self.call_verilator(args_dict, outfilepath)
        with open(outfilepath,  'rb') as fp:
            self.ground_truth = fp.read()

    def call_verilator(self, arg_dict, outfilepath, debug=False):
        #//From: include/verilated.cpp,https://github.dev/verilator/verilator Max characters in static char string for VL_VALUE_STRING constexpr unsigned VL_VALUE_STRING_MAX_WIDTH = 8192;
        #Store in self.result_cache_dir/results_id
        if debug is True:
            subprocess_args = [self.verilator_path]
            for arg, value in arg_dict.items():
                if value is not None:
                    subprocess_args += [f"+{arg}={str(value)}"]
                    if type(value) == str and len(value)>= 8000:
                        print(f"Arg {arg}")
                        raise Exception(f"Value {value} for {arg} too long")
                else:
                    subprocess_args += [f"+{arg}"]
            print(" ".join(subprocess_args))
        if self.use_verilator_library is False:
            subprocess_args = [self.verilator_path]
            for arg, value in arg_dict.items():
                if value is not None:
                    subprocess_args += [f"+{arg}={str(value)}"]
                    if type(value) == str and len(value)>= 8000:
                        print(f"Arg {arg}")
                        raise Exception(f"Value {value} for {arg} too long")
                else:
                    subprocess_args += [f"+{arg}"]
               
            #print("Invoking", " ".join(subprocess_args))
            
            if self.use_fuse_soc:
                subprocess.run(subprocess_args, stdout=subprocess.DEVNULL)
            else:
                #subprocess.run(subprocess_args, stdout=subprocess.DEVNULL)
                with open(outfilepath, "wb") as fp:
                    proc = subprocess.run(subprocess_args, stdout=fp, stderr=subprocess.PIPE)#subprocess.PIPE)
                    #print(proc.stderr.lower())
                    if b"No flop found matching" in proc.stderr:
                        #raise Exception(f"I think verilator can't find the flop to inject in? STDERR: {proc.stderr} {' '.join(subprocess_args)}")
                        print(f"I think verilator can't find the flop to inject in? STDERR: {proc.stderr} {' '.join(subprocess_args)}")
                    #TODO: Check for errors
        elif self.use_verilator_library is True:
            #print("Calling clib main first", flush=True)
            subprocess_args = []
            for arg, value in arg_dict.items():
                if value is not None:
                    if type(value) == str and len(value)>= 8000:
                        print(f"Arg {arg}, value {value}")
                        raise Exception(f"Value {value} for {arg} too long")
                    subprocess_args += [f"+{arg}={str(value)}"]
                else:
                    subprocess_args += [f"+{arg}"]
            subprocess_args += [f"+stdoutfile={os.path.realpath(outfilepath)}"]
            #print("Subprocess args", subprocess_args)
            L = [arg.encode('utf-8') for arg in subprocess_args]
            L = [self.libpath.encode('utf-8')] + L
            #print("Converting to ctypes")
            arr = (ctypes.c_char_p * len(L))()
            arr[:] = L
            #print("Calling clib main ",  L, flush=True)
            ret = self.c_lib.main(len(L), arr)
            if ret == -1:
                args_hash = hashlib.md5(("".join(subprocess_args)).encode("utf-8")).hexdigest()
                with open(f"/tmp/failed_invocation_{args_hash}.json", "w") as fp:
                    json.dump(subprocess_args, fp)
                #raise Exception(f"I think verilator can't find the flop to inject in? Invocation of library {L}")
                print(f"I think verilator can't find the flop to inject in? Invocation of library {L}")
            #exit(0)
        return ret, subprocess_args

    def call_verilator_and_compare(self, results_id, verilator_arg_dict, debug=False):
        aquire_lock(results_id)
        if debug is False:
            with self.lmdb_env.begin() as txn:
                key = results_id.encode("ascii")
                data = txn.get(key, None)
                if data:
                    release_lock(results_id)
                    return json.loads(data.decode("utf-8"))["isAce"]
        results_dir = os.path.join(self.result_cache_dir,results_id )
        os.makedirs(results_dir, exist_ok=True)
        subprocess_args = []
        if not os.path.exists(os.path.join(results_dir, "output.txt")) or debug is True:
            outfilepath = os.path.join(os.path.abspath(results_dir), 'output.txt')
            ret, subprocess_args = self.call_verilator(verilator_arg_dict, outfilepath, debug)
        with open(os.path.join(results_dir, "output.txt"),  'rb') as fp:
            result = fp.read()
            if self.ground_truth != result:
                ace = True #flop_list is ACE
            else:
                ace = False #flop_list did not matter
        with self.lmdb_env.begin(write=True) as txn:
            key = results_id.encode("ascii")
            data = txn.get(key, None)
            if data is None:
                data = (json.dumps({"output": result.decode("utf-8", errors="backslashreplace"), "isAce": ace, "command_line": " ".join(subprocess_args)})).encode("utf-8")
                txn.put(key, data)
        release_lock(results_id)
        return ace

    def calculate_delay_aceness(self, flop_list, cycle):
        flop_list_file_name = "delay_aceness_"+",".join(sorted(flop_list))+",cycle="+str(cycle)
        if len(flop_list_file_name)>=os.pathconf('/', 'PC_NAME_MAX'):
            hash_digest = hashlib.sha256(flop_list_file_name.encode("utf-8")).hexdigest()
            flop_list_file_name = flop_list_file_name[:(os.pathconf('/', 'PC_NAME_MAX')-len(hash_digest))]+hash_digest
        if self.use_fuse_soc:
            arg_dict = collections.OrderedDict([("uart_baudrate", "57600"),("timeout", self.verilator_timeout), ("firmware", self.hex_payload_path),
                #("trace-underscore", None), 
                ("delay_simulation", None),
                ("memsize", "262144"), ("bad_flop",",".join(sorted(flop_list))), 
                ("bad_cycle", int(cycle))])
                #("output_dir", os.path.abspath(results_dir))])
        else:
            arg_dict = collections.OrderedDict([("timeout", self.verilator_timeout), ("firmware", self.hex_payload_path), #("trace-underscore", None),
                    ("bad_flop",",".join(sorted(flop_list))), ("bad_cycle", int(cycle)), ("delay_simulation", None)]) # ("output_dir", os.path.abspath(results_dir)), 
            for key, arg in self.custom_verilator_args.items():
                arg_dict[key] = arg
        ace = self.call_verilator_and_compare(flop_list_file_name, arg_dict)
        return ace 

    def calculate_aceness(self, flop_list, cycle, debug=False):
        
        flop_list_file_name = ",".join(sorted(flop_list))+",cycle="+str(cycle)
        if len(flop_list_file_name)>=os.pathconf('/', 'PC_NAME_MAX'):
            hash_digest = hashlib.sha256(flop_list_file_name.encode("utf-8")).hexdigest()
            flop_list_file_name = flop_list_file_name[:(os.pathconf('/', 'PC_NAME_MAX')-len(hash_digest))]+hash_digest
        if self.use_fuse_soc:
            arg_dict = collections.OrderedDict([("uart_baudrate", "57600"),("timeout", self.verilator_timeout), ("firmware", self.hex_payload_path),
                #("trace-underscore", None), 
                ("memsize", "262144"), ("bad_flop",",".join(sorted(flop_list))), 
                ("bad_cycle", int(cycle))]) 
                #("output_dir", os.path.abspath(results_dir))]) #VU: output_dir does not do anything?
        else:
            arg_dict = collections.OrderedDict([("timeout", self.verilator_timeout), ("firmware", self.hex_payload_path), #("trace-underscore", None),
                    ("bad_flop",",".join(sorted(flop_list))), ("bad_cycle", int(cycle))])
            #, ("output_dir", os.path.abspath(results_dir))]) ##VU: output_dir does not do anything?
            for key, arg in self.custom_verilator_args.items():
                arg_dict[key] = arg
        if debug is True:
            print("Calling caclulating aceness flop list ", arg_dict.items())
        ace = self.call_verilator_and_compare(flop_list_file_name, arg_dict, debug)
        return ace 
    
    def get_or_ace_ness(self, flop_list, cycle):
        for f in flop_list:
            if self.get_ace_ness([f], cycle) == True:
                return True
        return False
        
    def get_ace_ness(self, flop_list, cycle):
        #   print("Getting aceness of ", flop_list, "at cycle", cycle)
        #flop_list = [util.process_flop_name(flop) for flop in flop_list]


        if self.protected_flops:
            flop_list = list(set(flop_list)-set(self.protected_flops))
        if len(flop_list) == 0:
            return False
        failing_flops_id = ",".join(sorted(flop_list))
        if failing_flops_id not in self.ace_ness_dict:
            self.ace_ness_dict[failing_flops_id] = {}
        if cycle not in self.ace_ness_dict[failing_flops_id]:
            self.ace_ness_dict[failing_flops_id][cycle] = self.calculate_aceness(flop_list, cycle)
        #print("Returning ",self.ace_ness_dict[failing_flops_id][cycle])
        #if self.ace_ness_dict[failing_flops_id][cycle] == True:
        #    exit(0)
        #print("get_ace_ness returning ",self.ace_ness_dict[failing_flops_id][cycle], "for", failing_flops_id, cycle)
        return self.ace_ness_dict[failing_flops_id][cycle]

    def get_delay_ace_ness(self, flop_list, cycle):
        #   print("Getting aceness of ", flop_list, "at cycle", cycle)
        #flop_list = [util.process_flop_name(flop) for flop in flop_list]
        if self.protected_flops:
            flop_list = list(set(flop_list)-set(self.protected_flops))
        if len(flop_list) == 0:
            return False
        failing_flops_id = "delay_aceness_"+",".join(sorted(flop_list))
        if failing_flops_id not in self.delay_ace_ness_dict:
            self.delay_ace_ness_dict[failing_flops_id] = {}
        if cycle not in self.delay_ace_ness_dict[failing_flops_id]:
            self.delay_ace_ness_dict[failing_flops_id][cycle] = self.calculate_delay_aceness(flop_list, cycle)
        #print("Returning ",self.ace_ness_dict[failing_flops_id][cycle])
        #if self.ace_ness_dict[failing_flops_id][cycle] == True:
        #    exit(0)
        #print("get_ace_ness returning ",self.ace_ness_dict[failing_flops_id][cycle], "for", failing_flops_id, cycle)
        return self.delay_ace_ness_dict[failing_flops_id][cycle]

    def cache_result_per_edge(self, edge, edge_result):
        for cycle, failing_flops in edge_result["dynamically_reachable_per_cycle"].items():
                #print("Cycle", cycle, "failing flops", failing_flops, flush=True)
                if self.protected_flops:
                    failing_flops = set(failing_flops) - self.protected_flops
                #print("Getting aceness for ", cycle, "and flop list", failing_flops, flush=True)
                aceness = self.get_ace_ness(failing_flops, cycle) #What do with this now?
                #print("Aceness for ", cycle, "flop list", failing_flops, "aceness", aceness)
                for flop in failing_flops:
                    aceness = self.get_ace_ness([flop], cycle) #What do with this now?
                    set_without_flop = set(failing_flops) - set(flop)
                    aceness_group_without_flop = self.get_ace_ness(list(set_without_flop), cycle) # Get aceness of group without this flop. Want to know if still ace
        pbar.update(1)


    def run_analysis(self):
        with open(self.fault_scenario_file_path) as fp:
            result_dict = json.load(fp)
        analysis_result_dict = result_dict["analysis_results"]
        #for edge, edge_result_per_delay in analysis_result_dict.items():
        #    self.cache_result_per_edge(edge,edge_result_per_delay)
        print("Running analaysis")
        for delay in analysis_result_dict.keys():
            jobs = [(sim_item["edge"], sim_item) for sim_item in analysis_result_dict[delay]]
            global pbar
            pbar = tqdm.tqdm(total=len(jobs))
            with ThreadPool(params.NJOBS) as pool:
                _= list(pool.starmap(self.cache_result_per_edge, jobs))
            

    def get_new_sim_result(self, sim_result):
        edge = sim_result["edge"]
        #print("Getting result for ", edge)
        #new_dynamic_per_cycle_set = {}
        #print("for cycles", sim_result["dynamically_reachable_per_cycle"].items())
        for cycle, failing_flops in sim_result["dynamically_reachable_per_cycle"].items():
            if len(failing_flops)==0:
                continue
            sim_result["dynamically_reachable_per_cycle"][cycle] = {"ace" : self.get_ace_ness(failing_flops, cycle), "dynamically_reachable": list(failing_flops)}
            #, "per_flop_aceness": {flop: {"uniqueAce": self.get_ace_ness([flop], cycle), "groupAceWithoutFlop": self.get_ace_ness(list(set(failing_flops)-set(flop)), cycle)} for flop in failing_flops}, 
            #                                                "per_flop_sdcness": {flop: self.get_sdc_ness([flop], cycle) for flop in failing_flops}}
            #print("Done")
        #pbar.update(1)
        #print("Returning sim result")
        return sim_result
        #print(result_dict)


    def get_result(self):
        #print("Done now dumping results")
        result_dict = None
        with open(self.fault_scenario_file_path) as fp:
            result_dict = json.load(fp)
            analysis_result = result_dict["analysis_results"]
        #results_db = sqlitedict.SqliteDict("test") 
        for delay in analysis_result.keys():
            sim_results_list = analysis_result[delay]
            result_dict["analysis_results"][delay] = []
            for new_sim_res in map(self.get_new_sim_result, sim_results_list):
                result_dict["analysis_results"][delay].append(new_sim_res)#new_sim_results_list
        return result_dict
    
    def dump_result(self, out_file=None):
        result_dict = self.get_result()
        if out_file is None:
            out_file = self.fault_scenario_file_path + "_including_aceness_and_sdcness.json"
        print(" \n Now writing to file", out_file, flush=True)
        with open(out_file, "w") as fp:
            json.dump(result_dict, fp)

    @classmethod
    def from_config_dict(cls, config_dict):
        synth_file = config_dict["synth_file"]
        sub_synth_file = config_dict.get("sub_synth_file", None)
        submodule_name = config_dict.get("submodule_name", None)
        short_submodule_name = config_dict.get("short_submodule_name", None)
        pdk_path = config_dict["pdk_path"]
        #trace_path = config_dict["trace_path"]
        top_path = config_dict["top_path"]
        clk_path = config_dict["clk_path"]
        outfile_path = config_dict.get("out", "fault_scenarios.json")
        add_global_delay = config_dict.get("add_global_delay", True) # False to add relative delay
        delay_min = float(config_dict.get("delay_min", 0.1))
        delay_max = float(config_dict.get("delay_max", 1))
        delay_range_step = int(config_dict.get("delay_range_steps", 10))
        hex_payload = config_dict["hex_payload"]
        hex_shortname = None # config_dict["hex_shortname"]
        verilator_path = util.get_verilator_path_from_config_dict(config_dict)
        delay_injection_results_path = util.get_delay_injection_results_path(config_dict)
        #config_dict.get("verilator_path", VERILATOR_PATH)
        #verilator_timeout = config_dict["verilator_timeout"]
        use_fuse_soc = config_dict.get("use_fuse_soc", False)
        #aceness_cache_dir = config_dict["aceness_cache_dir"]
        custom_verilator_args = config_dict.get("custom_verilator_args", None)
        with open(util.get_metadata_path_from_config_dict(config_dict)) as fp:
            metadata = json.load(fp)
            verilator_timeout = metadata["verilator_timeout"]
        aceness_cache_dir = util.get_aceness_cache_dir(config_dict) #util.get_protection_rates_path(config_dict)
        aceness_analyser = cls(delay_injection_results_path, hex_payload, verilator_timeout, use_fuse_soc, verilator_path , aceness_cache_dir, custom_verilator_args)
        return aceness_analyser
