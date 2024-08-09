use petgraph::Incoming;
use std::any::TypeId;
use std::collections::{HashMap, HashSet};
use std::ops::{Add, AddAssign};
use std::sync::{Arc, Mutex};
use std::fs;
use std::fs::File;
use std::io::{BufWriter, Write};
use itertools::Itertools;
use rayon::iter::{ParallelIterator, IntoParallelRefIterator};
use rayon::collections::{hash_set};
use indicatif::{ParallelProgressIterator, ProgressStyle};

use serde::Serialize;
use crate::params;
use indicatif::ProgressIterator;
use petgraph::algo::all_simple_paths;
use petgraph::algo::toposort;
use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::visit::EdgeRef;
use std::io;
use serde::Deserialize;
use crate::utils;

#[derive(Debug, Serialize,Default)]
pub struct TimingAnalysis {
    path_distribution: Vec<(String, String, i64)>,
    clk_period: i64,
    longest_discrete_path: i64
}


#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum CellType {
    Buf,
    Not,
    And,
    Nor,
    Nand,
    Or,
    Xnor,
    Xor,
    InFlop,
    OutFlop,
    ConstantZero,
    ConstantOne,
    ConstantX,
}

fn xor_bool_vector(vec: &[bool]) -> bool {
    let mut result = false;
    for &element in vec {
        result ^= element;
    }
    result
}

impl CircuitElement {

    pub fn can_short_circuit(&self, inputs: &[bool]) -> Option<bool> {
        match self.cell_type {
            CellType::Buf => {
                debug_assert!(inputs.len() == 1,"Unexpected number of inputs for logic function!");
                Some(inputs[0])
            }
            CellType::Not => {
                debug_assert!(inputs.len() == 1,"Unexpected number of inputs for logic function!");
                Some(!inputs[0])
                //if inputs.len() == 1 {
                //    Some(!inputs[0])
                //} else {
                    // Handle error: NOT cell requires exactly one input
                //    panic!("Unexpected number of inputs for logic function!");
                //}
            }
            CellType::And => {if inputs.iter().any(|&x| !x) { return Some(false);} else{ return None;} },
            CellType::Nor => {if inputs.iter().any(|&x| x) { return Some(false);} else{ return None;} },
            CellType::Nand => {if inputs.iter().any(|&x| !x) { return Some(true);} else{ return None;} },
            CellType::Or => {if inputs.iter().any(|&x| x) { return Some(true);} else{ return None;} }
            CellType::Xnor => {
                return None;
                //if inputs.len() == 2 {
                //    inputs[0] == inputs[1]
                //} else {
                //     // Handle error: XNOR cell requires exactly two inputs
                //    panic!("Unexpected number of inputs for logic function for Xnor!");
                //}
            }
            CellType::Xor => {
                return None;
                //if inputs.len() == 2 {
                //    inputs[0] != inputs[1]
                //} else {
                //    // Handle error: XOR cell requires exactly two inputs
                //    panic!("Unexpected number of inputs for logic function for Xor!");
                // }
            }
            CellType::InFlop => {
                panic!("Should not call logic evaluation on InFlop?");
            }
            CellType::OutFlop => {
                debug_assert!(inputs.len() == 1,"Unexpected number of inputs for output flop");
                Some(inputs[0])
            }
            CellType::ConstantZero => {
                //if inputs.len() > 0 {
                //    panic!("Should not call logic evaluation with inputs on contant zero?");
                //}
                return Some(0 != 0);
                //panic!("Should not call logic evaluation on contant zero?");
            }
            CellType::ConstantOne => {
                //if inputs.len() > 0 {
                //    panic!("Should not call logic evaluation with inputs on contant one?");
                //}
                return Some(1 != 0);
                //panic!("Should not call logic evaluation on contant one?");
            }
            CellType::ConstantX => {
                panic!("Cell type constant x should never be called for logic evaluation element {:?} !", &self);
            }
        }
    }
    pub fn evaluate_logic(&self, inputs: &[bool]) -> bool {
        match self.cell_type {
            CellType::Buf => {
                if inputs.len() == 1 {
                    inputs[0]
                } else {
                    // Handle error: BUF cell requires exactly one input
                    panic!("Unexpected number of inputs for logic function!");
                }
            }
            CellType::Not => {
                if inputs.len() == 1 {
                    !inputs[0]
                } else {
                    // Handle error: NOT cell requires exactly one input
                    panic!("Unexpected number of inputs for logic function!");
                }
            }
            CellType::And => inputs.iter().all(|&x| x),
            CellType::Nor => !(inputs.iter().any(|&x| x)),
            CellType::Nand => !(inputs.iter().all(|&x| x)),
            CellType::Or => inputs.iter().any(|&x| x),
            CellType::Xnor => {
                !xor_bool_vector(inputs)
                //if inputs.len() == 2 {
                //    inputs[0] == inputs[1]
                //} else {
                //     // Handle error: XNOR cell requires exactly two inputs
                //    panic!("Unexpected number of inputs for logic function for Xnor!");
                //}
            }
            CellType::Xor => {
                xor_bool_vector(inputs)
                //if inputs.len() == 2 {
                //    inputs[0] != inputs[1]
                //} else {
                //    // Handle error: XOR cell requires exactly two inputs
                //    panic!("Unexpected number of inputs for logic function for Xor!");
                // }
            }
            CellType::InFlop => {
                panic!("Should not call logic evaluation on InFlop?");
            }
            CellType::OutFlop => {
                if inputs.len() == 1 {
                    inputs[0]
                } else {
                    // Handle error: BUF cell requires exactly one input
                    panic!(
                        "Unexpected number of inputs for logic function for flop, inputs {:?}",
                        inputs
                    );
                }
                //panic!("Should not call logic evaluation on flop?");
            }
            CellType::ConstantZero => {
                return 0 != 0;
                //panic!("Should not call logic evaluation on contant zero?");
            }
            CellType::ConstantOne => {
                return 1 != 0;
                //panic!("Should not call logic evaluation on contant one?");
            }
            CellType::ConstantX => {
                panic!("Cell type constant x should never be called for logic evaluation element {:?} !", &self);
            }
        }
    }
}

