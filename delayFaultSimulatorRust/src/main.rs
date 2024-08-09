use std::path::Path;
mod circuit_graph;
mod delay_fault_injector;
mod params;
mod recursive_simulator;
mod utils;
//mod flow;

use circuit_graph::CircuitGraph;
use clap::{App, Arg};
use delay_fault_injector::DelayFaultInjector;


fn parse_args() -> (String, bool, Option<String>) {
    let matches = App::new("Delay Fault Injector")
        .version("1.0")
        .author("Vincent Ulitzsch/Peter Deutsch")
        .about("Injects delay faults into the system")
        .arg(
            Arg::with_name("config_file")
                .help("Sets the config file to use")
                .required(true)
                .index(1),
        )
        .arg(
            Arg::with_name("dump_only")
                .long("dump_only")
                .short('d')
                .takes_value(false)
                .help("Dump the configuration file"),
        )
        .arg(Arg::with_name("debug_config")
            .long("debug_config")
            .takes_value(true)
            .required(false)
            .help("A json config to debug a specific flop trace"))
        .get_matches();

    let config_file = matches.value_of("config_file").unwrap().to_string();
    let debug_config: Option<String> = match matches.value_of("debug_config") {
        Some(path) => {
            Some(path.to_string())
        },
        None => {
            None
        }
    };
    let dump_only = matches.is_present("dump_only");
    (config_file, dump_only, debug_config)
}

fn main() {
    let (config_file_path, dump_only, do_debug_path) = parse_args();
    //let args: Vec<String> = env::args().collect();
   
    let config_path: String = config_file_path; //&args[1];
    let config = utils::read_json_file(&config_path);
    let output_dir = config["output_dir"].as_str().unwrap();
    let graph_path: String =  Path::new(output_dir).join("circuit_out.json").into_os_string().into_string().unwrap();  //config["circuit_out_fp"].as_str().unwrap().to_string(); //&args[1];
    let full_graph_path: String =  Path::new(output_dir).join("circuit_out_full.json").into_os_string().into_string().unwrap();  //config["circuit_out_fp"].as_str().unwrap().to_string(); //&args[1];

    

    let delays_range: Vec<f64> = match config.get("delay_range_steps") {
        Some(_steps) => {
            let delay_min: f64 = config["delay_min"].as_f64().unwrap();
            let delay_max: f64 = config["delay_max"].as_f64().unwrap();
            let steps: i64 = config["delay_range_steps"].as_i64().unwrap();
            itertools_num::linspace(delay_min, delay_max, steps as usize).into_iter().collect::<Vec<f64>>()
        },
        None => {
            let range = config["delay_range"].as_array().unwrap().into_iter().map(|x| x.as_f64().unwrap()).collect::<Vec<f64>>();
            range
        }
    };
    let config_clk_period: Option<i64> = match config.get("clk_period") {
        Some(v) => {v.as_i64()},
        None => { None }
    };
    //let inject_into_edges: Vec<Vec<&str>> = config["injectIntoEdges"].try_into().unwrap();
    //println!("Inject into edges {:?}", inject_into_edges);
    //println!("Delays range {:?} {:?}", &delays_range, &config["out"].as_str().unwrap());

    //return;
    //let output_dir = &config["output_dir"];
    //let default_path = ;
    let output_path: String = match config.get("timing_analysis_results") {
        Some(path) => path.to_string(),
        None =>  { Path::new(output_dir).join("timing_metadata.json").into_os_string().into_string().unwrap()}
    };
    let full_circuit_graph = CircuitGraph::new_from_json_path(full_graph_path);
    println!("Clk period, determined through full structure {:?}", full_circuit_graph.clk_period);
    //let clk_period = full_circuit_graph.clk_period;
    let mut circuit_graph = CircuitGraph::new_from_json_path(graph_path);
    circuit_graph.clk_period = full_circuit_graph.clk_period;
    circuit_graph.dump_timing_data(&output_path);
    if let Some(clk_period) = config_clk_period {
        circuit_graph.clk_period = clk_period;
    }
    if !(dump_only) {
        let flop_values_path: String = Path::new(output_dir).join("dump_vcdtrace.json").into_os_string().into_string().unwrap();  //config["json_vcdtrace_fp"].as_str().unwrap().to_string(); //&args[2];
        let mut delay_fault_injector = DelayFaultInjector::new_from_circuit(circuit_graph, flop_values_path);
        
        //println!("Hello, world!");
        //let mut delay_fault_injector = delay_fault_injector::DelayFaultInjector::new(
        //   graph_path.to_string(),
        //    flop_values_path.to_string(),
        //);
        let output_path: String = match config.get("delay_injection_results") {
            Some(path) => path.to_string(),
            None =>  { Path::new(output_dir).join("delay_injection_res.json").into_os_string().into_string().unwrap()}
        };
        if let Some(debug_path) = do_debug_path {
            let debug_config = utils::read_json_file(&debug_path);
            let edge = debug_config["edge"].as_array().unwrap();
            let edge = (delay_fault_injector.circuit.node_to_graph_index[edge[0].as_str().unwrap()].clone(), delay_fault_injector.circuit.node_to_graph_index[edge[1].as_str().unwrap()].clone());
            println!("Edge {:?}", edge);
            let flop_str = "dff_".to_owned()+debug_config["flop"].as_str().unwrap()+"_in";
            //println!("Flop values {:?}", delay_fault_injector.circuit.node_to_graph_index.keys());
            let flop_index =delay_fault_injector.circuit.node_to_graph_index[&flop_str].clone();
            let cycle = debug_config["cycle"].as_i64().unwrap();
            let delay1 = debug_config["delays"].as_array().unwrap()[0].as_i64().unwrap();
            let delay2 = debug_config["delays"].as_array().unwrap()[1].as_i64().unwrap();
            //delay_fault_injector.debug();
            delay_fault_injector.prepare_simulators();
            delay_fault_injector.debug_edge(cycle, delay1, delay2, &edge, flop_index);
            return;
        }
        delay_fault_injector.run_campaign(delays_range, &output_path);
    }
}
