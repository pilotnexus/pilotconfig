use proc_macro2::TokenStream;
use quote::quote_spanned;
use syn::{spanned::Spanned, ItemStatic, Result};

pub fn expand(item: &ItemStatic) -> Result<TokenStream> {
    let static_varname = &item.ident;
    let static_ty = &item.ty;
    Ok(quote_spanned!(static_ty.span()=>
        #[no_mangle]
        static PLC_VARIABLES: crate::pilot::bindings::VariableInfo = crate::pilot::bindings::VariableInfo {
            name: core::stringify!(#static_varname),
            ty: "COMPOUND",
            fields: <#static_ty as crate::pilot::bindings::PilotAccess>::VARIABLES,
            field_number_offset: 0,
        };

        #[repr(packed(1))]
        struct VarMsgStruct {
          pub opt: u8,
          pub number: u16,
        }

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

        unsafe fn plc_varnumber_to_variable(number: u16) -> Option<&'static dyn MemVar> {
            crate::pilot::bindings::PilotAccess::plc_varnumber_to_variable(&#static_varname, number)
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
        unsafe fn plc_read_from_variable(num: u16, subvalue: u8, buffer: *mut u8, _size: i32) -> u8
        {
          match plc_varnumber_to_variable(num) {
                 Some(v) => {
                   v.to_buffer(buffer, subvalue)
                 },
                 None => 0
             }
        }

        #[no_mangle]
        unsafe fn plc_write_to_variable(number: u16, subvalue: u8, buffer: *const u8, _size: i32) -> u8
        {
            match plc_varnumber_to_variable(number) {
                Some(v) => (*v).from_buffer(buffer, subvalue),
                None => 0
            }
        }

        #[no_mangle]
        unsafe fn plc_read_config_from_variable(num: u16, config: u8) -> u8 
        {
          match plc_varnumber_to_variable(num) {
            Some(v) => {
              match config {
                1 => (*v).get_subscribed(),
                2 => (*v).get_forced(),
                _ => 0
              }
            }
            None => 0
          }
        }

        #[no_mangle]
        unsafe fn plc_write_config_to_variable(num: u16, config: u8, value: u8) -> u8 
        {
          match plc_varnumber_to_variable(num) {
            Some(v) => {
              match config {
                1 => {
                  (*v).set_subscribed(value);
                  1
                },
                2 => {
                  (*v).set_forced(value);
                  1
                },
                _ => 0
              }
            }
            None => 0
          }
        }


        #[no_mangle]
        unsafe fn plc_get_updated_variables(data: *mut u8, _size: u32) -> u32
        {
          static VAR_COUNT: u16 = <#static_ty as crate::pilot::bindings::PilotAccess>::FIELD_NUM;
          static mut CUR_VAR_INDEX: u16 = 0;
          static MAX_VARS_PER_MSG: u16 = 5;
          let mut vars_in_msg: u16 = 0;
          let mut ret: u32 = 0;
          let mut p: *mut u8 = data as *mut u8;
          let mut opt: Option<*mut u8> = None;

          //scan all variables one time m
          for _n in 0..VAR_COUNT {
            match plc_varnumber_to_variable(CUR_VAR_INDEX) {
              Some(v) => if v.get_subscribed() > 0 && v.is_dirty() { 
                v.clear_dirty();
                //set next var bit if there was a prev. var
                match opt {
                  Some(o) => (*o) = (*o) | 0x80,
                  None => ()
                }
                opt = Some(p);

                let mut t: *mut VarMsgStruct = p as *mut VarMsgStruct;
                (*t).number = CUR_VAR_INDEX;
                p = p.offset(3); //var header is 3 bytes
                let mut len = v.to_buffer(p, 2);
                if len > 8 {
                  len = 8; //Todo? cannot handle vars longer than 8, should never happen
                }
                p = p.offset(len as isize);
                (*t).opt = len;
                (*t).opt = (*t).opt | ((0x2 & 0x7) << 4); //subvalue 2

                vars_in_msg = vars_in_msg + 1;
                if vars_in_msg >= MAX_VARS_PER_MSG {
                  break;
                }
                ret = ret + 3 + len as u32;
              },
              None => ()
            };

            //increment
            CUR_VAR_INDEX = CUR_VAR_INDEX + 1;
            if CUR_VAR_INDEX >= VAR_COUNT {
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