impl CellType {
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "buf" => Some(CellType::Buf),
            "not" => Some(CellType::Not),
            "and" => Some(CellType::And),
            "nor" => Some(CellType::Nor),
            "nand" => Some(CellType::Nand),
            "or" => Some(CellType::Or),
            "xnor" => Some(CellType::Xnor),
            "xor" => Some(CellType::Xor),
            "0" => Some(CellType::ConstantZero),
            "1" => Some(CellType::ConstantOne),
            "x" => Some(CellType::ConstantX),
            _ => panic!("Could not parse cell type {:?}?", s),
        }
    }
}

#[derive(Debug)]
pub struct CircuitElement {
    _name: String,
    pub cell_type: CellType,
}

#[derive(Debug, Clone, Default)]
pub struct CircuitWire {
    pub float_weight: f64,
    pub discrete_weight: i64,
}

#[derive(Debug, Default)]
pub struct CircuitGraph {
    pub circuit: DiGraph<CircuitElement, CircuitWire>,
    pub node_to_graph_index: HashMap<String, NodeIndex>,
    pub graph_index_to_node: HashMap<NodeIndex, String>,
    pub input_nodes: HashSet<NodeIndex>,
    pub output_nodes: Vec<NodeIndex>,
    paths_dict: HashMap<(NodeIndex, NodeIndex), Arc<Vec<Arc<Vec<NodeIndex>>>>>,
    _edge_to_paths: HashMap<(NodeIndex, NodeIndex), Vec<Arc<Vec<NodeIndex>>>>,
    //paths_to_id_bymap: BiMap<(u64, Vec<NodeIndex>)>,
    _path_to_cached_length: HashMap<Arc<Vec<NodeIndex>>, i64>,
    //path_counter: u64,
    pub edges: Vec<(NodeIndex, NodeIndex)>,
    pub longest_path_per_node: HashMap<NodeIndex, i64>,
    pub edge_to_reachable_flops: HashMap<(NodeIndex, NodeIndex), Arc<HashMap<NodeIndex, i64>>>,
    pub longest_discrete_path: Option<i64>,
    pub nodes_to_pred: HashMap<NodeIndex, HashSet<NodeIndex>>,
    pub clk_period: i64,
    pub inject_into_edges: Vec<(NodeIndex, NodeIndex)>
}

#[derive(Debug, Deserialize)]
struct SerializedGate {
    name: String,
    cell_type: String,
}

#[derive(Debug, Deserialize)]
struct SerializedFlop {
    name: String,
    direction: Option<String>,
    pins: Option<HashMap<String, String>>,
}

#[derive(Debug, Deserialize)]
struct SerializedWire {
    from: String,
    to: String,
    weight: f64,
}

#[derive(Debug, Deserialize)]
struct SerializedGraph {
    gates: Vec<SerializedGate>,
    flops: Vec<SerializedFlop>,
    edges: Vec<SerializedWire>,
    inject_into_edges: Vec<(String, String)>
}

impl CircuitGraph {
    pub fn new_with_capacity(num_nodes: usize, num_edges: usize) -> Self {
        let circuit: DiGraph<CircuitElement, CircuitWire> =
            DiGraph::with_capacity(num_nodes, num_edges);
        Self {
            circuit: circuit,
            node_to_graph_index: HashMap::new(),
            input_nodes: HashSet::new(),
            output_nodes: Vec::new(),
            ..Default::default()
        }
    }

