use crate::circuit_graph::{CircuitElement, CircuitGraph};
use petgraph::graph::NodeIndex;
use petgraph::visit::EdgeRef;
use std::{collections::{HashMap, HashSet}, sync::Arc};
use smallvec::SmallVec;

type FlopMapIndexType = NodeIndex; //NodeIndex;
type FlopValueType = bool;
pub type RecursiveValMapType = Vec<HashMap<i64, FlopValueType>>; //HashMap<FlopMapIndexType, HashMap<i64, FlopValueType>>

#[derive(Default)]
pub struct Simulator {
    circuit: Arc<CircuitGraph>,
    pub values_prior_cycle: HashMap<FlopMapIndexType, bool>,
    values_this_cycle: HashMap<FlopMapIndexType, bool>,
    flop_idx_to_string: HashMap<FlopMapIndexType, String>,
    _flop_string_to_idx: HashMap<String, FlopMapIndexType>,
    _gate_string_to_idx: HashMap<String, FlopMapIndexType>,
    idx_to_gate_string: HashMap<FlopMapIndexType, String>,
    max_steps: usize,
}

fn int_to_flop_value(x: i64) -> FlopValueType {
    x != 0
}

impl Simulator {
    pub fn new(
        circuit: Arc<CircuitGraph>,
        values_prior_cycle: &HashMap<String, i64>,
        values_this_cycle: &HashMap<String, i64>,
        max_steps: usize,
    ) -> Self {
        let mut values_prior_cycle_map: HashMap<FlopMapIndexType, bool> = HashMap::new();//Vec::with_capacity(values_prior_cycle.len());
        let mut values_this_cycle_map: HashMap<FlopMapIndexType,bool> = HashMap::new(); //Vec::with_capacity(values_this_cycle.len());
        let mut flop_idx_to_string: HashMap<FlopMapIndexType, String> = HashMap::new();
        let mut flop_string_to_idx: HashMap<String, FlopMapIndexType> = HashMap::new();
        let mut gate_string_to_idx: HashMap<String, FlopMapIndexType> = HashMap::new();
        let mut idx_to_gate_string: HashMap<FlopMapIndexType, String> = HashMap::new();

        for (key, value) in values_prior_cycle.iter() {
            //println!("Now trying to find key {:?}", key);
            let idx = circuit.node_to_graph_index[key];
            flop_idx_to_string.insert(idx, key.to_string());//)idx, key.to_string());
            flop_string_to_idx.insert(key.to_string(), idx);
            values_prior_cycle_map.insert(idx, int_to_flop_value(*value));
            //values_this_cycle_vec.insert(idx, int_to_flop_value(*value));
        }
        for (key, value) in values_this_cycle.iter() {
            //flop_idx_to_string.insert(idx, key.to_string());
            let idx = circuit.node_to_graph_index[key]; 
            values_this_cycle_map.insert(idx, int_to_flop_value(*value));
        }
        //let max_idx = values_this_cycle_map.len();
        //let mut curr_idx = max_idx;
        for node in circuit.node_to_graph_index.keys() {
            if flop_string_to_idx.contains_key(node) {
                continue;
            } else {
                let idx = circuit.node_to_graph_index[node];
                gate_string_to_idx.insert(node.to_string(), idx);
                idx_to_gate_string.insert(idx, node.to_string());
                //curr_idx += 1;
            }
        }
        Self {
            circuit: circuit,
            values_prior_cycle: values_prior_cycle_map,
            values_this_cycle: values_this_cycle_map,
            flop_idx_to_string: flop_idx_to_string,
            _flop_string_to_idx: flop_string_to_idx,
            max_steps: max_steps,
            _gate_string_to_idx: gate_string_to_idx,
            idx_to_gate_string: idx_to_gate_string,
            ..Default::default()
        }
    }

