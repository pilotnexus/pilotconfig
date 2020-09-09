use lazy_static::lazy_static;

use proc_macro::TokenStream;
use proc_macro2::Span;
use quote::{quote, ToTokens};
use std::collections::HashMap;
use std::io::Write;
use std::sync::Mutex;
use syn::{parse_macro_input, DeriveInput, Ident, ItemStatic};

mod pilot_bindings;
mod root_var;
mod var_communication;
mod var_derive;

extern "C" {
    pub fn _putchar(c: u8);
}

#[allow(unused_macros)]
macro_rules! print {
    ($f:expr) => {
        unsafe {
            for c in $f.chars() {
                _putchar(c as u8);
            }
        }
    };
}

#[allow(unused_macros)]
macro_rules! println {
    ($f:expr) => {
        print!($f);
        unsafe {
            _putchar(10);
            _putchar(13);
        }
    };
}

lazy_static! {
    static ref HASHMAP: Mutex<HashMap<String, Vec<(String, String, Option<String>)>>> = {
        let m = HashMap::new();
        Mutex::new(m)
    };
    static ref BINDINGS: Mutex<Vec<(bool, bool, String, String)>> = {
        let m = Vec::new();
        Mutex::new(m)
    };
    static ref ROOT: Mutex<Option<String>> = Mutex::new(None);
    static ref IECVARS: HashMap<&'static str, &'static str> = {
        let mut vars = HashMap::new();
        vars.insert("AtomicU32", "UDINT");
        vars.insert("AtomicI32", "DINT");
        vars.insert("AtomicU16", "UINT");
        vars.insert("AtomicI16", "INT");
        vars.insert("AtomicU8", "USINT");
        vars.insert("AtomicI8", "SINT");
        vars.insert("AtomicBool", "BOOL");
        vars.insert("u32", "UDINT");
        vars.insert("i32", "DINT");
        vars.insert("u16", "UINT");
        vars.insert("i16", "INT");
        vars.insert("u8", "USINT");
        vars.insert("i8", "SINT");
        vars.insert("bool", "BOOL");
        vars
    };
}