    pub fn new_from_json_path(graph_path: String) -> Self{
        let file = fs::File::open(graph_path).expect("file should open read only");
        let out: SerializedGraph = serde_json::from_reader(file).unwrap();
        let mut circuit =
        CircuitGraph::new_with_capacity(out.gates.len() + out.flops.len(), out.edges.len());

        //Iterating through all
        for gate in out.gates {
            circuit.add_node(gate.name, CellType::from_str(&gate.cell_type).unwrap());
            //let node: CircuitElement = CircuitElement { name: gate.name, cell_type: CellType::from_str(&gate.cell_type).unwrap()};
        }
        for flop in out.flops {

            //println!("Flop {:?}", &flop);
            match flop.pins {
                //let in_node = CircuitElement { name: pin["IN"].to_string(), cell_type: CellType::Flop};
                Some(pin) => {
                    //let out_node_q = CircuitElement { name: pin["Q"].to_string(), cell_type: CellType::Flop};
                    //let out_node_qn = CircuitElement { name: pin["QN"].to_string(), cell_type: CellType::Flop};
                    //node_to_graph_index.insert(in_node.name.to_string(),  circuit.add_node(in_node));
                    //node_to_graph_index.insert(out_node_q.name.to_string(),  circuit.add_node(out_node_q));
                    //node_to_graph_index.insert(out_node_qn.name.to_string(), circuit.add_node(out_node_qn));
                    circuit.add_node(pin["IN"].to_string(), CellType::OutFlop);
                    circuit.add_node(pin["Q"].to_string(), CellType::InFlop);
                    if pin.contains_key("QN") {
                        circuit.add_node(pin["QN"].to_string(), CellType::InFlop);
                    }
                }
                None => {
                    //println!("Flop object {:?}", flop);
                    if flop.direction.as_ref().unwrap() == "IN" {
                        circuit.add_node(flop.name.to_string(), CellType::InFlop);
                    //[TODO 15/09/2023 VU] I am not sure this is correct. In fact, it is probably not.
                    } else if flop.direction.unwrap() == "OUT" {
                        circuit.add_node(flop.name.to_string(), CellType::OutFlop);
                        //[TODO 15/09/2023 VU] I am not sure this is correct. In fact, it is probably not.
                    }

                    //let index = circuit.add_node(CircuitElement{name: flop.name.to_string(), cell_type: CellType::Flop } );
                    //node_to_graph_index.insert(flop.name, index);
                }
            }
        }
        for edge in out.edges {
            circuit.add_edge(&edge.from, &edge.to, edge.weight)
        }

        //println!("Lenght of edges {:?}", circuit.edges.len());
        //println!("Floyd warshall longest path {:?} bruteforce ", circuit.calculate_longest_path_via_top_sort());
        //println!("Circuit is {:?}", circuit);
        //println!("Calculating paths");
        //circuit.calculate_paths();
        //println!("Calculating longest paths");
        let longest_path_length: f64 = circuit.calculate_longest_path_via_top_sort(|x| x.float_weight);
        
        io::stdout().flush().unwrap();
        println!("Assigning discrete steps..., longest path f64 {:?}", longest_path_length);
        let max_steps = circuit.assign_discrete_weight(longest_path_length);
        println!("Max steps {:?} ", max_steps);
        println!("Updating max steps to account for rounding error");
        let longest_path_length: i64 = circuit.calculate_longest_path_via_top_sort(|x| x.discrete_weight);
        circuit.longest_discrete_path = Some(longest_path_length);
        let max_steps =  circuit.get_cycle_time(longest_path_length as f64).ceil() as i64;
        circuit.clk_period = max_steps;
        println!("New max steps {:?}", max_steps);
//        println!("max flow {:?}", circuit.calculate_longest_path_via_max_flow(|x| x.discreteWeight));
        //println!("Precomputing reachable flop mapping!");
        let inject_into_edges: Vec<_> = out.inject_into_edges.iter().map(|x| (circuit.node_to_graph_index[&x.0], circuit.node_to_graph_index[&x.1])).collect();
        circuit.inject_into_edges = inject_into_edges;
        circuit
    }

    pub fn dump_timing_data(&mut self, outfile_path: &str){
        let path_dist: Vec<(String, String, i64)> = self.get_path_distribution();
        let final_result: TimingAnalysis = TimingAnalysis {clk_period: self.clk_period, path_distribution: path_dist, longest_discrete_path: self.longest_discrete_path.unwrap()};
        println!("Now writing to {:?}", outfile_path);
        let file = File::create(outfile_path).unwrap();
        let mut writer = BufWriter::new(file);
        serde_json::to_writer(&mut writer, &final_result).unwrap();
        writer.flush().unwrap();
    }

