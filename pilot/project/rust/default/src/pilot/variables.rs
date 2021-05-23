#![macro_use]

use pilot_sys::var::{ Var, VarProps, PilotBindings };
use pilot_macro::*;
use crate::pilot::bindings::PilotAccess;

#[derive(ConstNew, PilotAccess, PilotBindings)]
pub struct PlcVars {
  //insert your plc variables here
  //they have to be of type Var<>
  //Usage:  
  //  examples:   IO16 `#[bind_read(m1, bit=1)]`  takes the second bit of the first module and binds it as read to the variable
  //  examples:  AIO16 `#[bind_read(m2.aio0)]' binds the first analog input of module 2 to the variable
  //  No binding:      `#[bind_ignore]`
  //  Value bindings:  e.g. `#[bind_read(m2)]`
  //  Nested Structs Syntax: `#[bind_nested(m3)]`
  //                         The referenced struct needs a `bind_type` attribute with the required sub-type e.g. `#[bind_type(crate::bindings::Motor)]`.
  //  Filter Functions: e.g. `#[bind_read(m3[0].position, filter(test_read_mask))]`. `test_read_mask` function has to have one argument and one return value.
  //                    It is also allowed to use filter functions with bit access e.g. als `#[bind_write(m3[1].position, bit=5, filter(test_write_bit_filter))]`. `test_write_bit_filter` takes the `Var` value as argument and returns 'bool', which is set into the selected bit.

  //#[bind_read(m2.io0)]

}


