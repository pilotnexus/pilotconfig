extern crate proc_macro;
extern crate proc_macro2;
extern crate syn;

#[macro_use]
extern crate lazy_static;

use std::collections::HashMap;
use std::env;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::Path;
use std::sync::Mutex;

use itertools::Itertools;
use regex::Regex;

use proc_macro::*;
use syn::{DataStruct, DeriveInput};


extern "C" { 
  pub fn _putchar(c: u8);
}

#[allow(unused_macros)]
macro_rules! print {
  ($f:expr) => (
    unsafe {
      for c in $f.chars() { 
        _putchar(c as u8);
      }
    }
  )
}

#[allow(unused_macros)]
macro_rules! println {
  ($f:expr) => (
    print!($f);
    unsafe {
      _putchar(10);
      _putchar(13);
    }
  )
}

lazy_static! {
    static ref HASHMAP: Mutex<HashMap<String, Vec<(String, String, Option<String>)>>> = {
        let m = HashMap::new();
        Mutex::new(m)
    };

    static ref VEC: Mutex<Vec<(u32, String)>> = {
        let m = Vec::new();
        Mutex::new(m)
    };

    static ref BINDINGS: Mutex<Vec<(bool, bool, String, String)>> = {
        let m = Vec::new();
        Mutex::new(m)
    };

    static ref ROOT: Mutex<Option<String>> = Mutex::new(None);

    static ref IECVARS: HashMap<&'static str, &'static str> = {
      let mut vars = HashMap::new();
      vars.insert("AtomicU32","UDINT");
      vars.insert("AtomicI32","DINT");
      vars.insert("AtomicU16","UINT");
      vars.insert("AtomicI16","INT");
      vars.insert("AtomicU8","USINT");
      vars.insert("AtomicI8","SINT");
      vars.insert("AtomicBool","BOOL");
      vars.insert("u32","UDINT");
      vars.insert("i32","DINT");
      vars.insert("u16","UINT");
      vars.insert("i16","INT");
      vars.insert("u8","USINT");
      vars.insert("i8","SINT");
      vars.insert("bool","BOOL");
      vars
    };
}

fn generate_vars(varnr: &mut u32, qualifier: String, structname: String, map: &HashMap<String, Vec<(String, String, Option<String>)>>, f: &mut std::fs::File) {
  //eprintln!("trying {}", &structname);
  for (name, ty, vartype) in map.get(&structname).unwrap_or_else(|| panic!("element {} not found", structname)) {
    if ty == "Var" {
      let mut varlist = VEC.lock().unwrap();
      let varname = match qualifier.as_str() { "" => name.clone(), _ => format!("{}.{}", qualifier, name)};
      eprintln!("{}, {:?}, {:?}", varname, vartype, IECVARS.get(vartype.clone().unwrap().as_str()));
      writeln!(f, "{0};VAR;CONFIG.RESOURCE1.{1};CONFIG.RESOURCE1.{1};{2};", varnr, varname.clone(), IECVARS.get(vartype.clone().unwrap().as_str()).unwrap()).expect("Could not write variable file");
      varlist.push( (*varnr, varname.clone()) );
      *varnr += 1;
    }
    else {
      let child_qualifier = match qualifier.as_str() {
        "" => name.clone(),
        _ => format!("{}.{}", qualifier, name)
      }; 

      generate_vars(varnr, child_qualifier, ty.clone(), map, f);
    }
  }
}

