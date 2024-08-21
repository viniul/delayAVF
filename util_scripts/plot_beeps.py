import sys
import os
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import itertools
import pandas as pd
from scipy.stats import gmean
import glob
module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(module_dir)
from injector import util
#matplotlib.use('pgf')
#import tikzplotlib

#import matplotlib2tikz
def set_size(width_pt, fraction=1, subplots=(1, 1)):
    """Set figure dimensions to sit nicely in our document.

    Parameters
    ----------
    width_pt: float
            Document width in points
    fraction: float, optional
            Fraction of the width which you wish the figure to occupy
    subplots: array-like, optional
            The number of rows and columns of subplots.
    Returns
    -------
    fig_dim: tuple
            Dimensions of figure in inches
    """
    # Width of figure (in pts)
    fig_width_pt = width_pt * fraction
    # Convert from pt to inches
    inches_per_pt = 1 / 72.27

    # Golden ratio to set aesthetic figure height
    golden_ratio = (5**.5 - 1) / 2

    # Figure width in inches
    fig_width_in = fig_width_pt * inches_per_pt
    # Figure height in inches
    fig_height_in = fig_width_in * golden_ratio * (subplots[0] / subplots[1])
    return (fig_width_in, fig_height_in)

def plot_avf(structures, avf, method, ax, idx, nolabel, printsubfig, decimal_places=12, bar_placement=2.5):
    # Bar width
    bar_width = 0.1
    #print("Size", set_size(240))
    # Set up figure and axis
    #fig, ax = plt.subplots(figsize=(3, 4))#plt.subplots(figsize=(12,12))
    
    #print("Structures", structures, "avf", avf, "benchmark", method)

    # Create bars for delay_fault_avf
    if not nolabel:
        bars1 = ax.bar(np.arange(len(structures))+idx*bar_width, avf, bar_width, label=method)
        if printsubfig: ax.text(0.5, -0.33, 'a)', transform=ax.transAxes, fontsize=11, ha='center')
    else:
        bars1 = ax.bar(np.arange(len(structures))+idx*bar_width, avf, bar_width)
        if printsubfig: ax.text(0.5, -0.33, 'b)', transform=ax.transAxes, fontsize=11, ha='center')

    for idx, (bar, avf) in enumerate(zip(bars1, avf)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height ,
                f'{avf:.{decimal_places}f}'.rstrip("0").rstrip("."), ha='center', va='bottom', rotation=90, fontsize=7.5)
    #print("Structures", structures, "avf", avf, "benchmark", method)

    # Create bars for particle_strike_avf
    #bars2 = ax.bar(np.arange(len(structures)) + bar_width, particle_strike_avf, bar_width, label='sAVF')

    # Add numbers above each bar
    #for bars, avf_values, method in zip([bars1, bars2], [delay_fault_avf, particle_strike_avf], [['wAVF']*len(delay_fault_avf),['sAVF']*len(particle_strike_avf)]):
    #    for bar, avf, method in zip(bars, avf_values, method):
    #        height = bar.get_height()
    #        ax.text(bar.get_x() + bar.get_width() / 2, height / 2 ,
    #                f'{avf:.5f}'.rstrip("0").rstrip("."), ha='center', va='bottom', rotation=90)


    # Set labels, title, and legend
    
    #ax.set_title('AVF Values for Different Structures')
    ax.set_xticks(np.arange(len(structures)) + bar_width*bar_placement*4 , rotation=45, ha='center', labels=structures)
    ax.set_xticklabels(structures, fontsize=7.5)

    #ax.legend()

def listdirs(path):
    path_arr = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    if path_arr is None:
        return None
    else:
        print(path_arr)
        return sorted(path_arr)

def parse_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def get_delays(path, target_structure_name):
    for benchmark_name in listdirs(path):
        #if "libstrstr" not in benchmark_name:
        #    continue
        benchmark_path = os.path.join(path, benchmark_name)

        for structure_name in listdirs(benchmark_path):
            if target_structure_name != structure_name:
                continue
            structure_path = os.path.join(benchmark_path, structure_name)
            json_file_path = os.path.join(structure_path, 'protection_rates.json')

            if os.path.exists(json_file_path):
                res_dict = parse_json_file(json_file_path)
                return res_dict.keys()
    raise Exception("Not delays found?")


