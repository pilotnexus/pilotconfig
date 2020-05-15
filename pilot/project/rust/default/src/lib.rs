#![no_std]

extern crate pilot_types;
extern crate pilot_macro;

mod pilot;
mod variables;
use pilot::*;
use variables::*;
use pilot_macro::*;
use core::panic::PanicInfo;
use pilot_types::var::*;

include!("pilot/bindings.rs");
var_communication!();

/// Initialization, executed once at startup
fn init(_vars: &PlcVars) {
  println!("Hello form Rust!");
}

/// Program Loop
fn run(_vars: &PlcVars, _us: u64) {
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}