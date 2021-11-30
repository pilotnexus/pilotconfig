#![allow(unused_imports)]
#![cfg_attr(not(test), no_std)]
extern crate pilot_sys;

use pilot_sys::{async_util::wait_or};
use pilot_sys::var::{VarChange, VarProps, Var};
use pilot_sys::time::{wait_next_cycle, wait_us };
use pilot_sys::plc_loop;

mod pilot;

use pilot_sys::*;
use pilot_sys::futures::join;
use pilot::variables::PlcVars;

pub async fn main_task(_v: &PlcVars) {      
    //place your PLC init code here 
    plc_loop! {{
    //place your application logic here
    }}
}