    pub fn add_node(&mut self, name: String, cell_type: CellType) {
        let node: CircuitElement = CircuitElement {
            _name: name.to_string(),
            cell_type: cell_type,
        };
        let node_index = self.circuit.add_node(node);
        self.node_to_graph_index
            .insert(name.to_string(), node_index);
        self.graph_index_to_node
            .insert(node_index, name.to_string());
        if cell_type == CellType::InFlop {
            self.input_nodes.insert(node_index);
        } else if cell_type == CellType::OutFlop {
            self.output_nodes.push(node_index);
        }
    }

    pub fn add_edge(&mut self, from: &str, to: &str, float_weight: f64) {
        self.circuit.add_edge(
            self.node_to_graph_index[from],
            self.node_to_graph_index[to],
            CircuitWire {
                float_weight,
                discrete_weight: 0,
            },
        );
        self.edges
            .push((self.node_to_graph_index[from], self.node_to_graph_index[to]));
    }

    pub fn _calculate_paths(&mut self) {
        println!(
            "Calculating paths dict len in_nodes {:?}, len out_nodes {:?}",
            self.input_nodes.len(),
            self.output_nodes.len()
        );
        for edge in self.edges.iter().progress() {
            self._edge_to_paths.insert(*edge, Vec::new());
        }
        io::stdout().flush().unwrap();
        for in_node in self.input_nodes.iter().progress() {
            for out_node in self.output_nodes.iter() {
                //io::stdout().flush().unwrap();
                //println!("Calculating all simples paths {:?} {:?}", in_node, out_node);
                let paths = all_simple_paths::<Vec<_>, &DiGraph<CircuitElement, CircuitWire>>(
                    &self.circuit,
                    *in_node,
                    *out_node,
                    0,
                    None,
                ); //.collect::<Vec<_>>();
                let mut arc_paths = Vec::new();
                for p in paths {
                    arc_paths.push(Arc::new(p));
                    //match self.paths_to_id_bymap.get_by_right(p) {
                    //    Some(path_id) => {arc_paths.push(path_id);},
                    //    None => {self.paths_to_id_bymap.insert(self.path_counter, p); self.path_counter += 1;}
                    //}

                    //}
                }
                //let arc_paths = arc_paths.
                let paths = Arc::new(arc_paths); /*unsafe {
                                                     Arc::from_raw(arc_paths.as_ptr()) //.into(); //.clone();
                                                 };*/
                //println!("Calculating all simples paths done {:?} {:?}, size {:}", in_node, out_node, paths.len());
                //let paths = Arc::new(paths.iter().map(|p| Arc::new(p)).collect::<Vec<_>>());
                if paths.len() > 0 {
                    for arc_p in paths.iter() {
                        //.map(|p| Arc::new(*p)) {
                        //let arc_p = Arc::new(*p);
                        //print!("Path {:?} pairwise: ", p);
                        //let edge_iter = &mut (self.paths_to_id_bymap.get_by_left(path_id).unwrap()).iter().map(|x| *x);
                        let edge_iter = &mut (arc_p).iter().map(|x| *x);
                        for edge in utils::pairwise(edge_iter) {
                            self._edge_to_paths
                                .get_mut(&edge)
                                .unwrap()
                                .push(arc_p.clone());
                        }

                        // for edge in nx.utils.pairwise(p):
                        //self.edge_to_path[edge].append(p)
                    }
                    self.paths_dict.insert((*in_node, *out_node), paths);
                    //println!("In nodes {:?} and out nodes {:?}, paths {:#?}", in_node, out_node, paths);
                }
            }
        }
        println!("Calculating paths dict done");
        //println!("edge_to_paths dict {:?}", self.edge_to_paths);
    }

    /*pub fn _dump_paths(&self) {
        for ((in_node, out_node), paths) in self.paths_dict.iter() {
            for p in paths.iter() {
                println!(
                    "In node {:?} Out Node {:?} Path Length {:?}",
                    self.graph_index_to_node[in_node],
                    self.graph_index_to_node[out_node],
                    self.get_path_length(*p, |x| x.discrete_weight)
                );
            }
        }
    }*/

