#![macro_use]
extern crate pilot_macro;
extern crate pilot_types;

use pilot_macro::*;

#[allow(unused_imports)]
use pilot_types::var::*;

#[derive(Var)]
#[root]
pub struct PlcVars {
  /* Example usage for a variable (assuming 16 Analog IO Module in module slot 1) */
  //#[bind(|read| => m1.aio0)]
  //pub aio0: Var<u16>,

  /* Example usage for a boolean variable (assuming 16 Digital IO Module in module slot 4) */
  //pub io0: Var<bool>,
  //#[bind(|read| => m4:0)]
}