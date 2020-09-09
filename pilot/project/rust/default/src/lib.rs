#![no_std]

extern crate pilot_macro;
extern crate pilot_types;

pub use pilot_macro::*;

mod pilot;
mod variables;
use core::panic::PanicInfo;
use pilot::*;
use pilot_types::var::*;
use variables::*;

#[root_var]
static mut TEST: PlcVars = <PlcVars>::new();

include!("pilot/bindings.rs");
//var_communication!();

/// Initialization, executed once at startup
fn init(_vars: &PlcVars) {
    println!("Hello form Rust!");
}

/// Program Loop
fn run(_vars: &mut PlcVars, _us: u64) {
    //timer demo
    static mut TIMER_START: u64 = 18_446_744_073_709_551_615u64;

    on_posedge!(_vars.inputs.io0, _vars.start => {
      println!("Started");
      _vars.start.set(false);
      unsafe {
        TIMER_START = _us;
      }
    });

    let elapsed = unsafe { _us - TIMER_START };
    if elapsed < 8_000_000 {
        _vars.demo_o1.set(true);
        match elapsed {
            d if d < 1_000_000 => _vars.outputs.io0.set(true),
            d if d < 2_000_000 => _vars.outputs.io1.set(true),
            d if d < 3_000_000 => _vars.outputs.io2.set(true),
            d if d < 4_000_000 => _vars.outputs.io3.set(true),
            d if d < 5_000_000 => _vars.outputs.io4.set(true),
            d if d < 6_000_000 => _vars.outputs.io5.set(true),
            d if d < 7_000_000 => _vars.outputs.io6.set(true),
            d if d < 8_000_000 => _vars.outputs.io7.set(true),
            _ => (),
        }
    } else {
        _vars.demo_o1.set(false);
        _vars.outputs.io0.set(false);
        _vars.outputs.io1.set(false);
        _vars.outputs.io2.set(false);
        _vars.outputs.io3.set(false);
        _vars.outputs.io4.set(false);
        _vars.outputs.io5.set(false);
        _vars.outputs.io6.set(false);
        _vars.outputs.io7.set(false);
    }
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}
