#![no_std]
#![allow(unused_imports)]
#![allow(dead_code)]

extern crate pilot_macro;
extern crate pilot_types;

pub use pilot_macro::*;

use async_util::raw_waker;
use core::{
    fmt::Write,
    panic::PanicInfo,
    pin::Pin,
    task::{Context, Waker},
};
use futures::future::{FusedFuture, FutureExt};
use macros::SerialWriter;
use main_task::main_task;
use pilot::*;
use pilot_macro::root_var;
use pilot_types::var::*;
use variables::PlcVars;

mod async_util;
mod main_task;
mod pilot;
mod time;
mod variables;


#[root_var]
pub static VARS: PlcVars = <PlcVars>::new();

include!("pilot/bindings.rs");

pub struct State<'a> {
    future: Pin<&'a mut dyn FusedFuture<Output = ()>>,
}


#[no_mangle]
unsafe fn plc_fw_version(_part: u8, buffer: *mut u8, buf_size: u32) -> i32
{
  static VERSION: &'static str = "v1.0"; //you can change this string to match your software version
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
fn init(main_loop: impl FnOnce(&mut State)) {
    println!("Hello form Rust!");

    let future = main_task().fuse();
    futures::pin_mut!(future);
    let mut state = State { future };
    // writeln!(SerialWriter, "State: {:#p}", &mut state).unwrap();

    main_loop(&mut state);
}

/// Program Loop
fn run(state: &mut State, us: u64) {
    time::set_system_time(us);

    let waker = unsafe { Waker::from_raw(raw_waker()) };
    let mut context = Context::from_waker(&waker);

    if state.future.as_mut().poll(&mut context).is_ready() {
        // println!("Future done");
    };
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}