fn generate_vars(
    varnr: &mut u16,
    qualifier: String,
    structname: String,
    map: &HashMap<String, Vec<(String, String, Option<String>)>>,
    f: &mut std::fs::File,
) -> Vec<(u16, proc_macro2::TokenStream)> {
    let mut varlist = Vec::new();
    //eprintln!("trying {}", &structname);
    for (name, ty, vartype) in map
        .get(&structname)
        .unwrap_or_else(|| panic!("element {} not found", structname))
    {
        let name_ident = Ident::new(&name, Span::call_site());
        if ty == "Var" {
            let varname = match qualifier.as_str() {
                "" => quote!(#name_ident),
                _ => quote!(#qualifier.#name_ident),
            };
            eprintln!(
                "{}, {:?}, {:?}",
                varname,
                vartype,
                IECVARS.get(vartype.clone().unwrap().as_str())
            );
            writeln!(
                f,
                "{0};VAR;CONFIG.RESOURCE1.{1};CONFIG.RESOURCE1.{1};{2};",
                varnr,
                varname.clone(),
                IECVARS.get(vartype.clone().unwrap().as_str()).unwrap()
            )
            .expect("Could not write variable file");
            varlist.push((*varnr, varname.clone()));
            *varnr += 1;
        } else {
            let child_qualifier = match qualifier.as_str() {
                "" => name.clone(),
                _ => format!("{}.{}", qualifier, name),
            };

            generate_vars(varnr, child_qualifier, ty.clone(), map, f);
        }
    }
    varlist
}

#[doc = "Defines communication structures, define after var structs"]
#[proc_macro]
pub fn var_communication(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as Option<syn::Ident>);
    let tokens = var_communication::expand(&input)
        .unwrap_or_else(|err| err.to_compile_error())
        .into();
    eprintln!("TOKENS: {}", tokens);
    tokens
}

fn extract_type_from_var(ty: &syn::Type) -> Option<syn::Type> {
    use syn::{GenericArgument, Path, PathArguments};

    fn extract_type_path(ty: &syn::Type) -> Option<&Path> {
        match *ty {
            syn::Type::Path(ref typepath) if typepath.qself.is_none() => Some(&typepath.path),
            _ => None,
        }
    }

    // TODO store (with lazy static) the vec of string
    // TODO maybe optimization, reverse the order of segments
    let extract_option_segment = |path: &Path| {
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
            .and_then(|_| path.segments.last().map(|ty| ty.clone()))
    };

    extract_type_path(ty)
        .and_then(|path| extract_option_segment(path))
        .and_then(|pair_path_segment| {
            let type_params = &pair_path_segment.arguments;
            // It should have only on angle-bracketed param ("<String>"):
            match *type_params {
                PathArguments::AngleBracketed(ref params) => params.args.first().map(Clone::clone),
                _ => None,
            }
        })
        .and_then(|generic_arg| match generic_arg {
            GenericArgument::Type(ty) => Some(ty),
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
pub fn derive_var(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let map = &mut HASHMAP.lock().unwrap();
    var_derive::expand(&input, map)
        .unwrap_or_else(|err| err.to_compile_error())
        .into()
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

/// The `#[root]` attribute is used to mark a static variable as the root of the PLC variables.
///
/// This attribute makes all fields of type `Var` contained in the annotated static accessible
/// from the outside. It also activates the `bind_*` attributes on the fields (see the
/// `PilotBindings` derive macro).
///
/// The marked static must be a struct that implements or derives the `PilotBindings` trait. Only a
/// single static can be marked as root.
///
/// ## Example
///
/// ```
/// #[root_var]
/// static mut VARS: PlcVars = PlcVars::new();
///
/// // See docs for `PilotBindings` derive macro
/// #[derive(PilotBindings)]
/// pub struct PlcVars {
///     #[bind_read(m1.0)]
///     pub i8_0: Var<bool>,
/// }
/// ```
#[proc_macro_attribute]
pub fn root_var(attr: TokenStream, item: TokenStream) -> TokenStream {
    parse_macro_input!(attr as syn::parse::Nothing);
    let input = parse_macro_input!(item as ItemStatic);
    let generated = root_var::expand(&input).unwrap_or_else(|err| err.to_compile_error());

    eprintln!("ROOT_VAR TOKENS: {}", generated);

    let mut item = input.into_token_stream();
    item.extend(generated);
    item.into()
}

/// This derive macro generates an implementation of the `PilotBindings` trait using `bind_*`
/// attributes.
///
/// By deriving the `PilotBindings` trait, all fields of type `Var` are accessible from the outside.
/// Fields of that type can be also bind to a field of an input or output module through
/// `#[bind_read]` or `#[bind_write]` attributes. The following syntax variants exist:
///
/// - `#[bind_read(m3.5)]`: Reads from the annotated variable of type `Var<bool>` resolve to the
///   value of bit 5 of module `m3`.
/// - `#[bind_write(m2.7)]`: Writes to the variable of type `Var<bool>` set the value of bit 7
///   of `m2`.
///
/// Planned variants that are not yet supported:
/// - `#[bind_read(m3)]`: Reads from the annotated variable of type `Var<u8>` resolve to the
///   value of module `m3`.
/// - `#[bind_write(m3)]`: Writes to the annotated variable of type `Var<u8>` set the value of
///   module `m3`.
///
/// It is possible to annotate a field with both `#[bind_read]` and `#[bind_write]` attributes:
///
/// ```
/// #[derive(PilotBindings)]
/// pub struct IOModule {
///     #[bind_read(m1.0)]
///     #[bind_write(m2.0)]
///     pub io0: Var<bool>,
/// }
/// ```
///
/// ## Compound Types
///
/// Instead of specifying all fields in a single struct, it is possible to specify fields that
/// refer to other structs that also implement/derive the `PilotBindings` trait:
///
/// ```
/// #[derive(PilotBindings)]
/// pub struct PlcVars {
///     /* Example for hieracical var structure */
///     #[bind_read]
///     pub inputs: IOModule,
///     #[bind_write]
///     pub outputs: IOModule,
///
///     #[bind_read(m1.0)]
///     pub i8_0: Var<bool>,
/// }
/// ```
///
/// Fields that refer to other structs must be annotated with argument-less `#[bind_read]` and/or
/// `#[bind_write]` attributes. These attributes specify whether the `#[bind_read]`/`#[bind_write]`
/// attributes of the referenced struct should apply or not. For the above example, only the
/// `#[bind_read]` attributes of the `IOModule` struct apply for the `inputs` fields and only the
/// `#[bind_write]` attributes apply to the `outputs` field.
///
/// ## Ignoring Fields
///
/// The macro requires that all fields are either of type `Var` or are annotated with a `bind_*`
/// attribute. Other fields need to be explicitly ignored through a `#[bind_ignore]` attribute.
/// This requirement ensures that one can't accidentally forget to add a `#[bind_*]` attributes
/// on fields that refer other structs such as the `inputs` fields in the example above.
///
/// ## Limitations
///
/// Since macro expansion happens before type analysis, the detection of fields of type `Var`
/// uses simple string matching. That means that specifying the field type using a path does
/// not work currently (e.g. `struct Test { io0: pilot_types::var::Var<bool>, }`).
#[proc_macro_derive(PilotBindings, attributes(bind_read, bind_write, bind_ignore))]
pub fn derive_var_new(item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as DeriveInput);
    let tokens = pilot_bindings::expand(&input).unwrap_or_else(|err| err.to_compile_error());

    eprintln!("VAR_NEW TOKENS: {}", tokens);

    tokens.into()
}