    pub fn reset(&self, recursive_val_map: &mut RecursiveValMapType) {
        //self.recursive_val = HashMap::new();
        //for idx in self.flop_idx_to_string.keys() {
        //    self.recursiveVal.insert(idx, Vec::with_capacity(self.max_steps))
        //}
        //println!("Starting reset");
        //recursive_val_map.clear();

        //Change this to None?
        *recursive_val_map = vec![HashMap::<i64, FlopValueType>::new(); self.circuit.graph_index_to_node.len()];
        /*for (idx, value) in self.values_this_cycle.iter() {
            let value_map: HashMap<i64, FlopValueType> =  HashMap::new(); //           recursive_val_map.get_mut(&idx).unwrap(); //, vec![Some(*value); self.max_steps]);
            recursive_val_map.insert(*idx, value_map);
            let value_map =recursive_val_map.get_mut(&idx).unwrap();
            for i in 0..self.max_steps {
                value_map.insert(i as i64,*value);
            }
        }*/
        for out_flop_idx in self.circuit.output_nodes.iter() {
            recursive_val_map[out_flop_idx.index()] = HashMap::new();  //.insert(*out_flop_idx, HashMap::new()); //vec![None; self.max_steps]);
        }
        for gate_idx in self.idx_to_gate_string.keys() {
            recursive_val_map[gate_idx.index()] = HashMap::new();   //.insert(*gate_idx, HashMap::new()); //vec![None; self.max_steps]);
        }
    }
        //println!("Reset done");
    
    pub fn _edge_is_toggling(&self, edge: &(FlopMapIndexType, FlopMapIndexType)){
        let edge_in_node: NodeIndex = edge.0;
        let in_nodes = self.circuit.nodes_to_pred.get(&edge_in_node).unwrap();
        let mut _all_equal: bool = true;
        //println!("In nodes of {:?}, in_nodes {:?}, {:?}", self.circuit.graph_index_to_node[&edge_in_node], in_nodes.iter().map(|&x| self.circuit.graph_index_to_node[&x].clone()).collect::<Vec<String>>(), in_nodes);
        for node in in_nodes.iter(){
            if self.values_this_cycle.get(node) != self.values_prior_cycle.get(node){
                //println!("{:?} is toggling", self.circuit.graph_index_to_node[node]);
                _all_equal = false;
            }

        }
    }

    pub fn run(
        &self,
        for_flops_arg: Option<&HashSet<FlopMapIndexType>>,
        delay: Option<i64>,
        delayed_edge: Option<&(FlopMapIndexType, FlopMapIndexType)>,
    ) -> HashMap<String, i64> {
        if delayed_edge.is_some() {
            let edge_in_node: NodeIndex = delayed_edge.unwrap().0;
            let in_nodes = self.circuit.nodes_to_pred.get(&edge_in_node).unwrap();
            let mut all_equal: bool = true;
            //println!("In nodes of {:?}, in_nodes {:?}", edge_in_node, in_nodes);
            for node in in_nodes.iter(){
                //println!("Checking whether input node {:?} toggled", node);
                if self.values_this_cycle.get(node) != self.values_prior_cycle.get(node){
                    //println!("{:?} is toggling", self.circuit.graph_index_to_node[node]);
                    all_equal = false;
                    break;
                }
            }
            if all_equal == true {
                return HashMap::<String, i64>::new();
            }
        }
        let mut ret_hashmap = HashMap::<String, i64>::new();
        if (2*(self.max_steps as i64)) < (self.circuit.longest_discrete_path.unwrap()+delay.unwrap_or(0)) {
            panic!("Multi-cycle delay is not supported {:?} {:?}!", self.max_steps, self.circuit.longest_discrete_path.unwrap()+delay.unwrap_or(0));
        };
        //println!("For flops arg {:?} {:?}", for_flops_arg, self.flop_idx_to_string[&self.flop_string_to_idx[for_flops_arg.unwrap().iter().next().unwrap()]]);
        /*let for_flops = match for_flops_arg {
            None => &(self
                .flop_idx_to_string
                .keys()
                .map(|x| x.clone())
                .collect::<HashSet<FlopMapIndexType>>()),
            Some(for_flops_inner_arg) => { for_flops_inner_arg }
            //Some(for_flops_inner_arg) => {
            //    for_flops_inner_arg.iter().map(|k| self.flop_string_to_idx[k]).collect()
                //self
                //.flop_string_to_idx
                //.iter()
                //.filter(|&(k, _v)| for_flops_inner_arg.contains(k))
                //.map(|(_k, v)| *v as usize)
                //.collect::<Vec<FlopMapIndexType>>(),
            //}
        //};*/
        let all_flops; // To guarantee correct lifetime later on
        let for_flops = match for_flops_arg {
            Some(for_flops_inner_arg) => for_flops_inner_arg,
            None => {
                all_flops = self.flop_idx_to_string.keys().map(|x| x.clone()).collect::<HashSet<FlopMapIndexType>>();
                &all_flops 
            }
        };

        let mut recursive_val_map: RecursiveValMapType = Vec::new();// = vec![HashMap::<i64, FlopValueType>::new(); self.circuit.graph_index_to_node.len()]; // Works because hashmap implements clone as a deep copy? //Vec::with_capacity(self.circuit.graph_index_to_node.len());//vec![HashMap::new(); self.]//HashMap<FlopMapIndexType, HashMap<i64, FlopValueType>> = HashMap::new();
        self.reset(&mut recursive_val_map);
        for flop in for_flops { // panic!("Not yet implemented!")){ //self.flop_idx_to_string.keys().map(|x| x.clone()).collect::<HashSet<FlopMapIndexType>>()) {
            recursive_val_map[flop.index()] = HashMap::new(); //.insert(*flop,HashMap::new());
            //println!("Recursive vlaue map here {:?}", recursive_val_map);
            //println!("Calculating for flop {:?}", self.flop_idx_to_string[&flop]);
            let val = self.get_recursive_val(
                (self.max_steps as i64)-1,
                *flop,
                delay,
                delayed_edge,
                &mut recursive_val_map,
            );
            //println!("Returning flop {:?} ", flop); // self.flop_idx_to_string);
            ret_hashmap.insert(self.flop_idx_to_string[&flop].to_string(), val as i64);
            //if self.circuit.graph_index_to_node[flop] == "\\o_wreg1[0]" {
            //    println!("{:?}", self.print_predecessor(*flop, (self.max_steps as i64)-1, delay,delayed_edge, &mut recursive_val_map));
            //}
        }
        //println!("Recurisve val map {:?}", recursive_val_map);
        ret_hashmap
    }

