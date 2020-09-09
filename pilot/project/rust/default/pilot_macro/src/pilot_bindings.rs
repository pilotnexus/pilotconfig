use proc_macro2::TokenStream;
use quote::quote;
use syn::{
    parse2, AttrStyle, DataStruct, DeriveInput, Error, ExprField, Ident, Member, Result, Type,
};

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

    let field_initializers = field_initializers(s);
    let NumberAssignment {
        plc_varnumber_to_variable,
        plc_varnumber_to_variable_inner_fields,
        compound_field_num,
        variables,
    } = assign_field_numbers(s)?;
    let Bindings {
        set_from_pilot_bindings,
        write_to_pilot_bindings,
    } = generate_bindings(s)?;

    let struct_name = &node.ident;

    Ok(quote! {
        impl #struct_name {
            pub const fn new() -> Self {
                Self {
                    #(#field_initializers)*
                }
            }
        }

        impl crate::pilot::bindings::PilotBindings for #struct_name {
            const MAX_FIELD_NUM: u16 = #(#compound_field_num)+*;

            const VARIABLES: &'static [crate::pilot::bindings::VariableInfo] = &[#(#variables),*];

            fn set_from_pilot_bindings(&mut self, plc_mem: &crate::pilot::bindings::plc_dev_t) {
                #(#set_from_pilot_bindings)*
            }

            fn write_to_pilot_bindings(&self, plc_mem: &mut crate::pilot::bindings::plc_dev_t) {
                #(#write_to_pilot_bindings)*
            }

            fn plc_varnumber_to_variable(&mut self, number: u16) -> Option<&mut dyn MemVar> {
                match number {
                    #(#plc_varnumber_to_variable)*
                    #(#plc_varnumber_to_variable_inner_fields)*
                    _ => None,
                }
           }
        }
    })
}

/// Creates a call to `field::new` for each field in the struct.
fn field_initializers(s: &DataStruct) -> Vec<TokenStream> {
    let mut field_initializers = Vec::new();

    // create field initializers
    for field in &s.fields {
        let field_name = &field.ident;
        let field_ty = &field.ty;

        field_initializers.push(quote!(
            #field_name: <#field_ty>::new(),
        ));
    }

    field_initializers
}