#[doc="Defines communication structures, define after var structs"]
#[proc_macro]
pub fn var_communication(item: TokenStream) -> TokenStream {
  let mut varnr = 0;
  let map: &HashMap<String, Vec<(String, String, Option<String>)>> = &*HASHMAP.lock().unwrap();
  let root = (ROOT.lock().unwrap())
    .clone()
    .expect("No root element defined");

  let (static_varname, static_vardeclaration): (String, String) = match item.to_string().trim() {
    "" => (String::from("VARS"), format!("static mut VARS: PlcVars = {}::new();", root)),
    n => (String::from(n), String::new()),
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

  generate_vars(&mut varnr, String::new(), root.clone(), map, &mut f);

  let varlist: &Vec<(u32, String)> = &*(VEC.lock().unwrap());
  //eprintln!("{:?}", varlist);
  let mut plc_var_matches = String::new(); 
  for (nr, name) in varlist {
    plc_var_matches += &String::from(format!("{nr} => {{ Some(&mut ({static_varname}.{name})) }},\n        ", nr = nr, static_varname = static_varname, name = name));
  }
 
  //
  let bindings = &*(BINDINGS.lock().unwrap());
  let mut plc_read_from_mem = String::new();
  let mut plc_write_to_mem = String::new();

  for (read, write, fqn, target) in bindings {
    let parts = target.split(":").collect::<Vec<&str>>();
    eprintln!("{:?}", parts);
    if *read {
      plc_read_from_mem += &match parts.len() {
        1 => format!("VARS.{}.set(plc_mem.{});\n", fqn, parts[0]),
        2 => format!("VARS.{}.set((plc_mem.{} & 0x{:X}) > 0);\n", fqn, parts[0], 1 << parts[1].parse::<i32>().unwrap()),
        _ => panic!("Cannot process more than one bit adress operator (:)")
      };
    }

    if *write {
      plc_write_to_mem += &match parts.len() {
        1 => format!("plc_mem.{} = VARS.{}.get();\n", parts[0], fqn),
        2 => format!("match VARS.{0}.get() {{ true => {{ plc_mem.{1} |= 0x{2:X}; }}, false => {{ plc_mem.{1} &= 0x{3:X}; }} }};\n", fqn, parts[0], 1 << parts[1].parse::<u16>().unwrap() as u16, !(1 << parts[1].parse::<u16>().unwrap()) as u16),
        _ => panic!("Cannot process more than one bit adress operator (:)")
      };
    }

    //VARS.children.var0_2.set((plc_mem.m3[0] & 0x1) > 0);
  }

  eprintln!("plc_mem_to_var():\n{}", plc_read_from_mem);
  eprintln!("plc_var_to_mem():\n{}", plc_write_to_mem);

  let out = format!(r#"
  {static_vardeclaration}

  #[no_mangle]
  unsafe fn plc_init() {{
    init(&{static_varname});
  }}

  #[no_mangle]
  unsafe fn plc_run(_cycles: u64) {{
    run(&{static_varname}, _cycles);
  }}

  #[no_mangle]
  unsafe fn plc_varnumber_to_variable(number: u16) -> Option<&'static mut MemVar> 
  {{
    match number {{
      {vars}
      _ => {{
        return None;
      }}
    }}
  }}

  #[no_mangle]
  unsafe fn plc_mem_to_var() {{
    let plc_mem: &mut pilot::bindings::plc_dev_t = _get_plc_mem_devices_struct();
    {read}
  }}

  #[no_mangle]
  unsafe fn plc_var_to_mem() {{
    let plc_mem: &mut pilot::bindings::plc_dev_t = _get_plc_mem_devices_struct();
    {write}
  }}

  #[no_mangle]
  unsafe fn plc_read_from_variable(number: u16, buffer: *mut u8, _size: i32) -> i32
  {{
    match plc_varnumber_to_variable(number) {{
      Some(v) => {{ v.to_buffer(buffer); v.len() }},
      None => 0
    }} 
  }}

  #[no_mangle]
  unsafe fn plc_write_to_variable(number: u16, buffer: *mut u8, _size: i32) -> i32
  {{
    match plc_varnumber_to_variable(number) {{
      Some(v) => {{ (*v).from_buffer(buffer); v.len() }},
      None => 0
    }}
  }}

  #[no_mangle]
  unsafe fn plc_find_next_updated_variable() -> i32
  {{
    return -1;
  }}

  #[no_mangle]
  unsafe fn plc_port_config(_slot: u8, _port: u8, _baud: u16)
  {{
  }}

  #[no_mangle]
  unsafe fn plc_configure_read_variables(_variables: *mut u8, _count: i32) -> i32
  {{
    return 0;
  }}

  #[no_mangle]
  unsafe fn plc_configure_write_variables(_variables: *mut u8, _count: i32) -> i32
  {{
    return 0;
  }}

  #[no_mangle]
  unsafe fn plc_read_variables(_buffer: *mut u8) -> i32
  {{
    return 0;
  }}

  #[no_mangle]
  unsafe fn plc_write_variables(_buffer: *mut u8, _count: i32)
  {{
  }}
"#, static_varname = static_varname, static_vardeclaration = static_vardeclaration, vars = plc_var_matches, read = plc_read_from_mem, write = plc_write_to_mem);

  //eprintln!("{}", out);

  out.parse().unwrap()
}

fn extract_type_from_var(ty: &syn::Type) -> Option<&syn::Type> {
    use syn::punctuated::Pair;
    use syn::token::Colon2;
    use syn::{GenericArgument, Path, PathArguments, PathSegment};

    fn extract_type_path(ty: &syn::Type) -> Option<&Path> {
        match *ty {
            syn::Type::Path(ref typepath) if typepath.qself.is_none() => Some(&typepath.path),
            _ => None,
        }
    }

    // TODO store (with lazy static) the vec of string
    // TODO maybe optimization, reverse the order of segments
    fn extract_option_segment(path: &Path) -> Option<Pair<&PathSegment, &Colon2>> {
        let idents_of_path = path
            .segments
            .iter()
            .into_iter()
            .fold(String::new(), |mut acc, v| {
                acc.push_str(&v.ident.to_string());
                acc.push('|');
                acc
            });
        vec!["Var|"]
            .into_iter()
            .find(|s| &idents_of_path == *s)
            .and_then(|_| path.segments.last())
    }

    extract_type_path(ty)
        .and_then(|path| extract_option_segment(path))
        .and_then(|pair_path_segment| {
            let type_params = &pair_path_segment.into_value().arguments;
            // It should have only on angle-bracketed param ("<String>"):
            match *type_params {
                PathArguments::AngleBracketed(ref params) => params.args.first(),
                _ => None,
            }
        })
        .and_then(|generic_arg| match *generic_arg.into_value() {
            GenericArgument::Type(ref ty) => Some(ty),
            _ => None,
        })
}

fn parse_path(path: &syn::Path) -> String {
  for p in path.segments.iter() {
    return p.ident.to_string();
  }
  panic!("No path found");
}

/// Derives a struct for PLC Var usage (Var<_> values)
#[proc_macro_derive(Var, attributes(root, bind))]
pub fn var_struct(item: TokenStream) -> TokenStream {
  const ROOT_ATTR_NAME: &'static str = "root";
  const BIND_ATTR_NAME: &'static str = "bind";
  let ast: DeriveInput = syn::parse(item.clone()).expect("Couldn't parse for var_struct");
  let mut map = HASHMAP.lock().unwrap();
  let mut m: Vec<(String, String, Option<String>)> = Vec::new();
  let name = ast.ident.to_string();
  let mut initializers = Vec::new();

  // Is it a struct?
  if let syn::Data::Struct(DataStruct { ref fields, .. }) = ast.data {
    // Looks for state_change attriute (our attribute)
    if let Some(ref _a) = ast
      .attrs
      .iter()
      .find(|a| parse_path(&a.path) == ROOT_ATTR_NAME)
    {
      //eprintln!("Found root on {}", name);
      *(ROOT.lock().unwrap()) = Some(name.clone());
    }
    for f in fields.iter() {
      let vartype = match extract_type_from_var(&f.ty) {
        Some(p) => match p {
          syn::Type::Path(s) => Some(parse_path(&s.path)),
          _ => panic!("type needs to be path"),
        },
        None => None
      };
      //eprintln!("type is {:?}", vartype);

      //look for bind attributes
      if let Some(b) = f.attrs.iter().find(|a| parse_path(&a.path) == BIND_ATTR_NAME) {
        let mut bindings = BINDINGS.lock().unwrap(); 
        let tts_str = b.tts.to_string().replace(&['(', ')', ' '][..], "");
        for v in tts_str.split(",")
            .map(|item| item.split("=>").next_tuple::<(&str, &str)>().expect("Cannot extract tuple, are you missing the => operator?"))
            {
              let re = Regex::new(r"\|(?P<rw>.*?)\|(?P<fqn>.*)").unwrap();
              let result = re.captures(v.0).unwrap();
              let fqn = format!("{}{}{}", &result["fqn"], if let 0 = &result["fqn"].len() { "" } else { "." }, f.ident.clone().unwrap().to_string());
              eprintln!("rw: {} fqn: {}", &result["rw"], fqn);
              let read: bool = &result["rw"] == "read";
              let write: bool = &result["rw"] == "write";
              bindings.push((read, write, fqn, String::from(v.1))); //push to vec, create owned string copies
            }
        eprintln!("{:?}", bindings);
      }

      let ty = match &f.ty {
        syn::Type::Path(s) => parse_path(&s.path),
        _ => panic!("Can only implement path in struct"),
      };

      let constructortype = match &vartype {
        Some(t) => format!("{}::<{}>", ty.clone(), t.clone()),
        None => ty.clone()
      };

      initializers.push(format!(
        "{}: {}::new()",
        f.ident.clone().unwrap().to_string(),
        constructortype,
      ));
      m.push( (f.ident.clone().unwrap().to_string(), ty.clone(), vartype) );
    }
  } else {
    // Nope. This is an Enum. We cannot handle these!
    panic!("#[var_struct] is only defined for structs, not for enums!");
  }
  map.insert(name.clone(), m);

  let x = format!(
    r#"
    impl {structname} {{
      pub const fn new() -> {structname} {{
        {structname} {{ {initializer }}}
      }}
    }}
    "#,
    structname = name,
    initializer = initializers.join(", ")
  );

   //eprintln!("{}", x);

  x.parse().expect("Generated invalid tokens")
}

#[proc_macro_attribute]
pub fn log_entry_and_exit(args: TokenStream, input: TokenStream) -> TokenStream {
  let x = format!(
    r#"
        fn dummy() {{
            println!("entering");
            println!("args tokens: {{}}", {args});
            println!("input tokens: {{}}", {input});
            println!("exiting");
        }}
    "#,
    args = args.into_iter().count(),
    input = input.into_iter().count(),
  );

  x.parse().expect("Generated invalid tokens")
}