    fn node_idx_is_flop(&self, node_idx: FlopMapIndexType) -> bool {
        self.values_prior_cycle.contains_key(&node_idx)
    }

    fn _node_idx_to_string(&self, node_idx: FlopMapIndexType) -> &String {
        let node_string: &String = if self.node_idx_is_flop(node_idx) == true {
            &self.flop_idx_to_string[&node_idx]
        } else {
            &self.idx_to_gate_string[&node_idx]
        };
        node_string
    }

    pub fn get_recursive_val(
        &self,
        step: i64,
        node_idx: FlopMapIndexType,
        delay: Option<i64>,
        delayed_edge: Option<&(NodeIndex, NodeIndex)>,
        recursive_val_map: &mut RecursiveValMapType,
    ) -> FlopValueType {
        //print!("I am calling {:?} nodeidx {:?}", step, node_idx);
        //println!("nodeString {:?}" ,self.flop_idx_to_string.get(&node_idx));
        //We now assert that there is no multi-cycle delay at the run function
        //if step < (-1) * (self.max_steps as i64) {
        //    panic!("Multi-cycle delay is not supported!");
        //};
        //if self.node_idx_is_flop(node_idx) {
            if self.circuit.input_nodes.contains(&node_idx) {
                if step < 0   {
                    //let edge_in_node: NodeIndex = delayed_edge.unwrap().0;
                    //let in_nodes = self.circuit.nodes_to_pred.get(&edge_in_node).unwrap();
                    //if !(in_nodes.contains(&node_idx)){
                    //    panic!("For edge {:?} need {:?} but in_nodes {:?}, pred {:?}", delayed_edge, self.circuit.graph_index_to_node[&node_idx], in_nodes.iter().map(|&x| self.circuit.graph_index_to_node[&x].clone()).collect::<Vec<String>>(), self._print_predecessor(edge_in_node, self.max_steps as i64,None,None, recursive_val_map));

                    //}
                    return self.values_prior_cycle[&node_idx];
                } else {
                    return self.values_this_cycle[&node_idx];
                }
            }
        //}
        //}
        //if step < 0 {
        //    println!("Step is smaller 0 at key {:?}", self.circuit.graph_index_to_node[&node_idx]);
        //}
        //if (step < (self.max_steps as i64 -1) && self.circuit.output_nodes.contains(&node_idx) ) {
        //    println!("Visting output node {:?} at step {:?} incoming {:?} outgoing {:?}", self.circuit.graph_index_to_node[&node_idx], step,  self.circuit.circuit.edges_directed(node_idx, petgraph::Direction::Incoming).map(|e| (self.circuit.graph_index_to_node[&e.source()].to_string(), self.circuit.graph_index_to_node[&e.target()].to_string())).collect::<Vec<(String, String)>>(), self.circuit.circuit.edges_directed(node_idx, petgraph::Direction::Outgoing).map(|e| (self.circuit.graph_index_to_node[&e.source()].to_string(), self.circuit.graph_index_to_node[&e.target()].to_string())).collect::<Vec<(String, String)>>());
        //    panic!("Should not recursively visit an output node?");
        //}
        if let Some(inner_val) = recursive_val_map[node_idx.index()].get(&step) { //.is_some() {
            //println!("Returning because of pre-determined value {:?}",recursive_val_map[&(node_idx as usize)][step as usize] );
            return *inner_val; //recursive_val_map[node_idx.index()][&step];
        };

        //let node_string = self.node_idx_to_string(node_idx);
        //let node_graph_index = self.circuit.node_to_graph_index[node_string];
        //println!("Calling with  {:?} {:?} {:?} {:?}",self.circuit.graph_index_to_node[&node_graph_index], step, self.max_steps, recursive_val_map[&(node_idx as usize)][step as usize] );
        let elem: &CircuitElement = self.circuit.circuit.node_weight(node_idx).unwrap();
        //let mut input_values: Vec<FlopValueType> = Vec::new();
        let mut input_values: SmallVec<[FlopValueType; 5]> = SmallVec::with_capacity(4);
        let mut out_val: Option<bool> = None;
        //let delayed_edge_index = self
        //    .circuit
        //    .circuit
        //    .find_edge(delayed_edge.0, delayed_edge.1)
        //    .unwrap();
        //println!("in edges of node {:?} {:?}", node_idx, self.circuit.circuit.edges_directed(node_idx, petgraph::Direction::Incoming));
        //println!("in edges of node {:?} {:?}", self.circuit.graph_index_to_node[&node_graph_index], self.circuit.circuit.edges_directed(node_graph_index, petgraph::Direction::Incoming).next());
        for in_edge in self
            .circuit
            .circuit
            .edges_directed(node_idx, petgraph::Direction::Incoming)
        {
            //let edge: () = in_edge;
            let mut edge_time = in_edge.weight().discrete_weight;
            //if self.circuit.graph_index_to_node[&node_idx] == "decode__169__ZN"{
            //    println!("Edge from {:?} to {:?} delay {:?}", self.circuit.graph_index_to_node[&in_edge.source()], self.circuit.graph_index_to_node[&in_edge.target()], edge_time);
            //}
            //println!("Delayed edge goes from {:?} to {:?}", delayed_edge.0, delayed_edge.1);
            if delayed_edge.is_some(){
                if in_edge.source() == delayed_edge.unwrap().0 && in_edge.target() == delayed_edge.unwrap().1 {
                    edge_time += delay.unwrap();
                    //println!("Adding a delay  of {:?} new time {:?}!", delay, edge_time);
                }
            }
            let in_node_idx = in_edge.source();
            //let in_node: String = self.circuit.graph_index_to_node[&in_node].to_string();
            //let in_node_idx = if (self.gate_string_to_idx.contains_key(&in_node)) {
            //    self.gate_string_to_idx[&in_node]
            //} else {
            //    self.flop_string_to_idx[&in_node]
            //};
            //println!("Calling recursive val with in_edge {:?} edge_time {:?} node {:?} out_node {:?}", in_edge, edge_time, self.circuit.graph_index_to_node[&in_node_idx], self.circuit.graph_index_to_node[&node_idx]);
            let val = self.get_recursive_val(
                step - edge_time,
                in_node_idx,
                delay,
                delayed_edge,
                recursive_val_map,
            );
            input_values.push(val);
            out_val = elem.can_short_circuit(&input_values);
            if out_val.is_some() {
                break;
            }
        }

        if out_val.is_none() { // Could not short circuit
            out_val = Some(elem.evaluate_logic(&input_values));
        }
        //if self.circuit.graph_index_to_node[&node_idx] == "decode__169__ZN"{
        //    println!("Out val {:?} input {:?}", out_val, &input_values);
        //}

        recursive_val_map[node_idx.index()].insert(step, out_val.unwrap()); //recursive_val_map.get_mut(&(node_idx)).unwrap().insert(step, out_val);
        out_val.unwrap()
    }