/// Generates the code for assigning an unique number to each field of type `Var`.
///
/// This also generates the implementation of the `MAX_FIELD_NUM` and `VARIABLES`
/// constants of the `PilotBindings` trait. See the docs for the `NumberAssignment`
/// struct for a description of the return type of this function.
fn assign_field_numbers(s: &DataStruct) -> Result<NumberAssignment> {
    // see the `NumberAssignment` struct for a description of these variables
    let mut plc_varnumber_to_variable = Vec::new();
    let mut plc_varnumber_to_variable_inner_fields = Vec::new();
    let mut field_num: u16 = 0;
    let mut variables = Vec::new();

    // first assign numbers for fields of type `Var`
    for field in &s.fields {
        let field_name = &field.ident;

        // skip fields that aren't of type `Var`
        let ty_path = if let Type::Path(ty_path) = &field.ty {
            let first_segment = ty_path.path.segments.first();
            if first_segment.map(|p| p.ident.to_string()).as_deref() == Some("Var") {
                ty_path
            } else {
                continue;
            }
        } else {
            continue;
        };

        // assign the current `field_num` to this `Var` field
        plc_varnumber_to_variable.push(quote! {
            #field_num => Some(&mut self.#field_name),
        });

        // extract the inner field type of the `Var` field (e.g. `bool` for `Var<bool>`)
        let field_ty = {
            let ty_args = match &ty_path.path.segments.first().unwrap().arguments {
                syn::PathArguments::AngleBracketed(args) => args,
                other => {
                    return Err(Error::new_spanned(
                        other,
                        "Expected generic arguments in angle brackets",
                    ))
                }
            };
            if ty_args.args.iter().len() != 1 {
                return Err(Error::new_spanned(
                    &ty_args.args,
                    "Expected exactly one generic argument",
                ));
            }
            ty_args.args.iter().next().unwrap()
        };

        // Generate a `VariableInfo` struct for this `Var` field.
        //
        // Since fields of type `Var` have no inner fields (unlike fields that reference
        // other structs), we set the `fields` field to the empty slice and the
        // `field_number_offset` to 0.
        variables.push(quote! {
            crate::pilot::bindings::VariableInfo {
                name: core::stringify!(#field_name),
                ty: core::stringify!(#field_ty),
                number: #field_num,
                fields: &[],
                field_number_offset: 0,
            }
        });

        // increase the field number by 1 so that the next field is assigned a different number
        field_num += 1;
    }

    // In the second step, assign field numbers for other fields.
    //
    // Since we don't know the number of fields of referenced structs, we can't calculate
    // the number ranges for the fields directly. Instead, we utilize the fact that referenced
    // structs also implement the PilotBindings trait and generate code that sums the
    // associated `MAX_FIELD_NUM` constants of fields and let the compiler sum these values for
    // us. The `compound_field_num` variable stores the terms of this sum.
    let mut compound_field_num = Vec::new();
    compound_field_num.push(quote! {#field_num});
    for field in &s.fields {
        let field_name = &field.ident;

        // skip `Var` fields (we already handled these above)
        if let Type::Path(ty_path) = &field.ty {
            let first_segment = ty_path.path.segments.first();
            if first_segment.map(|p| p.ident.to_string()).as_deref() == Some("Var") {
                continue;
            }
        }

        // add the compound_field_num elements together
        let offset = quote! {
            (#(#compound_field_num)+*)
        };

        let ty = &field.ty;
        let field_as_trait = quote! {
            <#ty as crate::pilot::bindings::PilotBindings>
        };

        // Forward `plc_varnumber_to_variable` calls to the field implementation. We need to
        // subtract the offset because each struct uses local field numbering starting at 0.
        plc_varnumber_to_variable_inner_fields.push(quote! {
            num if num >= #offset && num < (#offset + #field_as_trait::MAX_FIELD_NUM) => {
                #field_as_trait::plc_varnumber_to_variable(&mut self.#field_name, num - #offset)
            }
        });

        // add the number of fields of the referenced struct to the total field number
        compound_field_num.push(quote! {
            #field_as_trait::MAX_FIELD_NUM
        });

        // Generate a `VariableInfo` struct for this field.
        //
        // Since this field references a different struct, we set the `fields` and
        // `field_number_offset` fields accordingly, utilizing the fact that the field
        // also implements the `PilotBindings` trait. We don't assign a field number,
        // since the `number` field is only relevant for fields of type `Var` that have
        // an empty `fields` slice.
        variables.push(quote! {
            crate::pilot::bindings::VariableInfo {
                name: core::stringify!(#field_name),
                ty: "COMPOUND",
                fields: #field_as_trait::VARIABLES,
                field_number_offset: #offset,
                number: 0,
            }
        });
    }

    Ok(NumberAssignment {
        plc_varnumber_to_variable,
        plc_varnumber_to_variable_inner_fields,
        compound_field_num,
        variables,
    })
}

/// The return type of the `assign_field_numbers` function.
struct NumberAssignment {
    /// Match arm for the `plc_varnumber_to_variable` function for `Var` fields
    ///
    /// These match arms are of format `n => […]` where `n` is the local number
    /// of the field. This numbering starts at 0 for each struct, so fields that
    /// reference other fields need to subtract an offset before calling the
    /// `plc_varnumber_to_variable` function on these fields.
    plc_varnumber_to_variable: Vec<TokenStream>,

    /// Also a match arm for the `plc_varnumber_to_variable` function, but for fields
    /// that reference other structs.
    ///
    /// These match arms are of format `num if num >= x && num < y => […]`. They forward
    /// the call to the `plc_varnumber_to_variable(z)` implementation of the field where
    /// `z` is the varnumber minus the number offset `x` of that field.
    plc_varnumber_to_variable_inner_fields: Vec<TokenStream>,

    /// The total number of `Var` fields, including the `Var` fields of all referenced
    /// structs.
    ///
    /// The format of this is `n + sum(Field::MAX_FIELD_NUM)` where `n` is the number
    /// of `Var` fields in this struct and `Field` are the fields referencing other
    /// structs. The `MAX_FIELD_NUM` is an associated constant of the PilotBindings trait,
    /// which these fields should implement.
    compound_field_num: Vec<TokenStream>,

    /// Contains an implementation for the `PilotBindings::VARIABLES` constant, which is
    /// a hierarchy of `VariableInfo` structs that can be used to read out the information
    /// about all `Var` fields from the staticlib.
    variables: Vec<TokenStream>,
}

/// Generates the code for the `set_from_pilot_bindings` and `write_to_pilot_bindings` methods.
fn generate_bindings(s: &DataStruct) -> Result<Bindings> {
    let mut set_from_pilot_bindings = Vec::new();
    let mut write_to_pilot_bindings = Vec::new();

    // expand bind_read and bind_write fields
    for field in &s.fields {
        let field_name = &field.ident;

        // whether the current field is of type `Var` or not
        let is_var = if let Type::Path(ty_path) = &field.ty {
            let first_segment = ty_path.path.segments.first();
            first_segment.map(|p| p.ident.to_string()).as_deref() == Some("Var")
        } else {
            false
        };

        // whether a `#[bind_*]` attribute was found for the field
        let mut bind_attribute_found = false;

        for attribute in &field.attrs {
            if let AttrStyle::Inner(_) = attribute.style {
                continue; // only outer attributes (#[attribute]) are supported
            }

            match attribute.path.get_ident().map(|i| i.to_string()).as_deref() {
                // #[bind_read] attribute on a field of type `Var`
                Some("bind_read") if is_var => {
                    bind_attribute_found = true;

                    if let Ok(expr_field) = attribute.parse_args::<ExprField>() {
                        // single bit

                        let plc_module = &expr_field.base;
                        let module_bit = match expr_field.member {
                            Member::Unnamed(index) => index, // TODO: check if out of bounds
                            Member::Named(ident) => {
                                return Err(Error::new_spanned(ident, "Must be a bit number"))
                            }
                        };

                        // generate code for extracting the specified bit from the `plc_mem` and
                        // setting the value accordingly
                        set_from_pilot_bindings.push(quote! {
                            self.#field_name.set((plc_mem.#plc_module & (1 << #module_bit)) > 0);
                        });
                    } else if let Ok(plc_module) = attribute.parse_args::<Ident>() {
                        // full module (not single bit access)

                        return Err(Error::new_spanned(
                            plc_module,
                            "Only bit-access is supported at the moment",
                        ));
                    } else {
                        return Err(Error::new_spanned(&attribute.tokens, "Malformed attribute"));
                    }
                }
                // #[bind_read] attribute on a field that references another struct
                Some("bind_read") => {
                    bind_attribute_found = true;

                    if let Ok(syn::parse::Nothing) = parse2(attribute.tokens.clone()) {
                        // generate code to forward the implementation to the
                        // `set_from_pilot_bindings` implementation of the referenced struct
                        set_from_pilot_bindings.push(quote! {
                            crate::pilot::bindings::PilotBindings::set_from_pilot_bindings(&mut self.#field_name, plc_mem);
                        });
                    } else {
                        return Err(Error::new_spanned(
                            &attribute.tokens,
                            "Arguments are only supported on `Var` types",
                        ));
                    }
                }
                // #[bind_write] attribute on a field of type `Var`
                Some("bind_write") if is_var => {
                    bind_attribute_found = true;

                    if let Ok(expr_field) = attribute.parse_args::<ExprField>() {
                        // single bit

                        let plc_module = &expr_field.base;
                        let module_bit = match expr_field.member {
                            Member::Unnamed(index) => index, // TODO: check if out of bounds
                            Member::Named(ident) => {
                                return Err(Error::new_spanned(ident, "Must be a bit number"))
                            }
                        };

                        // generate code for setting the specified bit of the `plc_mem`
                        write_to_pilot_bindings.push(quote! {
                            match self.#field_name.get() {
                                true => plc_mem.#plc_module |= 1 << #module_bit,
                                false => plc_mem.#plc_module &= !(1 << #module_bit),
                            }
                        });
                    } else if let Ok(plc_module) = attribute.parse_args::<Ident>() {
                        return Err(Error::new_spanned(
                            plc_module,
                            "Only bit-access is supported at the moment",
                        ));
                    } else {
                        return Err(Error::new_spanned(&attribute.tokens, "Malformed attribute"));
                    }
                }
                // #[bind_write] attribute on a field that references another struct
                Some("bind_write") => {
                    bind_attribute_found = true;

                    if let Ok(syn::parse::Nothing) = parse2(attribute.tokens.clone()) {
                        // generate code to forward the implementation to the
                        // `write_to_pilot_bindings` implementation of the referenced struct
                        write_to_pilot_bindings.push(quote! {
                            crate::pilot::bindings::PilotBindings::write_to_pilot_bindings(&self.#field_name, plc_mem);
                        });
                    } else {
                        return Err(Error::new_spanned(
                            &attribute.tokens,
                            "Arguments are only supported on `Var` types",
                        ));
                    }
                }
                Some("bind_ignore") => {
                    // only silence the error about missing `#[bind_*]` attributes
                    bind_attribute_found = true;
                }
                _other => {}
            }
        }

        if !is_var && !bind_attribute_found {
            return Err(Error::new_spanned(
                field,
                "Field must be either a `Var` type or must \
                be annotated with a `bind_*` attribute. Use `bind_ignore` to ignore this field.",
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
