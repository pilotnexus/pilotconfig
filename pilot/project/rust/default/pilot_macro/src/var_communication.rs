use crate::{generate_vars, BINDINGS, HASHMAP, ROOT};
use proc_macro2::{Span, TokenStream};
use quote::quote;
use std::{collections::HashMap, env, fs::OpenOptions, path::Path};
use syn::{Ident, Result};

pub fn expand(input: &Option<Ident>) -> Result<TokenStream> {
    let mut varnr = 0;
    let map: &HashMap<String, Vec<(String, String, Option<String>)>> = &*HASHMAP.lock().unwrap();
    let root = (ROOT.lock().unwrap())
        .clone()
        .expect("No root element defined");
    let root_ident = Ident::new(&root, Span::call_site());

    let (static_varname, static_vardeclaration): (Ident, TokenStream) = match input {
        None => (
            Ident::new("VARS", Span::call_site()),
            quote!(static mut VARS: PlcVars = <#root_ident>::new();),
        ),
        Some(ident) => (ident.clone(), quote!()),
    };

    let out_dir = match env::var("PILOT_OUT_DIR") {
    Ok(dir) => dir,
    Err(err) => panic!("Error getting working directory for variable output (environement variable PILOT_OUT_DIR) {}", err) 
  };

    //open variable file
    let dest_path = Path::new(&out_dir).join("VARIABLES.csv");
    let mut f = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(&dest_path)
        .unwrap();

    let varlist = generate_vars(&mut varnr, String::new(), root.clone(), map, &mut f);

    //eprintln!("{:?}", varlist);
    let mut plc_var_matches = Vec::new();
    for (nr, name) in varlist {
        let match_arm = quote! {
            #nr => { Some(&mut #static_varname.#name) }
        };
        plc_var_matches.push(match_arm);
    }

    let bindings = &*(BINDINGS.lock().unwrap());
    let mut plc_read_from_mem = Vec::new();
    let mut plc_write_to_mem = Vec::new();

    for (read, write, fqn, target) in bindings {
        let parts = target.split(":").collect::<Vec<&str>>();
        eprintln!("{:?}", parts);

        let part = Ident::new(parts[0], Span::call_site());
        let fqn = fqn.split('.').map(|s| Ident::new(s, Span::call_site()));
        let fqn = quote!(#(#fqn).*);

        if *read {
            let part_1 = parts[1].parse::<i32>().unwrap();

            plc_read_from_mem.push(match parts.len() {
                1 => quote!(VARS.#fqn.set(plc_mem.#part);),
                2 => quote!(VARS.#fqn.set((plc_mem.#part & (1 << #part_1)) > 0);),
                _ => panic!("Cannot process more than one bit adress operator (:)"),
            });
        }

        if *write {
            let part_1 = parts[1].parse::<u16>().unwrap();
            let part_1_mask = syn::Index::from(1 << part_1 as u16);
            let part_1_mask_inverse = syn::Index::from(!(1 << part_1) as u16 as usize);

            plc_write_to_mem.push(match parts.len() {
                1 => quote!(plc_mem.#part = VARS.#fqn.get();),
                2 => quote!(match VARS.#fqn.get() {
                    true => { plc_mem.#part |= #part_1_mask; },
                    false => { plc_mem.#part &= #part_1_mask_inverse; },
                }),
                _ => panic!("Cannot process more than one bit adress operator (:)"),
            });
        }

        //VARS.children.var0_2.set((plc_mem.m3[0] & 0x1) > 0);
    }

    Ok(quote! {
        #static_vardeclaration

        #[no_mangle]
        unsafe fn plc_init() {
            init(&#static_varname);
        }

        #[no_mangle]
        unsafe fn plc_run(_cycles: u64) {
            run(&mut #static_varname, _cycles);
        }

        #[no_mangle]
        unsafe fn plc_varnumber_to_variable(number: u16) -> Option<&'static mut MemVar>
        {
            match number {
                #(#plc_var_matches)*
                _ => {
                    return None;
                }
            }
        }

        #[no_mangle]
        unsafe fn plc_mem_to_var() {
            let plc_mem: &mut pilot::bindings::plc_dev_t = _get_plc_mem_devices_struct();
            #(#plc_read_from_mem)*
        }

        #[no_mangle]
        unsafe fn plc_var_to_mem() {
            let plc_mem: &mut pilot::bindings::plc_dev_t = _get_plc_mem_devices_struct();
            #(#plc_write_to_mem)*
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
    })
}
