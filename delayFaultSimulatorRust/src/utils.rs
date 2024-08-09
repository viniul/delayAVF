use std::collections::HashMap;
use std::fs;
use std::iter::Iterator;
use serde::Deserialize;

/*
pub fn pairwise<'a, I>(iterable:&'a I, cyclic: bool) -> Box<dyn Iterator<Item = (I::Item, I::Item)>>
where
    I: Iterator + Clone,
{
    let mut a = iterable.clone();
    let mut b= iterable;
    let first = b.next();

    if cyclic {
        Box::new(a.zip(b.chain(first.into_iter())))
    } else {
        Box::new(a.zip(*b))
    }
}
 */



pub fn process_flop_name(x: &str) -> String {
    let mut result = x.replace("dff_", "").replace("Q_out", "Q").replace("QN_out", "QN").replace("\\", "").replace("__in", "_");
    result.shrink_to_fit(); // Optional: Reduce the capacity to match the length
    result
}

pub fn pairwise<I>(iterable: &mut I) -> Vec<(I::Item, I::Item)>
where
    I: Iterator + Clone,
    <I as Iterator>::Item: Clone,
{
    let mut ret_vec: Vec<(I::Item, I::Item)> = Vec::new();
    let a = iterable.clone();
    let b = iterable;
    let _ = b.next();
    //let mut e2 = b.next().unwrap();
    for e1 in a {
        let e2 = match b.next() {
            Some(e) => e,
            None => continue,
        };
        ret_vec.push((e1.clone(), e2.clone()));

        //for e2 in b {
        //    ret_vec.push((e1,e2));
        //}
    }
    ret_vec
}

#[derive(Debug, Deserialize)]
struct _SerializedFlopValue {
    _value: i64,
    _index: i64,
    _cycle: i64,
}

#[derive(Debug, Deserialize)]
struct SerializedVcdTrace {
    flop_values: HashMap<i64, HashMap<String, i64>>, //flop_values: Vec<SerializedFlopValue>,
                                                     //idx_to_flop_name: HashMap<i64, String>
                                                     inject_into_cycles: Vec<i64>,

}

pub fn parse_trace(flop_values_path: String) -> (HashMap<i64, HashMap<String, i64>>,Vec<i64>) {
    let file = fs::File::open(flop_values_path).expect("file should open read only");
    let out: SerializedVcdTrace = serde_json::from_reader(file).unwrap();
    (out.flop_values, out.inject_into_cycles)
    //let mut flop_values_map: HashMap<i64, (String, i64)> = HashMap::new();
    //for flop_value in out.flop_values.iter() {
    //    flop_values_map.insert((out.idx_to_flop_name[&flop_value.index].to_string(), flop_value.cycle), flop_value.value );
    //}
    //flop_values_map
}

pub fn read_config(config_path: &String) -> serde_json::Value {
    let file = fs::File::open(config_path).expect("file should open read only");
    let config_out: serde_json::Value = serde_json::from_reader(file).unwrap();
    config_out
}

pub fn read_json_file(json_path: &String) -> serde_json::Value {
    let file = fs::File::open(json_path).expect("file should open read only");
    let config_out: serde_json::Value = serde_json::from_reader(file).unwrap();
    config_out
}