    pub fn compare_recursive_val(&self, node_idx: FlopMapIndexType, step: i64,
    delay1: i64, delay2: i64, delayed_edge: &(FlopMapIndexType, FlopMapIndexType), recursive_val_map1: &mut RecursiveValMapType, recursive_val_map2: &mut RecursiveValMapType){
        for in_edge  in self
        .circuit
        .circuit
        .edges_directed(node_idx, petgraph::Direction::Incoming){
            let edge_time = in_edge.weight().discrete_weight;
            
            if in_edge.source() == delayed_edge.0 && in_edge.target() == delayed_edge.1 {
                let edge_time1 = edge_time + delay1;
                let edge_time2 = edge_time + delay2;
                let val1 = self.get_recursive_val(
                    step - edge_time1,
                    in_edge.source(),
                    None,
                    None,
                    recursive_val_map1,
                );
                let val2 = self.get_recursive_val(
                    step - edge_time2,
                    in_edge.source(),
                    None,
                    None,
                    recursive_val_map2,
                );
                println!("Edge from {:?} to {:?} edge_time1 {:?} edge_time2 {:?} step {:?} val1 {:?} val2 {:?}", self.circuit.graph_index_to_node[&in_edge.source()], self.circuit.graph_index_to_node[&in_edge.target()], edge_time1, edge_time2, step, val1, val2);
                //println!("Done \n");
                return;
                
            }
            
            
            let in_node_idx = in_edge.source();
            let val1 = self.get_recursive_val(
                step - edge_time,
                in_node_idx,
                None,
                None,
                recursive_val_map1,
            );
            let val2 = self.get_recursive_val(
                step - edge_time,
                in_node_idx,
                None,
                None,
                recursive_val_map2,
            );
            if (val1 != val2){
                println!("Edge from {:?} to {:?} delay {:?} step {:?} val1 {:?} val2 {:?}", self.circuit.graph_index_to_node[&in_edge.source()], self.circuit.graph_index_to_node[&in_edge.target()], edge_time, step, val1, val2);
                //return;
            }
            //recursive_list.push((self.circuit.graph_index_to_node[&in_node_idx].to_string(), val, step - edge_time));
            self.compare_recursive_val(in_node_idx, step-edge_time, delay1, delay2, delayed_edge, recursive_val_map1, recursive_val_map2);
            //recursive_list.append(&mut recursive_list_pred);
        }
    }