    pub fn get_path_distribution(&self) -> Vec<(String, String, i64)> { //change to f64 and float_weight for floating point dist
        //println!("Getting path distribution, output nodes {:?}", self.output_nodes);
        let mut path_dist: Arc<Mutex<Vec<(String, String, i64)>>> = Arc::new(Mutex::new(Vec::new()));
        let topsort = toposort(&self.circuit, None).unwrap();
        self.input_nodes.iter().collect::<Vec<&NodeIndex>>().iter().progress().for_each(|in_node| {
            let mut dist_map: HashMap<NodeIndex, i64> = HashMap::new();
            //let source_node = edge.0;
            let start_node = **in_node;
            let position = topsort
                .iter()
                .position(|&node| node == start_node)
                .unwrap();
            //if dist.get(&target_node).is_none() {
            //    println!("Skipping target_node {:?}", self.graph_index_to_node[&target_node]);
            //    self.edge_to_reachable_flops.insert(*edge, Arc::new(dist_map));
            //    continue;
            //}
            dist_map.insert(start_node, 0);
            for i in position..topsort.len() {
                let v = topsort[i];
                for in_edge in self.circuit.edges_directed(v.clone(), Incoming) {
                    let pred = in_edge.source();
                    if dist_map.get(&pred).is_none() {
                        continue;
                    }
                    let curr_value = dist_map.get(&v).unwrap_or(&0).clone();
                    let pred_value = dist_map.get(&pred).unwrap().clone();
                    let cmp_value = pred_value + in_edge.weight().discrete_weight; //float_weight would work,too
                    if curr_value <= cmp_value {
                        //.floatWeight {
                        dist_map.insert(v, cmp_value);
                    }
                }
            }
            //println!("Dist map {:?}", dist_map);
            dist_map.retain(|&x, _| self.output_nodes.contains(&x));
            //println!("Dist map {:?}", dist_map);
            for (out_node, length) in dist_map.iter() {
                path_dist.lock().unwrap().push((
                    self.graph_index_to_node[in_node].to_string(),
                    self.graph_index_to_node[out_node].to_string(),
                    *length //self.get_path_length(p, |x| x.discrete_weight),
                ));
            }
            /* 
            for out_node in self.output_nodes.iter().filter(|x| self.input_nodes.contains(x)) {
                let paths = all_simple_paths::<Vec<_>, &DiGraph<CircuitElement, CircuitWire>>(
                    &self.circuit,
                    *in_node,
                    **out_node,
                    0,
                    None,
                ).collect::<Vec<_>>();
                println!("Between {:?} and {:?} are {:?} paths", self.graph_index_to_node[in_node], self.graph_index_to_node[out_node],paths.len());
                for p in paths.into_iter() {
                    {
                        println!("Between {:?} and {:?} path:", self.graph_index_to_node[in_node],self.graph_index_to_node[out_node]);//, self.graph_index_to_node[in_node],paths.len());
                        println!("Path ");
                        self.print_path(&p);
                        path_dist.lock().unwrap().push((
                            self.graph_index_to_node[in_node].to_string(),
                            self.graph_index_to_node[out_node].to_string(),
                            self.get_path_length(p, |x| x.discrete_weight),
                        ));
                    }
                }
            } */
        });
    
        //for ((in_node, out_node), paths) in self.paths_dict.iter() {
        //    for p in paths.iter() {
        //        path_dist.push((
        //            self.graph_index_to_node[in_node].to_string(),
        //            self.graph_index_to_node[out_node].to_string(),
        //            self.get_path_length(p, |x| x.discrete_weight),
        //        ));
        //    }
        //}
        Arc::try_unwrap(path_dist).unwrap().into_inner().unwrap()
    }

    pub fn _get_cached_path_length(&self, path: &Arc<Vec<NodeIndex>>) -> i64 {
        *self._path_to_cached_length.get(path).unwrap() //.copied()
    }

    pub fn get_path_length<WeightType, GetWeightFunc>(
        &self,
        path: Vec<NodeIndex>,
        get_weight_func: GetWeightFunc,
    ) -> WeightType
    where
        WeightType: Add + Default + AddAssign,
        GetWeightFunc: Fn(&CircuitWire) -> WeightType,
    {
        //if TypeId::of::<WeightType>() == TypeId::of::<i64>() && let Some(path_length) = self.get_cached_path_length(path){
        //    return path_length
        //}
        let mut path_length: WeightType = Default::default();
        let mut edge_iter = path.iter();
        for edge_tuple in utils::pairwise(&mut edge_iter) {
            let edge_index = self
                .circuit
                .find_edge(*edge_tuple.0, *edge_tuple.1)
                .unwrap();
            let edge = self.circuit.edge_weight(edge_index).unwrap();
            path_length += get_weight_func(edge);
        }
        path_length
    }

    pub fn print_path(&self, path: &Vec<NodeIndex>) {
        println!(
            "Path {:?}",
            path.iter()
                .map(|x| self.graph_index_to_node[x].to_string())
                .collect::<Vec<String>>()
        );
    }

    //    pub fn calculate_longest_path_max_flow(&self){
    //        utils::convert_graph(self.circuit);

    //    }

