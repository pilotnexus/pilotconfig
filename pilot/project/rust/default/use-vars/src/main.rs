//! A minimal executable that preserves the `PLC_VARIABLES` variable from the staticlib in the
//! ELF executable. This makes it much easier to read out the value of this variable because
//! the linker resolves relocations for us this way.

#![no_std]
#![no_main]

use core::{panic::PanicInfo, ptr};

extern "C" {
    // TODO: use &[u8] instead of &str in VariableInfo to make it FFI safe?
    #[allow(improper_ctypes)]
    static PLC_VARIABLES: VariableInfo;
}

#[no_mangle]
fn _start() {
    // do a volatile read of the static to ensure that the compiler and linker
    // keep it
    unsafe { ptr::read_volatile(&PLC_VARIABLES) };
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}

/// This must be kept in sync with the VariableInfo struct specified in src/pilot/bindings.rs.
#[derive(Debug)]
#[repr(C)]
pub struct VariableInfo {
    pub name: &'static str,
    pub fields: Option<&'static [VariableInfo]>, // for compound types
    pub number: u16,                             // only valid when fields is None
}