def process_directories(path, delay_percentage):
    out_dict_wire_avf = {}
    out_dict_particle_avf = {}
    #out_dict_single_flop_avf = {}
    #out_dict_multi_flop_avf = {}

    for config_dict_path in glob.glob(path+"/*.dict"):
        with open(config_dict_path) as fp:
            config_dict = json.load(fp)
        benchmark_name = os.path.splitext(os.path.basename(config_dict["hex_payload"]))[0]
        #if "libstrstr" not in benchmark_name:
        #    continue
        #print("Benchmark name", benchmark_name)
        structure_name = config_dict["short_submodule_name"]
        if config_dict["ecc_on"]:
            structure_name = structure_name+"_ecc"
        protection_rates_path = util.get_protection_rates_path(config_dict)
        #if "ibfibcall" not in benchmark_name:
        #    continue
        #if benchmark_name in ["libbubblesort" ,"crc", "liblevenshtein" ,"matmult", "libstrstr_test"]:
        #    continue
        #benchmark_path = os.path.splitext(os.path.basename(self.hex_payload_path))[0]
        if benchmark_name not in out_dict_wire_avf:
            out_dict_wire_avf[benchmark_name] = {}
            out_dict_particle_avf[benchmark_name] = {}

        #for structure_name in listdirs(benchmark_path):
            #print("AAAA", structure_name, benchmark_name)
            #delays = get_delays(path, structure_name)
            #delay = list(delays)[delay_idx]
            #structure_path = os.path.join(benchmark_path, structure_name)
        #json_file_path = os.path.join(structure_path, 'protection_rates.json')

        if os.path.exists(protection_rates_path):
            #print(protection_rates_path)
            res_dict = parse_json_file(protection_rates_path)
            if "clk_period" in config_dict:
                max_steps = config_dict["clk_period"]
            else:
                max_steps = res_dict["clk_period"]
            delay = str(int(max_steps*delay_percentage))
            if delay in res_dict["delayavf_per_delay"]:
                res_dict = res_dict["delayavf_per_delay"][delay]
            else:
                print(f"Skipping {protection_rates_path} because it does not have delay {delay}")
                continue #return None
            print(f"Got {res_dict['delayAVF']} delay {delay_percentage} out {max_steps} for {benchmark_name}/{structure_name}")
            out_dict_wire_avf[benchmark_name][structure_name] = res_dict["delayAVF"]
            #out_dict_particle_avf[benchmark_name][structure_name] = res_dict["particle_strike_avf_extern"]
            #if "single_flop_micro_arch_approx_avf" in res_dict:
            #    if benchmark_name not in out_dict_single_flop_avf:
            #        out_dict_single_flop_avf[benchmark_name] = {}
            #    out_dict_single_flop_avf[benchmark_name][structure_name] = res_dict["single_flop_micro_arch_approx_avf"]
            #if "fan_out_micro_arch_approx_avf" in res_dict:
            #    if benchmark_name not in out_dict_multi_flop_avf:
            #        out_dict_multi_flop_avf[benchmark_name] = {}
            #    out_dict_multi_flop_avf[benchmark_name][structure_name] = res_dict["fan_out_micro_arch_approx_avf"]
                
    out_dict_wire_avf = {key: value for key, value in out_dict_wire_avf.items() if value}
    #out_dict_particle_avf = {key: value for key, value in out_dict_particle_avf.items() if value}
    #out_dict_wire_avf = {key: value for key, value in out_dict_wire_avf.items() if value}
    return out_dict_wire_avf#, out_dict_particle_avf, out_dict_single_flop_avf, out_dict_multi_flop_avf

def get_particle_geomeans(benchmark_path_data):
    out_dict_particle_avf = process_directories_particle_avf(benchmark_path_data)
    #max_value = max(list(itertools.chain.from_iterable([list(out_dict_particle_avf[benchmark].values()) for benchmark in out_dict_particle_avf.keys()])))
    avf_benchmark_dict = {}
    structures = ["register","loadstore", "prefetch", "register_ecc"]
    structures = list(structures) #list(avf_dict["delay"][list(avf_dict["delay"].keys())[0]].keys())
    values_per_structure = {k: [] for k in structures}
    geomean_per_structure = {}
    for idx, benchmark in enumerate(out_dict_particle_avf.keys()):
        current_data_dict = out_dict_particle_avf[benchmark]
        for structure in structures: #avf_dict[method][benchmark].keys(): # Needs to be determinsitic ordering!
            if structure in current_data_dict:
                values_per_structure[structure].append(current_data_dict[structure])
    for structure in structures:
        geomean_per_structure[structure] = gmean(values_per_structure[structure])
    return geomean_per_structure
        
