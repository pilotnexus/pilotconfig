use proc_macro::TokenStream;
use quote::ToTokens;
use syn::{parse_macro_input, DeriveInput, ItemStatic};

mod const_new;
mod pilot_access;
mod pilot_bindings;
mod root_var;

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
/// static VARS: PlcVars = PlcVars::new();
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

    // eprintln!("ROOT_VAR TOKENS: {}", generated);

    let mut item = input.into_token_stream();
    item.extend(generated);
    item.into()
}

#[proc_macro_derive(PilotAccess)]
pub fn derive_pilot_access(item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as DeriveInput);
    let tokens = pilot_access::expand(&input).unwrap_or_else(|err| err.to_compile_error());

    // eprintln!("pilot_access TOKENS: {}", tokens);

    tokens.into()
}

/// This derive macro generates an implementation of the `PilotBindings` trait using `bind_*`
/// attributes.
///
/// By deriving the `PilotBindings` trait, all fields of type `Var` are accessible from the outside.
/// Fields of that type can be also bind to a field of an input or output module through
/// `#[bind_read]` or `#[bind_write]` attributes. The following syntax variants exist:
///
/// - `#[bind_read(m3, bit = 5)]`: Reads from the annotated variable of type `Var<bool>` resolve to the
///   value of bit 5 of module `m3`.
/// - `#[bind_write(m2, bit = 7)]`: Writes to the variable of type `Var<bool>` set the value of bit 7
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
///     #[bind_read(m1, bit = 0)]
///     #[bind_write(m2, bit = 0)]
///     pub io0: Var<bool>,
/// }
/// ```
///
/// It is also possible to bind to certain sub-fields of the generated module structs:
///
/// ```
/// #[derive(PilotBindings)]
/// pub struct IOModule {
///    // assuming that `m3` is an array of `Motor { position: u32, }` structs
///    #[bind_write(m3[0].position, bit = 15)]
///    pub demo_o1: Var<bool>,
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
///     #[bind_nested]
///     pub inputs: IOModule,
///     #[bind_nested]
///     pub outputs: IOModule,
///
///     #[bind_read(m1, bit = 0)]
///     pub i8_0: Var<bool>,
/// }
/// ```
///
/// Fields that refer to other structs must be annotated with an argument-less `#[bind_nested]`
/// attribute.
///
/// ## Ignoring Fields
///
/// The macro requires that all fields are either of type `Var` or are annotated with a `bind_*`
/// attribute. Other fields need to be explicitly ignored through a `#[bind_ignore]` attribute.
/// This requirement ensures that one can't accidentally forget to add a `#[bind_*]` attributes
/// on fields that refer other structs such as the `inputs` fields in the example above.
#[proc_macro_derive(
    PilotBindings,
    attributes(bind_read, bind_write, bind_ignore, bind_nested, bind_type)
)]
pub fn derive_pilot_bindings(item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as DeriveInput);
    let tokens = pilot_bindings::expand(&input).unwrap_or_else(|err| err.to_compile_error());

    // eprintln!("binding TOKENS: {}", tokens);

    tokens.into()
}

#[proc_macro_derive(ConstNew)]
pub fn derive_const_new(item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as DeriveInput);
    let tokens = const_new::expand(&input).unwrap_or_else(|err| err.to_compile_error());

    tokens.into()
}
