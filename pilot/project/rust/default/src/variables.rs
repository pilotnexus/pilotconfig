#![macro_use]
extern crate pilot_macro;
extern crate pilot_types;

use pilot_macro::*;

#[allow(unused_imports)]
use pilot_types::var::*;

#[derive(PilotBindings)]
pub struct PlcVars {
     pub io16_0: Var<bool>  
}


