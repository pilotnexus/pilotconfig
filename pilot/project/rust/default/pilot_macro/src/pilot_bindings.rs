use proc_macro2::TokenStream;
use quote::{quote, quote_spanned};
use syn::{parse2, spanned::Spanned, AttrStyle, DataStruct, DeriveInput, Error, Result};

pub fn expand(node: &DeriveInput) -> Result<TokenStream> {
    let s = match &node.data {
        syn::Data::Struct(data) => data,
        _other => {
            return Err(Error::new_spanned(
                node,
                "Deriving `Var` for enums is not supported",
            ))
        }
    };

    let Bindings {
        set_from_pilot_bindings,
        write_to_pilot_bindings,
    } = generate_bindings(s)?;

    let struct_name = &node.ident;

    let bind_type = if let Some(attribute) = node.attrs.iter().find(|a| {
        a.path
            .get_ident()
            .map(|i| i.to_string().as_str() == "bind_type")
            .unwrap_or(false)
    }) {
        let type_path: syn::TypePath = attribute.parse_args()?;
        quote!(#type_path)
    } else {
        quote!(crate::pilot::bindings::plc_dev_t)
    };

    Ok(quote! {
        impl crate::pilot::bindings::PilotBindings for #struct_name {
            type BindType = #bind_type;

            fn set_from_pilot_bindings(&self, plc_mem: &Self::BindType) {
                #(#set_from_pilot_bindings)*
            }

            fn write_to_pilot_bindings(&self, plc_mem: &mut Self::BindType) {
                #(#write_to_pilot_bindings)*
            }
        }
    })
}

struct Binding {
    expr: syn::Expr,
    options: syn::punctuated::Punctuated<syn::Meta, syn::Token![,]>,
}

impl syn::parse::Parse for Binding {
    fn parse(input: syn::parse::ParseStream) -> syn::Result<Self> {
        let expr = input.parse()?;

        let options = if input.peek(syn::Token![,]) {
            input.parse::<syn::Token![,]>()?;
            input.parse_terminated(syn::Meta::parse)?
        } else {
            syn::punctuated::Punctuated::new()
        };

        Ok(Self { expr, options })
    }
}

#[derive(Default)]
struct BindingOptions {
    bit: Option<syn::LitInt>,
    filter: Option<syn::Path>,
}

impl BindingOptions {
    fn from_puncutated(
        options: &syn::punctuated::Punctuated<syn::Meta, syn::Token![,]>,
    ) -> syn::Result<Self> {
        let mut parsed = BindingOptions::default();

        for option in options {
            match option {
                syn::Meta::Path(path) => {
                    return Err(syn::Error::new_spanned(path, "unsupported option"))
                }
                syn::Meta::NameValue(option) => {
                    let name = option
                        .path
                        .get_ident()
                        .ok_or(syn::Error::new_spanned(&option.path, "must be `bit`"))?;
                    match name.to_string().as_str() {
                        "bit" => {
                            if parsed.bit.is_some() {
                                return Err(syn::Error::new(name.span(), "`bit` given twice"));
                            }
                            let bit_number = match &option.lit {
                                syn::Lit::Int(integer) => integer,
                                other => {
                                    return Err(syn::Error::new_spanned(
                                        &other,
                                        "must be an integer literal",
                                    ))
                                }
                            };
                            parsed.bit = Some(bit_number.to_owned());
                        }
                        _other => {
                            return Err(syn::Error::new(name.span(), "unknown option"));
                        }
                    }
                }
                syn::Meta::List(list) => {
                    let name = list
                        .path
                        .get_ident()
                        .ok_or_else(|| syn::Error::new_spanned(&list.path, "unsupported option"))?;

                    match name.to_string().as_str() {
                        "filter" => {
                            if parsed.filter.is_some() {
                                return Err(syn::Error::new(name.span(), "`filter` given twice"));
                            }
                            if list.nested.len() > 1 {
                                return Err(syn::Error::new(
                                    list.nested.span(),
                                    "to many arguments",
                                ));
                            }
                            let arg = list.nested.first().ok_or_else(|| {
                                syn::Error::new(
                                    list.span(),
                                    "expected filter function name as argument",
                                )
                            })?;

                            if let syn::NestedMeta::Meta(syn::Meta::Path(path)) = arg {
                                parsed.filter = Some(path.to_owned());
                            } else {
                                return Err(syn::Error::new(
                                    arg.span(),
                                    "expected path to function",
                                ));
                            }
                        }
                        _other => {
                            return Err(syn::Error::new(name.span(), "unknown option"));
                        }
                    }
                }
            }
        }

        Ok(parsed)
    }
}