    //Example call: self.get_path_length::<f64, _>(path, |x| x.floatWeight);
    /* pub fn _calculate_longest_path<WeightType, GetWeightFunc>(
        &mut self,
        get_weight_func: GetWeightFunc,
    ) -> WeightType
    where
        WeightType: Add + Default + AddAssign + std::cmp::PartialOrd + std::fmt::Debug + 'static,
        GetWeightFunc: Fn(&CircuitWire) -> WeightType,
    {
        let mut max_path_length: WeightType = WeightType::default();
        let mut max_path = None;
        for ((_, _), possible_paths) in self.paths_dict.iter() {
            for path in possible_paths.iter() {
                let tmp_length = self.get_path_length::<WeightType, _>(path, &get_weight_func);
                if TypeId::of::<WeightType>() == TypeId::of::<i64>() {
                    let tmp_length_i64: i64 =
                        self.get_path_length::<i64, _>(path, |x| x.discrete_weight);
                    self._path_to_cached_length
                        .insert(path.clone(), tmp_length_i64);
                }
                if tmp_length > max_path_length {
                    max_path_length = tmp_length;
                    max_path = Some(path.clone());
                }
            }
        }
        println!("Max path length {:?}", max_path_length); // {:?}", max_path_length, max_path.unwrap().iter().map(|x| self.graph_index_to_node[x].to_string()).collect::<Vec<String>>());
        self._print_path(&max_path.unwrap());
        max_path_length
    } */

    pub fn calculate_longest_path_via_top_sort<WeightType, GetWeightFunc>(
        &self,
        get_weight_func: GetWeightFunc,
    ) -> WeightType
    where
        WeightType: Copy
            + Add<Output = WeightType>
            + Default
            + AddAssign
            + std::cmp::PartialOrd
            + std::fmt::Debug
            + 'static,
        GetWeightFunc: Fn(&CircuitWire) -> WeightType,
    {
        let topsort = toposort(&self.circuit, None).unwrap();
        let mut dist: HashMap<NodeIndex, WeightType> = HashMap::new();
        for v in topsort.iter() {
            for in_edge in self.circuit.edges_directed(v.clone(), Incoming) {
                let curr_value = dist.get(v).unwrap_or(&WeightType::default()).clone();
                let pred = in_edge.source();
                let pred_value = dist.get(&pred).unwrap().clone();
                let cmp_value = pred_value + get_weight_func(in_edge.weight());
                if curr_value < cmp_value {
                    //.floatWeight {
                    dist.insert(*v, cmp_value);
                }
            }
            if dist.get(v).is_none() {
                dist.insert(*v, WeightType::default());
            }
        }
        let mut m = WeightType::default();
        let mut longest_end_point: NodeIndex = NodeIndex::default();
        for (end_point, value) in dist.into_iter() {
            if value > m {
                m = value;
                longest_end_point = end_point;
            }
        }
        println!("Longest path ends in {:?} and is of length {:?}", self.graph_index_to_node[&longest_end_point], m);
        m
    }