def plot_particle_vs_delay(particle_geomean_dict, geomean_structure_delay_dict, delay_list):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5.7,2.45), sharey=True, sharex=True)
    #ax1.set_xlabel('Structure',loc='center')
    #ax2.set_xlabel('Structure',loc='center')
    ax1.set_ylabel('Normalized AVF Values',loc='center')
    ax1.set_title("wAVF")
    ax2.set_title("sAVF")
    target_structures = ["register", "loadstore", "prefetch", "register_ecc"]
    #for method in ["particle", "delay"]:
    #    if method == "delay":
    #          curr_ax = ax1
    #          nolabel = False
    ##    else:
    #          curr_ax = ax2
    #          nolabel = True
    max_geomean = 0
    for structure, per_delay_dict in geomean_structure_delay_dict.items():
        if structure in target_structures:
            #print(list(itertools.chain.from_iterable(per_delay_dict.values())))
            max_geomean = max(max_geomean, max(per_delay_dict.values()))
    print("Max gemeoan", max_geomean)
    for idx, delay in enumerate(delay_list):
        #delay = delay_list[idx]
        #print(geomean_structure_delay_dict[structure].values())
        #geomean_list =[[entry[delay]] for entry in geomean_structure_delay_dict.values()]
        geomean_list = []
        for structure in target_structures:
            #entry = unscaled_delay_structure_dict[structure]
            this_struct_geomean = geomean_structure_delay_dict[structure][delay] #gmean(entry[delay])
            geomean_list.append(this_struct_geomean) 
        print("geoeamn list", geomean_list)
        flattened_geomean_list = np.array(geomean_list)/max_geomean
        print("Flattened geoeamn list", flattened_geomean_list)
        plot_avf(target_structures, flattened_geomean_list, int(delay_list[idx]*100), ax1, idx, False, True, 4, bar_placement=1)
    flattened_geomean_list_particle = []
    max_geomean_particle = max(particle_geomean_dict.values())
    for structure in target_structures:
        flattened_geomean_list_particle.append(particle_geomean_dict[structure] / max_geomean_particle)
    plot_avf(target_structures, flattened_geomean_list_particle, ["Geomean"], ax2, 0, True, True, 4, bar_placement=1)
    fig.legend(loc='upper center', bbox_to_anchor=(0.5, 1.024), ncol=6, fancybox=True)
    #plot_avf(structures, delay_fault_avf,"histogram_delay_fault.png", "wAVF", ax1)
    #plot_avf(structures, particle_strike_avf,"histogram_particle_strike.png", "sAVF", ax2)


    plt.tight_layout()
    plt.subplots_adjust(top=0.8, bottom=0.25)
    plt.savefig("beeps_plots/particle_vs_delay.pdf")
    plt.close()
             
        #avf_benchmark_dict[benchmark] = list(zip(structures, avf_values))
        #plot_avf(structures, avf_values, benchmark, ax, idx, False, True)

def plot_external_particle_avf(benchmark_path_data):
    out_dict_particle_avf = process_directories_particle_avf(benchmark_path_data)
    max_value = max(list(itertools.chain.from_iterable([list(out_dict_particle_avf[benchmark].values()) for benchmark in out_dict_particle_avf.keys()])))
    avf_benchmark_dict = {}
    structures = ["register","loadstore", "prefetch"]
        
    structures = list(structures) #list(avf_dict["delay"][list(avf_dict["delay"].keys())[0]].keys())
    fig, ax = plt.subplots()
    geomeans = {}
    for idx, benchmark in enumerate(out_dict_particle_avf.keys()):
        avf_values = []
        unscaled_avf_values = []
        current_data_dict = out_dict_particle_avf[benchmark]
        for structure in structures: #avf_dict[method][benchmark].keys(): # Needs to be determinsitic ordering!
            if structure in current_data_dict and max_value>0:
                avf_values.append(current_data_dict[structure]/max_value)
                unscaled_avf_values.append(current_data_dict[structure])
            else:
                avf_values.append(0)
                unscaled_avf_values.append(0)
        #avf_benchmark_dict[benchmark] = list(zip(structures, avf_values))
        plot_avf(structures, avf_values, benchmark, ax, idx, False, True)
    fig.legend(loc='upper center', bbox_to_anchor=(0.5, 1.02), ncol=6, fancybox=True)
    plt.tight_layout()
    plt.subplots_adjust(top=0.775, bottom=0.22)
    plt.savefig(f"beeps_plots/intern_particle_strike.pdf",)
    plt.close()
    #df = pd.DataFrame.from_dict(avf_dict["delay"], orient='index')
    #df.to_csv(f'beeps_plots/output_{delay}.csv')

