use crate::circuit_graph::CellType;
use crate::circuit_graph::CircuitGraph;
use crate::params;
use crate::recursive_simulator::Simulator;
use crate::recursive_simulator::RecursiveValMapType;
use crate::utils;
use indicatif::{ParallelProgressIterator, ProgressStyle};
use petgraph::graph::NodeIndex;

use serde::Serialize;
use std::collections::HashMap;
use std::collections::HashSet;

use std::sync::Arc;
use rayon::iter::{ParallelIterator, IntoParallelRefIterator};
use std::fs::File;
use std::io::{BufWriter, Write};
use itertools::Itertools;





pub struct DelayFaultInjector {
    pub circuit: Arc<CircuitGraph>,
    flop_values_map: HashMap<i64, HashMap<String, i64>>,
    clk_period: i64,
    _all_cycles_sorted: Vec<i64>,
    inject_into_cycles: Vec<i64>,
    //inject_into_edges: Vec<(String, String)>,
    simulator_per_cycle: Option<HashMap<i64, Simulator>>,
}

#[derive(Debug, Serialize,Default)]
pub struct SimulationResult {
    edge: (String, String),
    delay: i64,
    fan_out: Vec<String>,
    static_reachable: Vec<String>,
    dynamically_reachable_per_cycle: HashMap<i64, Vec<String>>,
}

#[derive(Debug, Serialize,Default)]
pub struct AccumulatedResults {
    num_cycles: i64,
    all_delays: Vec<i64>,
    all_flops: Vec<String>,
    analysis_results: HashMap<i64, Vec<SimulationResult>>,
    clk_period: i64,
}




impl DelayFaultInjector {
    pub fn new(graph_path: String, flop_values_path: String) -> Self {

       let mut circuit = CircuitGraph::new_from_json_path(graph_path);
       DelayFaultInjector::new_from_circuit(circuit, flop_values_path)
        //serde_json::Deserializer::from_str(&data).into_iter::<SerializedFlop>(){
    }

    pub fn new_from_circuit(mut circuit: CircuitGraph, flop_values_path: String) -> Self{
        //let longest_path_length = circuit.longest_discrete_path.unwrap();
        println!("Parsing trace!");
        let clk_period = circuit.clk_period; //circuit.get_cycle_time(longest_path_length as f64);
        let  (flop_values_map, mut  inject_into_cycles) = utils::parse_trace(flop_values_path);
        inject_into_cycles.sort();
        let mut all_cycles_sorted = flop_values_map
            .keys()
            .map(|k| k.clone())
            .collect::<Vec<i64>>();
        all_cycles_sorted.sort();
        //circuit.dump_paths();
        let clk_period = circuit.clk_period.clone();
        println!("Precomputing edge to reachable flop mapping");
        circuit.precompute_edge_to_reachable_flop_mapping(circuit.inject_into_edges.clone());
        Self {
            circuit: Arc::new(circuit),
            flop_values_map: flop_values_map,
            clk_period: clk_period,
            _all_cycles_sorted: all_cycles_sorted,
            inject_into_cycles: inject_into_cycles,
            //inject_into_edges: circuit.inject_into_edges,
            simulator_per_cycle: None,
        }

    }

    pub fn verify_correctness(&self){
        for cycle in self.inject_into_cycles.iter() { //We get the cycles from python, so do not expect to be enumerated like 0,1,2!
            //let cycle = self.all_cycles_sorted[idx];
            let current_values = &self.flop_values_map[&cycle];
            let sim = &self.simulator_per_cycle.as_ref().unwrap()[&cycle];
            let sim_res = sim.run(None, None, None);
            let mut failing_flops_this_cycle: Vec<String> = Vec::new();
            for (key, value) in sim_res.iter() {
                //if key=="dff__1715__in"{
                //    println!("Verilator vlaue at {:?} is {:?} sim res {:?}", cycle, current_values[key], value);
                //    println!("prior dict value is {:?}", sim.values_prior_cycle[&self.circuit.node_to_graph_index[key]]);
                //} 
                if current_values[key] != *value {
                    failing_flops_this_cycle.push(utils::process_flop_name(&key[..]));
                    panic!("Flop {:?} failed has value {:?} should have {:?} in cycle {:?}", key, value, current_values[key], cycle);
                }
            }
            //println!("Dynamically reachable per cycle {:?} is {:?}", self.all_cycles_sorted[idx], &failing_flops_this_cycle);
            //if (failing_flops_this_cycle.len())>0{
            //    dynamically_reachable_per_cycle
            //        .insert(*cycle, failing_flops_this_cycle);
            //}
            
        }
    }
    
