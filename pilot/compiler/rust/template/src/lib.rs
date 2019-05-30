#![no_std]
use core::panic::PanicInfo;

include!("bindings.rs");

#[no_mangle]
fn plc_init() {
  println!("Hello form Rust!!!");
}

#[no_mangle]
fn plc_run() {
}

#[no_mangle]
unsafe fn plc_configure_read_variables(_variables: *mut u8, _count: i32) -> i32
{
  return 0;
}

#[no_mangle]
unsafe fn plc_configure_write_variables(_variables: *mut u8, _count: i32) -> i32
{
  return 0;
}

#[no_mangle]
unsafe fn plc_read_variables(_buffer: *mut u8) -> i32
{
  return 0;
}

#[no_mangle]
unsafe fn plc_write_variables(_buffer: *mut u8, _count: i32)
{
}

#[no_mangle]
unsafe fn plc_read_from_variable(_number: u16, _buffer: *mut u8, _size: i32) -> i32
{
  return 0;
}

#[no_mangle]
unsafe fn plc_write_to_variable(_number: u16, _buffer: *mut u8, _size: i32) -> i32
{
  return 0;
}

#[no_mangle]
unsafe fn plc_find_next_updated_variable() -> i32
{
  return 0;
}

#[no_mangle]
unsafe fn plc_port_config(_slot: u8, _port: u8, _baud: u16)
{
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}