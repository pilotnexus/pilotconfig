#![allow(unused_imports)]
#![cfg_attr(not(test), no_std)]
extern crate pilot_sys;
use pilot_sys::async_util::wait_or;
use pilot_sys::loop_async;
use pilot_sys::time::{wait_next_cycle, wait };
use pilot_sys::var::{Var, VarChange, VarProps, NumVar };
mod pilot;
use pilot::variables::PlcVars;
use pilot_sys::futures::join;
use pilot_sys::*;
use core::time::Duration;

pub async fn main_task(_v: &PlcVars) {      
    //place your PLC init code here 
    loop_async! {{
        //place your application logic here
    }}
}
