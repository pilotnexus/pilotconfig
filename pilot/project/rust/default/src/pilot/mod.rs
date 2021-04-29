#![allow(unused_imports)]
#![allow(dead_code)]

use core::{
    fmt::Write,
    panic::PanicInfo,
    pin::Pin,
    task::{Context, Waker},
};


use pilot_sys::time;
use pilot_sys::var::{ Var, MemVar, VariableInfo, PilotBindings };
use pilot_sys::futures::{ FutureExt, pin_mut };
use pilot_sys::async_util::{ State, raw_waker };
use pilot_macro::root_var;

pub mod variables;
pub mod bindings;

use crate::main_task;
use pilot_sys::var::*;
use variables::PlcVars;

#[root_var]
pub static VARS: PlcVars = <PlcVars>::new();

extern "C" {
    pub fn _get_plc_mem_devices_struct() -> &'static mut bindings::plc_dev_t;
}

macro_rules! crate_version {
    () => {
        env!("CARGO_PKG_VERSION")
    };
}

#[no_mangle]
unsafe fn plc_fw_version(_part: u8, buffer: *mut u8, buf_size: u32) -> i32
{
  static VERSION: &'static str = crate_version!();
  let mut size = 0;

  for (i,c) in VERSION.chars().enumerate() {
    if (i as u32) < buf_size-1 {
      let new_p = buffer.offset(i as isize);
      *new_p = c as u8;
      size = size + 1;
    }
  }
  //add string terminination
  *buffer.offset(size as isize) = 0;

  size+1
}

/// Initialization, executed once at startup
fn init(main_loop: impl FnOnce(&mut State<()>)) {

    let future = main_task(&VARS).fuse();
    pin_mut!(future);
    let mut state = State { future };

    main_loop(&mut state);
}

/// Program Loop
fn run(state: &mut State<()>, us: u64) {
    time::set_system_time(us);

    let waker = unsafe { Waker::from_raw(raw_waker()) };
    let mut context = Context::from_waker(&waker);

    if state.future.as_mut().poll(&mut context).is_ready() {
        // println!("Future done");
    };
}

#[cfg(target_arch = "arm")]
#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}