    pub fn debug_edge(&self, cycle: i64, delay1: i64, delay2: i64, edge: &(NodeIndex, NodeIndex), flop: NodeIndex) {
        let static_reachable_flops1: HashSet<NodeIndex> =   self.circuit
                .trace_delay_defect(edge, delay1, self.clk_period);
        let static_reachable_flops2: HashSet<NodeIndex> =   self.circuit
            .trace_delay_defect(edge, delay2, self.clk_period);
        let sim = &self.simulator_per_cycle.as_ref().unwrap()[&cycle];
        //let sim_res1 = sim.run(Some(&static_reachable_flops1), Some(delay1), Some(edge));
        //let sim_res2 = sim.run(Some(&static_reachable_flops2), Some(delay2), Some(edge));
        let x = self.circuit.graph_index_to_node[&flop].clone();
        let mut recursive_val_map1: RecursiveValMapType = Vec::new();// = vec![HashMap::<i64, FlopValueType>::new(); self.circuit.graph_index_to_node.len()]; // Works because hashmap implements clone as a deep copy? //Vec::with_capacity(self.circuit.graph_index_to_node.len());//vec![HashMap::new(); self.]//HashMap<FlopMapIndexType, HashMap<i64, FlopValueType>> = HashMap::new();
        sim.reset(&mut recursive_val_map1);
        sim.get_recursive_val(self.clk_period, flop, Some(delay1), Some(edge), &mut recursive_val_map1);
        let mut recursive_val_map2: RecursiveValMapType = Vec::new();// = vec![HashMap::<i64, FlopValueType>::new(); self.circuit.graph_index_to_node.len()]; // Works because hashmap implements clone as a deep copy? //Vec::with_capacity(self.circuit.graph_index_to_node.len());//vec![HashMap::new(); self.]//HashMap<FlopMapIndexType, HashMap<i64, FlopValueType>> = HashMap::new();
        sim.reset(&mut recursive_val_map2);
        sim.get_recursive_val(self.clk_period, flop, Some(delay2), Some(edge), &mut recursive_val_map2);
        let mut recursive_val_map3: RecursiveValMapType = Vec::new();// = vec![HashMap::<i64, FlopValueType>::new(); self.circuit.graph_index_to_node.len()]; // Works because hashmap implements clone as a deep copy? //Vec::with_capacity(self.circuit.graph_index_to_node.len());//vec![HashMap::new(); self.]//HashMap<FlopMapIndexType, HashMap<i64, FlopValueType>> = HashMap::new();
        sim.reset(&mut recursive_val_map3);
        sim.get_recursive_val(432, edge.0, None, None, &mut recursive_val_map3);
        println!("####### START {:?} ######", recursive_val_map3[edge.0.index()][&432]);
        sim.compare_recursive_val(flop, self.clk_period,delay1,delay2,edge, &mut recursive_val_map1, &mut recursive_val_map2);
        //sim.print_predecessor(flop, self.max_steps, Some(delay1), Some(edge), &mut recursive_val_map1);
        println!("####### TRACE1 END #####");
       // sim.print_predecessor(flop, self.max_steps, Some(delay2), Some(edge), &mut recursive_val_map2);
        println!("####### TRACE2 END #####");



        //sim.print_predecessor(flop, self.max_steps, Some(delay1), Some(edge), &mut recursive_val_map);
        //sim.print_predecessor(flop, self.max_steps, Some(delay2), Some(edge), &mut recursive_val_map);
        //println!("Value 1 {:?}", sim_res1[&x]);
        //println!("Value 2 {:?}", sim_res2[&x]);


    }

    pub fn run_simulation_for_edge(
        &self,
        edge: &(NodeIndex, NodeIndex),
        delay: i64,
    ) -> SimulationResult {
        let edge_as_string_tuple = (
            self.circuit.graph_index_to_node[&edge.0].to_string(),
            self.circuit.graph_index_to_node[&edge.1].to_string(),
        );
        let static_reachable_flops: HashSet<NodeIndex
        > =
            self.circuit
                .trace_delay_defect(edge, delay, self.clk_period);
        let mut dynamically_reachable_per_cycle: HashMap<i64, Vec<String>> = HashMap::new();
        let fan_out = self.circuit.get_fan_out_of_edge(edge).into_iter().map(|x| utils::process_flop_name(&self.circuit.graph_index_to_node[&x].to_string())).collect::<Vec<String>>();
        if static_reachable_flops.len() == 0 {
            return SimulationResult {
                static_reachable: Vec::new(),
                fan_out: fan_out,
                edge: edge_as_string_tuple,
                delay: delay,
                dynamically_reachable_per_cycle: dynamically_reachable_per_cycle,
            };
        }
        //println!("Now starting simulation");
        for cycle in self.inject_into_cycles.iter(){ //}.progress() { //We get the cycles from python, so do not expect to be enumerated like 0,1,2!
            //let cycle = self.all_cycles_sorted[idx];
            let current_values = &self.flop_values_map[&cycle];
            let sim = &self.simulator_per_cycle.as_ref().unwrap()[&cycle];
            let sim_res = sim.run(Some(&static_reachable_flops), Some(delay), Some(edge));
            let mut failing_flops_this_cycle: Vec<String> = Vec::new();
            for (key, value) in sim_res.iter() {
                //if key=="dff__1715__in"{
                //    println!("Verilator vlaue at {:?} is {:?} sim res {:?}", cycle, current_values[key], value);
                //    println!("prior dict value is {:?}", sim.values_prior_cycle[&self.circuit.node_to_graph_index[key]]);
                //} 
                if current_values[key] != *value {
                    failing_flops_this_cycle.push(utils::process_flop_name(&key[..]));
                }
            }
            //println!("Dynamically reachable per cycle {:?} is {:?}", self.all_cycles_sorted[idx], &failing_flops_this_cycle);
            if (failing_flops_this_cycle.len())>0{
            //    println!("Dynamically reachable per cycle {:?} {:?} for edge {:?}", cycle, failing_flops_this_cycle, edge );
            //    sim.edge_is_toggling(edge);
                dynamically_reachable_per_cycle
                    .insert(*cycle, failing_flops_this_cycle);
            }
            
        }
        
        
        return SimulationResult {
            edge: edge_as_string_tuple,
            delay: delay,
            fan_out: fan_out,
            static_reachable: static_reachable_flops.into_iter().map(|x| utils::process_flop_name(&self.circuit.graph_index_to_node[&x].to_string())).collect::<Vec<String>>(),
            dynamically_reachable_per_cycle: dynamically_reachable_per_cycle,
        };
    }