def micro_plot(path):
    #delays = get_delays(benchmark_path_data)
    avf_delay_benchmark_dict = {}
    unscaled_avf_delay_benchmark_dict = {}
    unscaled_delay_structure_dict = {}
    delay_list = [0.1,0.2, 0.3, 0.4, 0.5,0.6, 0.7,0.8,0.9]
    structures = {}
    for delay_percentage in delay_list: #delays:
        res = process_directories(path, delay_percentage)
        #continue
        if res is None:
            continue
        out_dict_wire_avf = res #, out_dict_particle_avf, out_dict_single_flop_avf, out_dict_multi_flop_avf = res 
        print("Res for", out_dict_wire_avf)
        #continue
        avf_delay_benchmark_dict[delay_percentage] = {}
        unscaled_avf_delay_benchmark_dict[delay_percentage] = {}
        if len(out_dict_wire_avf)  == 0:
            continue
        avf_dict = {}
        avf_dict["delay"] = out_dict_wire_avf

        structures = set(structures)
        for _, structs in avf_dict["delay"].items():
            structures.update(structs)
        structures = list(structures) #list(avf_dict["delay"][list(avf_dict["delay"].keys())[0]].keys())
        method = "delay"
        max_value = max(list(itertools.chain.from_iterable([list(avf_dict[method][benchmark].values()) for benchmark in avf_dict[method].keys()])))
        for idx, benchmark in enumerate(avf_dict[method].keys()):
            avf_values = []
            unscaled_avf_values = []
            current_data_dict = avf_dict[method][benchmark]
            #if benchmark == "libstrstr":
            #    print("Current data dict", current_data_dict)
            #    print("Structures", structures)
            for structure in structures: #avf_dict[method][benchmark].keys(): # Needs to be determinsitic ordering!
                if structure not in unscaled_delay_structure_dict:
                    unscaled_delay_structure_dict[structure] = {}
                if delay_percentage not in unscaled_delay_structure_dict[structure]:
                    unscaled_delay_structure_dict[structure][delay_percentage] = [] 
                if structure in current_data_dict and max_value>0:
                    avf_values.append(current_data_dict[structure]/max_value)
                    unscaled_avf_values.append(current_data_dict[structure])
                    #print("Adding Benchmark", benchmark, "structure", structure, "delay", delay_percentage, "current data dict", current_data_dict[structure])
                    unscaled_delay_structure_dict[structure][delay_percentage].append(current_data_dict[structure])
                else:
                    avf_values.append(0)
                    unscaled_avf_values.append(0)
                
                    
            #print(current_data_dict)
            #print(avf_values)
            #print("Bencdhmark", benchmark)
            #plot_avf(avf_dict[method][benchmark].keys(), avf_values, benchmark, curr_ax, idx, nolabel)
            avf_delay_benchmark_dict[delay_percentage][benchmark] = list(zip(structures, avf_values))
            unscaled_avf_delay_benchmark_dict[delay_percentage][benchmark] = list(zip(structures, unscaled_avf_values))
            #plot_avf(structures, avf_values, benchmark, curr_ax, idx, nolabel, True)
        #print(avf_dict["delay"])
        #print("Avf delay benchmark", avf_delay_benchmark_dict)
        #fig.legend(loc='upper center', bbox_to_anchor=(0.5, 1.02), ncol=6, fancybox=True)
        #plot_avf(structures, delay_fault_avf,"histogram_delay_fault.png", "wAVF", ax1)
        #plot_avf(structures, particle_strike_avf,"histogram_particle_strike.png", "sAVF", ax2)

        #delay = delay_percentage
        #plt.tight_layout()
        #plt.subplots_adjust(top=0.775, bottom=0.22)
        #plt.savefig(f"beeps_plots/histogram_delay_fault_{delay}.pdf",)
        #df = pd.DataFrame.from_dict(avf_dict["delay"], orient='index')
        #df.to_csv(f'beeps_plots/output_{delay}.csv')
        #df = pd.DataFrame.from_dict(out_dict_single_flop_avf, orient='index')
        #df.to_csv(f'beeps_plots/single_flop_{delay}.csv')
        #df = pd.DataFrame.from_dict(out_dict_multi_flop_avf, orient='index')
        #df.to_csv(f'beeps_plots/multi_flop_avf_{delay}.csv')
            #plt.savefig(outfile, format='pgf')
            #tikzplotlib.save("histogram_plot.tex")
            #matplotlib2tikz.save("mytikz.tex")
            # Show plot
    
    # Plot delay sweep next...
    #delay_list = [0.25, 0.5, 0.75, 1.0]
    #delay_list = [0.5, 0.7,0.9]
    flattened_lists = {}
    geomean_structure_delay_dict = {}
    max_geomean = 0
    #for scaled in ["noscaling", "scaled_perdelay", "normalizedperstructure"]:
    print("unscaled_avf_delay_benchmark_dict",unscaled_avf_delay_benchmark_dict)
    scaled = "normalizedperstructure"
    for structure in structures:
        structure_max = 0
        #if scaled == "noscaling": geomean_structure_delay_dict[structure] = {}
        fig, ax = plt.subplots(1,1,figsize=(4,2.2))
        for idx, delay in enumerate(unscaled_avf_delay_benchmark_dict.keys()):
            if scaled == "scaled_perdelay": filtered_list = [[item[1] for item in entry if item[0] == structure] for entry in list(avf_delay_benchmark_dict[delay].values())]
            else: filtered_list = [[item[1] for item in entry if item[0] == structure] for entry in list(unscaled_avf_delay_benchmark_dict[delay].values())]
            print("filtered litst", filtered_list)
            flattened_list = list(itertools.chain.from_iterable(filtered_list))

            #if scaled == "noscaling":
                #print("NOSCALING")
            #    geomean_structure_delay_dict[structure][delay] = gmean(flattened_list)
            #    if max_geomean < geomean_structure_delay_dict[structure][delay]:
            #        max_geomean = geomean_structure_delay_dict[structure][delay]

            if max(flattened_list) > structure_max:
                structure_max = max(flattened_list)

            flattened_lists[idx] = flattened_list

        for idx, delay in enumerate(unscaled_avf_delay_benchmark_dict.keys()):
            if scaled == "normalizedperstructure": flattened_lists[idx] = list(np.array(flattened_lists[idx]) / structure_max) 
            print("Flattened list", flattened_list)
            plot_avf(list(unscaled_avf_delay_benchmark_dict[delay].keys()), flattened_lists[idx], int(delay_list[idx]*100), ax, idx, False, False,bar_placement=1, decimal_places=4)

        handles, labels = plt.gca().get_legend_handles_labels()
        order = [0,7,1,8]+list(range(2,7)) #[0,2,1]+list(range(3,9))
        #fig.legend([handles[idx] for idx in order],[labels[idx] for idx in order], loc='upper center', bbox_to_anchor=(0.5, 1.01), ncol=9, fancybox=True, title="Delay Duration (% of Clock Cycle)",  prop={'size': 6.5})
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.01), ncol=9, fancybox=True, title="Delay Duration (% of Clock Cycle)",  prop={'size': 5.25})

        #fig.legend()
        #plt.subplots_adjust(top=0.6, bottom=0.15, right=0.99)
        plt.subplots_adjust(top=0.77, bottom=0.085, right=0.99, wspace=0.65, hspace=0)#0.45)
        #ax.set_ylabel("Normalized DelayAVF Values")
        fig.text(0.04, 0.4, 'Normalized DelayAVF Values', ha='center', va='center', rotation='vertical')
        ax.set_ylim([0,1.1])
        #ax.set_title(structure)
        plt.tight_layout()
        plt.rcParams.update({'font.size': 7})
        plt.savefig("beeps_plots/delay"+structure+"_"+scaled+".pdf")
        plt.close()



    #plt.show()
        
if __name__ == "__main__":
    os.makedirs("beeps_plots", exist_ok=True)
    micro_plot(path="configs/beeps")