    pub fn precompute_edge_to_reachable_flop_mapping(
        &mut self,
        inject_into_edges: Vec<(NodeIndex, NodeIndex)>,
    ) {
        let topsort = toposort(&self.circuit, None).unwrap();
        let mut dist: HashMap<NodeIndex, i64> = HashMap::new();
        //For each node, store the predecessors that can reach this node
        //let mut preds: HashMap<NodeIndex, HashSet<NodeIndex>> = HashMap::new();
        self.nodes_to_pred =  HashMap::new();
        //println!("Topsort {:?}", topsort[0]);
        //println!("Topsort {:?}", self.input_nodes[0]);
        for x_in in self.input_nodes.iter() {
            dist.insert(*x_in, 0);
            self.nodes_to_pred.insert(*x_in, HashSet::from([*x_in]));
        }
        //println!("dist {:?}", dist);
        for v in topsort.iter() {
            for in_edge in self.circuit.edges_directed(v.clone(), Incoming) {
                let curr_value = dist.entry(*v).or_insert(0).clone();//.unwrap_or(&0).clone();
                let pred = in_edge.source();
                //if dist.get(&pred).is_none() {
                //    continue;
                //}
                let pred_value = dist.get(&pred).unwrap().clone();
                let cmp_value = pred_value + in_edge.weight().discrete_weight;
                if curr_value < cmp_value {
                    //.floatWeight {
                    dist.insert(*v, cmp_value);
                }
                let preds_this_node = self.nodes_to_pred[&pred]
                .iter()
                .map(|x| x.clone())
                .collect::<Vec<NodeIndex>>();
                //println!("preds this node {:?}", preds_this_node);
                //let mut abort = false;
                //if preds_this_node.len()>2 {
                //    println!("Preds this done {:?}", &preds_this_node);
                //    abort = true;
                    //panic!("test");
                //}
                //if (self.graph_index_to_node[v] == "\\u_ibex_core.id_stage_i.controller_i.instr_i[31]"){
                //    println!("Preds for {:?} {:?}", self.graph_index_to_node[&pred], preds_this_node.iter().map(|x| self.graph_index_to_node[x].clone()).collect::<Vec<String>>());
                //}
                self.nodes_to_pred.entry(*v).or_insert(HashSet::<NodeIndex>::from([*v])).extend(preds_this_node);
                //if (self.graph_index_to_node[v] == "\\u_ibex_core.id_stage_i.controller_i.instr_i[31]"){
                //    let in_nodes = self.nodes_to_pred.get(&v).unwrap();
                //    println!("in_nodes {:?}", in_nodes.iter().map(|&x| self.graph_index_to_node[&x].clone()).collect::<Vec<String>>());
                //}
                //if abort == true {

                //    println!("nodes_to_pred {:?}", self.nodes_to_pred[v]);
                //    panic!("test")
                //}
                //Add preds[pred] to preds[v]
            }
            if dist.get(v).is_none() {
                //println!("Initializing {:?} to zero", self.graph_index_to_node[v], self.circuit.edges_directed(v.clone(), Incoming));
                dist.insert(*v, 0);
                self.nodes_to_pred.insert(*v, HashSet::from([*v]));
            }
        }
        //println!("dist {:?}", dist);
        //println!("Nodes to pred {:?}", self.nodes_to_pred[&self.node_to_graph_index["\\u_ibex_core.id_stage_i.controller_i.instr_i[31]"]]);
        //println!("Input nodes {:?}", self.input_nodes.iter().map(|x| utils::process_flop_name(&self.graph_index_to_node[&x].to_string())).collect::<Vec<String>>());
        for edge in inject_into_edges.iter().progress() {
            let mut dist_map: HashMap<NodeIndex, i64> = HashMap::new();
            //let source_node = edge.0;
            let target_node = edge.1;
            let position = topsort
                .iter()
                .position(|&node| node == target_node)
                .unwrap();
            //if dist.get(&target_node).is_none() {
            //    println!("Skipping target_node {:?}", self.graph_index_to_node[&target_node]);
            //    self.edge_to_reachable_flops.insert(*edge, Arc::new(dist_map));
            //    continue;
            //}
            dist_map.insert(target_node, *dist.get(&target_node).unwrap());
            for i in position..topsort.len() {
                let v = topsort[i];
                for in_edge in self.circuit.edges_directed(v.clone(), Incoming) {
                    let pred = in_edge.source();
                    if dist_map.get(&pred).is_none() {
                        continue;
                    }
                    let curr_value = dist_map.get(&v).unwrap_or(&0).clone();
                    let pred_value = dist_map.get(&pred).unwrap().clone();
                    let cmp_value = pred_value + in_edge.weight().discrete_weight;
                    if curr_value <= cmp_value {
                        //.floatWeight {
                        dist_map.insert(v, cmp_value);
                    }
                }
            }
            dist_map.retain(|&x, _| self.output_nodes.contains(&x));
            self.edge_to_reachable_flops
                .insert(*edge, Arc::new(dist_map));
        }
        //println!("Edge to reachable flops {:?}", self.edge_to_reachable_flops);
        //for v in self.input_nodes.iter() {

        //}
    }

    //VINCENT: This is wrong!
    /*
    pub fn calculate_longest_path_via_max_flow<WeightType, GetWeightFunc>(&mut self, get_weight_func: GetWeightFunc)
    where WeightType: Add + Sub +  Clone +std::cmp::Ord + SubAssign + Default + AddAssign + std::cmp::PartialOrd + std::fmt::Debug + 'static, GetWeightFunc: Fn(&CircuitWire) -> WeightType {
        //let mut max_path_length: WeightType = WeightType::default();
        //let mut max_path = None;
        //for ((xin, xout), possible_paths) in self.paths_dict.iter(){
        let helper_source_node: CircuitElement = CircuitElement { name: "Source".to_string(), cell_type: CellType::HelperSource};
        let helper_sink_node: CircuitElement = CircuitElement { name: "Sink".to_string(), cell_type: CellType::HelperSink};
        let source_node_index = self.circuit.add_node(helper_source_node);
        let helper_sink_index = self.circuit.add_node(helper_sink_node);
        //for in_node in self.input_nodes.iter().progress() {
        //    self.circuit.add_edge(source_node_index, *in_node, CircuitWire { floatWeight: 100_000.0, discreteWeight: 100_000 });
        //}
        //for out_node in self.output_nodes.iter().progress() {
        //     self.circuit.add_edge(*out_node, helper_sink_index, CircuitWire { floatWeight: 100_000.0, discreteWeight: 100_000 });
        //}
        let mut max_flow = WeightType::default();
        for in_node in self.input_nodes.iter().progress() {
            for out_node in self.output_nodes.iter().progress() {
                max_flow = max(max_flow, flow::edmonds_karp(&self.circuit, *in_node, *out_node, &get_weight_func));
            }
        }
        println!("Max flow {:?}",max_flow);
        //    for path in possible_paths.iter() {
        //        let tmp_length = self.get_path_length::<WeightType, _>(path, &get_weight_func);
        //        if TypeId::of::<WeightType>() == TypeId::of::<i64>() {
        //            let tmp_length_i64: i64 = self.get_path_length::<i64, _>(path, |x| x.discreteWeight);
        //            self.path_to_cached_length.insert(path.clone(), tmp_length_i64);
        //        }
        //        if tmp_length > max_path_length {
        //            max_path_length = tmp_length;
        //            max_path = Some(path.clone());
        //        }
        //    }
        //}

        //println!("Max path length {:?}", max_path_length);// {:?}", max_path_length, max_path.unwrap().iter().map(|x| self.graph_index_to_node[x].to_string()).collect::<Vec<String>>());
        //self.print_path(&max_path.unwrap());
        //max_path_length
    }
    */