/// Generates the code for the `set_from_pilot_bindings` and `write_to_pilot_bindings` methods.
fn generate_bindings(s: &DataStruct) -> Result<Bindings> {
    let mut set_from_pilot_bindings = Vec::new();
    let mut write_to_pilot_bindings = Vec::new();

    // expand bind_read and bind_write fields
    for field in &s.fields {
        let field_name = &field.ident;

        // whether a `#[bind_*]` attribute was found for the field
        let mut bind_attribute_found = false;

        for attribute in &field.attrs {
            if let AttrStyle::Inner(_) = attribute.style {
                continue; // only outer attributes (#[attribute]) are supported
            }

            match attribute.path.get_ident().map(|i| i.to_string()).as_deref() {
                Some("bind_read") => {
                    bind_attribute_found = true;

                    let Binding { expr, options } = attribute.parse_args::<Binding>()?;
                    let parsed = BindingOptions::from_puncutated(&options)?;

                    let value = match parsed.bit {
                        Some(bit_number) => {
                            // generate code for extracting the specified bit from the `plc_mem` and
                            // setting the value accordingly
                            quote_spanned!(field.span()=> (plc_mem.#expr & (1 << #bit_number)) > 0)
                        }
                        None => {
                            // full module (not single bit access)
                            quote_spanned!(expr.span()=> plc_mem.#expr)
                        }
                    };
                    let filtered = match parsed.filter {
                        Some(filter) => quote!(#filter ( #value )),
                        None => quote!(#value),
                    };
                    set_from_pilot_bindings.push(quote_spanned! {field.ty.span()=>
                        pilot_types::var::VarProps::set(&self.#field_name, #filtered);
                    });
                }
                Some("bind_write") => {
                    bind_attribute_found = true;

                    let Binding { expr, options } = attribute.parse_args::<Binding>()?;
                    let parsed = BindingOptions::from_puncutated(&options)?;

                    let value = quote_spanned!(field.ty.span()=> pilot_types::var::VarProps::get(&self.#field_name) );
                    let filtered = match parsed.filter {
                        Some(filter) => quote!(#filter ( #value )),
                        None => quote!(#value),
                    };
                    match parsed.bit {
                        Some(bit_number) => {
                            // generate code for setting the specified bit of the `plc_mem`
                            write_to_pilot_bindings.push(quote! {
                                match #filtered {
                                    true => plc_mem.#expr |= 1 << #bit_number,
                                    false => plc_mem.#expr &= !(1 << #bit_number),
                                }
                            });
                        }
                        None => {
                            // full module (not single bit access)

                            write_to_pilot_bindings.push(quote! {
                                plc_mem.#expr = #filtered;
                            });
                        }
                    };
                }
                // #[bind_nested] attribute on a field that references another struct
                Some("bind_nested") => {
                    bind_attribute_found = true;

                    let field_ty = &field.ty;

                    let (plc_mem, check_trait) = if let Ok(syn::parse::Nothing) =
                        parse2(attribute.tokens.clone())
                    {
                        let bind_type = quote!(crate::bindings::plc_dev_t);
                        let check_trait = quote_spanned! {field.ty.span()=>
                            {struct _X where #field_ty: crate::pilot::bindings::PilotBindings<BindType = #bind_type>; }
                        };
                        (quote!(*plc_mem), check_trait)
                    } else {
                        let field_access: syn::Expr = attribute.parse_args()?;
                        (
                            quote_spanned!(field_access.span()=> plc_mem.#field_access),
                            quote!(),
                        )
                    };

                    // generate code to forward the implementation to the
                    // `set_from_pilot_bindings` and `write_to_pilot_bindings`
                    // implementations of the referenced struct
                    set_from_pilot_bindings.push(quote_spanned! {field.ty.span()=>
                        #check_trait
                        crate::pilot::bindings::PilotBindings::set_from_pilot_bindings(&self.#field_name, &#plc_mem);
                    });
                    write_to_pilot_bindings.push(quote_spanned! {field.ty.span()=>
                        #check_trait
                        crate::pilot::bindings::PilotBindings::write_to_pilot_bindings(&self.#field_name, &mut #plc_mem);
                    });
                }
                Some("bind_ignore") => {
                    // only silence the error about missing `#[bind_*]` attributes
                    bind_attribute_found = true;
                }
                _other => {}
            }
        }

        if !bind_attribute_found {
            return Err(Error::new_spanned(
                field,
                "Field must be annotated with a `bind_*` attribute. Use `bind_ignore` to ignore this field.",
            ));
        }
    }

    Ok(Bindings {
        set_from_pilot_bindings,
        write_to_pilot_bindings,
    })
}

/// The return type of the `generate_bindings` function.
struct Bindings {
    /// The operations of the `set_from_pilot_bindings` method.
    set_from_pilot_bindings: Vec<TokenStream>,

    /// The operations of the `write_to_pilot_bindings` method.
    write_to_pilot_bindings: Vec<TokenStream>,
}