    pub fn prepare_simulators(&mut self) {
        self.simulator_per_cycle = Some(HashMap::new());
        let mut ret_map: HashMap<String, i64> = HashMap::new();
        for cycle in self.inject_into_cycles.iter() {
            //let cycle = self.all_cycles_sorted[idx];
            let prior_values = match cycle {
                0 => {
                    let keys = self.flop_values_map[&cycle].keys();
                    for k in keys {
                        ret_map.insert(k.to_string(), params::FLOP_DEFAULT_VALUE);
                    }
                    &ret_map
                }
                _ => &self.flop_values_map[&(cycle-1)], //We need to get the prior cycle (so cycle-1), not the prior cycle in the list (so NOT flop_values_map[self.cycles[cycle-1]]!!!)
            };
            let current_values = &self.flop_values_map[&cycle];

            let sim = Simulator::new(
                self.circuit.clone(),
                prior_values,
                current_values,
                self.clk_period.try_into().unwrap(),
            );
            self.simulator_per_cycle
                .as_mut()
                .unwrap()
                .insert(*cycle, sim);
        }
    }

    pub fn run_campaign(&mut self, delays: Vec<f64>, outfile_path: &str) {
        println!("Running the simulation");
        //println!("Running the simulation on edges {:?} ", self.circuit.edges);
        self.prepare_simulators();
        println!("Checking correctness first");
        //self.verify_correctness();
        println!("Done checking correctness first");
        println!("Delays {:?} clk period {:?}", delays, self.clk_period);
        let mut delays = delays.iter().map(|x| (x*self.clk_period as f64) as i64).unique().collect::<Vec<i64>>();
        delays.sort();
        //for edge in 
        println!("Delays {:?} clk period {:?}", delays, self.clk_period);
        
        let mut accumulated_result: HashMap<i64, Vec<SimulationResult>> = HashMap::new();
        //let inject_into_edges = match inject_into_edges_arg {
        //    Some(inner) => Box::new(inner.iter().map(|x| (self.circuit.node_to_graph_index[&x.0], self.circuit.node_to_graph_index[&x.1])).collect()), 
        //    None => Box::new(self.circuit.edges.clone())
        //};
        //let inject_into_edges: Vec<_> = self.inject_into_edges.iter().map(|x| (self.circuit.node_to_graph_index[&x.0], self.circuit.node_to_graph_index[&x.1])).collect();
        let inject_into_edges: Vec<_> = self.circuit.inject_into_edges.clone();//.iter().map(|x| (self.circuit.node_to_graph_index[&x.0], self.circuit.node_to_graph_index[&x.1])).collect();
        
        //let inject_into_edges: Vec<_> =self.circuit.edges.clone();
        for delay in delays.iter() {
            let style = ProgressStyle::default_bar();
            let sim_results: Vec<SimulationResult> = inject_into_edges.par_iter().progress_with_style(style).map(|edge| {
                //println!("running edge {:?}", edge);
                //if self.circuit.graph_index_to_node[&edge.0].to_string() == "\\i_ibus_rdt[13]" && self.circuit.graph_index_to_node[&edge.1].to_string() == "decode__167__ZN" {
                self.run_simulation_for_edge(edge, *delay)
                //} else {
                //    SimulationResult {..Default::default()}
                //}
                
            }).collect();
            accumulated_result.insert(*delay, sim_results);
        }
        let final_result: AccumulatedResults = AccumulatedResults {num_cycles: self.inject_into_cycles.len() as i64, all_delays: delays, analysis_results: accumulated_result, all_flops: self.circuit.node_to_graph_index.keys().map(|x| utils::process_flop_name(&x[..].to_string())).collect::<Vec<String>>(), clk_period: self.clk_period };
        println!("Now writing to {:?}", outfile_path);
        let file = File::create(outfile_path).unwrap();
        let mut writer = BufWriter::new(file);
        serde_json::to_writer(&mut writer, &final_result).unwrap();
        writer.flush().unwrap();
        //println!("Simulation results {:#?} \n", sim_results);
    }
}
