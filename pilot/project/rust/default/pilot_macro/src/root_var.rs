use proc_macro2::TokenStream;
use quote::quote;
use syn::{ItemStatic, Result};

pub fn expand(item: &ItemStatic) -> Result<TokenStream> {
    let static_varname = &item.ident;
    let static_ty = &item.ty;
    Ok(quote!(
        #[no_mangle]
        static PLC_VARIABLES: crate::pilot::bindings::VariableInfo = crate::pilot::bindings::VariableInfo {
            name: core::stringify!(#static_varname),
            ty: "COMPOUND",
            fields: <#static_ty as crate::pilot::bindings::PilotBindings>::VARIABLES,
            field_number_offset: 0,
            number: 0,
        };

        #[no_mangle]
        unsafe fn plc_init(main_loop: extern "C" fn(*mut u8)) {
            init(|state: &mut State| {
                let state_ptr: *mut State = state;
                main_loop(state_ptr.cast());
            });
        }

        #[no_mangle]
        unsafe fn plc_run(state: *mut u8, cycles: u64) {
            // ensure correct function signature
            let run_fn: fn (state: &mut State, u64) = run;
            run_fn(&mut *(state as *mut State), cycles);
        }

        unsafe fn plc_varnumber_to_variable(number: u16) -> Option<&'static MemVar> {
            crate::pilot::bindings::PilotBindings::plc_varnumber_to_variable(&#static_varname, number)
        }

        #[no_mangle]
        unsafe fn plc_mem_to_var() {
            let plc_mem: &pilot::bindings::plc_dev_t = _get_plc_mem_devices_struct();
            crate::pilot::bindings::PilotBindings::set_from_pilot_bindings(&#static_varname, plc_mem);
        }

        #[no_mangle]
        unsafe fn plc_var_to_mem() {
            let plc_mem: &mut pilot::bindings::plc_dev_t = _get_plc_mem_devices_struct();
            crate::pilot::bindings::PilotBindings::write_to_pilot_bindings(&#static_varname, plc_mem);
        }

        #[no_mangle]
        unsafe fn plc_read_from_variable(num: u16, subvalue: u8, buffer: *mut u8, _size: i32) -> i32
        {
            let number: u16 = num & 0xFFF;
            match plc_varnumber_to_variable(number) {
                Some(v) => {
                    let len: i32;
                    if num & 0x8000 > 0 {
                        v.set_subscribed(true);
                    }
                    if num & 0x4000 > 0 {
                        v.set_subscribed(false);
                    }
                    len = v.to_buffer(buffer, subvalue);
                    if subvalue == 1 && v.is_dirty() {
                        v.clear_dirty_or_update();
                    }
                    len
                },
                None => 0
            }
        }

        #[no_mangle]
        unsafe fn plc_write_to_variable(number: u16, subvalue: u8, buffer: *mut u8, _size: i32) -> i32
        {
            match plc_varnumber_to_variable(number) {
                Some(v) => (*v).from_buffer(buffer, subvalue),
                None => 0
            }
        }

        #[no_mangle]
        unsafe fn plc_find_next_updated_variable() -> i32
        {
            static VAR_COUNT: u16 = 20; // #varcount;
            static mut CUR_VAR_INDEX: u16 = 0;
            let mut ret: i32 = -1;

            for _n in 0..VAR_COUNT {
                let dirty = match plc_varnumber_to_variable(CUR_VAR_INDEX) {
                    Some(v) => if v.get_subscribed() { v.is_dirty() } else { false },
                    None => false
                };

                if dirty {{
                    ret = CUR_VAR_INDEX as i32;
                    break;
                }}

                //increment
                CUR_VAR_INDEX = CUR_VAR_INDEX + 1;
                if CUR_VAR_INDEX > (VAR_COUNT-1) {
                    CUR_VAR_INDEX = 0;
                }
            }
            ret
        }

        #[no_mangle]
        unsafe fn plc_port_config(_slot: u8, _port: u8, _baud: u16)
        {
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
    ))
}