    pub fn print_predecessor(&self, node_idx: FlopMapIndexType, step: i64,    delay: Option<i64>,
        delayed_edge: Option<&(FlopMapIndexType, FlopMapIndexType)>, recursive_val_map: &mut RecursiveValMapType) -> Vec<(String, bool, i64)>{ //HashMap<FlopMapIndexType, HashMap<i64, FlopValueType>>) -> Vec<(String, bool, i64)>{
        let mut recursive_list: Vec<(String, bool, i64)> = Vec::new();
        for in_edge  in self
        .circuit
        .circuit
        .edges_directed(node_idx, petgraph::Direction::Incoming){
            let mut edge_time = in_edge.weight().discrete_weight;
            if delayed_edge.is_some(){
                if in_edge.source() == delayed_edge.unwrap().0 && in_edge.target() == delayed_edge.unwrap().1 {
                //panic!("Adding a delay!");
                    edge_time += delay.unwrap();
                }
            }
            println!("Edge from {:?} to {:?} delay {:?} step {:?}", self.circuit.graph_index_to_node[&in_edge.source()], self.circuit.graph_index_to_node[&in_edge.target()], edge_time, step);
            let in_node_idx = in_edge.source();
            let val = self.get_recursive_val(
                step - edge_time,
                in_node_idx,
                None,
                None,
                recursive_val_map,
            );
            recursive_list.push((self.circuit.graph_index_to_node[&in_node_idx].to_string(), val, step - edge_time));
            let mut recursive_list_pred = self.print_predecessor(in_node_idx, step-edge_time, delay, delayed_edge, recursive_val_map);
            recursive_list.append(&mut recursive_list_pred);
        }
        recursive_list
    }
}

//pub fn