    pub fn assign_discrete_weight(&mut self, longest_path_length: f64) -> i64 {
        //Assign discrete weight and return max steps

        let cycle_time: f64 = self.get_cycle_time(longest_path_length);
        /*let mut v = self
        .circuit
        .edge_references()
        .map(|edge_reference| edge_reference.weight().float_weight)
        .collect::<Vec<f64>>();
        v.sort_by(|a,b| a.total_cmp(&b));
        println!("Out v {:?}",v);*/
        /*let mut uniq_edge_weights = self
                            .circuit
                            .edge_references()
                            .map(|edge_reference| edge_reference.weight().float_weight.to_string()).collect::<HashSet<String>>()
                            .into_iter()
                            .map(|str_weight| str_weight.parse::<f64>().unwrap())
                            .collect::<Vec<f64>>();
        uniq_edge_weights.sort_by(|a,b| a.total_cmp(&b));
                            //.collect::<Vec<f64>>().sorted();
        println!("Edge weights {:?}", uniq_edge_weights);*/
        let min_edge_weight = self
            .circuit
            .edge_references()
            .map(|edge_reference| edge_reference.weight().float_weight)
            .filter(|x| *x > 0.0)
            .fold(f64::INFINITY, |a, b| a.min(b));
        let min_edge_weight = min_edge_weight / 2.0;
        let max_steps: i64 = (cycle_time / min_edge_weight).ceil() as i64;
        //println!("Min edge weight: {:?}", min_edge_weight);
        //println!("Edge weights: {:?}", self.circuit.edge_references().map(|edge_reference| edge_reference.weight().floatWeight).collect::<Vec<f64>>());
        self.circuit.edge_weights_mut().for_each(|wire| {
            wire.discrete_weight = (wire.float_weight / min_edge_weight).ceil() as i64
        });
        //println!("New edge weights {:?}", self.circuit.edge_references().map(|edge_reference| edge_reference.weight()));
        max_steps
    }

    pub fn get_cycle_time(&mut self, longest_path_length: f64) -> f64 {
        let cycle_time: f64 = longest_path_length+1.0; // + params::TIMING_SLACK * longest_path_length;
        cycle_time
    }

    //Trace the delay defect and return HashSet
    pub fn trace_delay_defect(
        &self,
        edge: &(NodeIndex, NodeIndex),
        delay: i64,
        clk_period: i64,
    ) -> HashSet<NodeIndex> {
        let mut static_reachable_flops: HashSet<NodeIndex> = HashSet::new();
        //for p in self.edge_to_paths[edge].iter(){
        //    let mut path_length = self.get_cached_path_length(p); //self.get_path_length(p, |x| x.discreteWeight);
        //    path_length += delay;
        //    if path_length as f64>clk_period {
        //static_reachable_flops.insert(self.graph_index_to_node[p.last().unwrap()].to_string());
        //        static_reachable_flops.insert(*p.last().unwrap());
        //    }
        //}
        let reachable_flops = self.edge_to_reachable_flops.get(edge).unwrap();
        for (flop, longest_path_len) in reachable_flops.iter() {
            if (longest_path_len + delay) > clk_period {
                static_reachable_flops.insert(*flop);
            }
        }
        //if static_reachable_flops.len() > 0 {
        //println!("Static reachable flop {:?}", static_reachable_flops);
        //}
        static_reachable_flops
    }

    pub fn get_fan_out_of_edge(&self, edge: &(NodeIndex, NodeIndex)) -> HashSet<NodeIndex> {
        //let mut fan_out_set: HashSet<NodeIndex> = HashSet::new();
        //for p in self.edge_to_paths[edge].iter(){
        //   fan_out_set.insert(*p.last().unwrap());
        //
        //}
        let fan_out_set = self.trace_delay_defect(edge, 0, 0 as i64); // Hack for now
        fan_out_set
    }
}
