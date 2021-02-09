use proc_macro2::TokenStream;
use quote::{quote, quote_spanned};
use syn::{spanned::Spanned, DataStruct, DeriveInput, Error, Result};

pub fn expand(node: &DeriveInput) -> Result<TokenStream> {
    let s = match &node.data {
        syn::Data::Struct(data) => data,
        _other => {
            return Err(Error::new_spanned(
                node,
                "Deriving `PilotAccess` for enums is not supported",
            ))
        }
    };

    let NumberAssignment {
        plc_varnumber_to_variable_inner_fields,
        compound_field_num,
        variables,
    } = assign_field_numbers(s)?;

    let struct_name = &node.ident;

    Ok(quote! {
        impl crate::pilot::bindings::PilotAccess for #struct_name {
            const FIELD_NUM: u16 = #(#compound_field_num)+*;

            const VARIABLES: &'static [crate::pilot::bindings::VariableInfo] = &[#(#variables),*];

            fn plc_varnumber_to_variable(&self, number: u16) -> Option<&dyn MemVar> {
                match number {
                    #(#plc_varnumber_to_variable_inner_fields)*
                    _ => None,
                }
           }
        }
    })
}

/// Generates the code for assigning an unique number to each field of type `Var`.
///
/// This also generates the implementation of the `FIELD_NUM` and `VARIABLES`
/// constants of the `PilotAccess` trait. See the docs for the `NumberAssignment`
/// struct for a description of the return type of this function.
fn assign_field_numbers(s: &DataStruct) -> Result<NumberAssignment> {
    // see the `NumberAssignment` struct for a description of these variables
    let mut plc_varnumber_to_variable_inner_fields = Vec::new();
    let mut variables = Vec::new();

    // Since we don't know the number of fields of referenced types, we can't calculate
    // the number ranges for the fields directly. Instead, we utilize the fact that referenced
    // types also implement the PilotAccess trait and generate code that sums the
    // associated `FIELD_NUM` constants of fields and let the compiler sum these values for
    // us. The `compound_field_num` variable stores the terms of this sum.
    let mut compound_field_num = Vec::new();
    compound_field_num.push(quote!(0));
    for field in &s.fields {
        let field_name = &field.ident;

        // add the compound_field_num elements together
        let offset = quote! {
            (#(#compound_field_num)+*)
        };

        let ty = &field.ty;
        let field_as_trait = quote_spanned! {ty.span()=>
            <#ty as crate::pilot::bindings::PilotAccess>
        };
        let field_plc_varnumber_to_variable =
            quote_spanned!(ty.span()=> #field_as_trait::plc_varnumber_to_variable);
        let field_field_num = quote_spanned!(ty.span()=> #field_as_trait::FIELD_NUM);
        let field_variables = quote_spanned!(ty.span()=> #field_as_trait::VARIABLES);

        // Forward `plc_varnumber_to_variable` calls to the field implementation. We need to
        // subtract the offset because each struct uses local field numbering starting at 0.
        //
        // The `Var` type provides a manual implementation of `PilotAccess` and thus provides the
        // leave implemenation for this recursive function.
        plc_varnumber_to_variable_inner_fields.push(quote! {
            num if num >= #offset && num < (#offset + #field_field_num) => {
                #field_plc_varnumber_to_variable(&self.#field_name, num - #offset)
            }
        });

        // add the number of fields of the referenced struct to the total field number
        compound_field_num.push(quote! {
            #field_field_num
        });

        // Generate a `VariableInfo` struct for this field.
        //
        // Since this field references a different struct, we set the `fields` and
        // `field_number_offset` fields accordingly, utilizing the fact that the field
        // also implements the `PilotAccess` trait.
        variables.push(quote! {
            crate::pilot::bindings::VariableInfo {
                name: core::stringify!(#field_name),
                ty: "COMPOUND",
                fields: #field_variables,
                field_number_offset: #offset,
            }
        });
    }

    Ok(NumberAssignment {
        plc_varnumber_to_variable_inner_fields,
        compound_field_num,
        variables,
    })
}

/// The return type of the `assign_field_numbers` function.
struct NumberAssignment {
    /// Match arm for the `plc_varnumber_to_variable` function for fields
    /// that reference other types.
    ///
    /// These match arms are of format `num if num >= x && num < y => […]`. They forward
    /// the call to the `plc_varnumber_to_variable(z)` implementation of the field where
    /// `z` is the varnumber minus the number offset `x` of that field. The subtraction is
    /// required because the local field numbering starts at 0 for each type.
    plc_varnumber_to_variable_inner_fields: Vec<TokenStream>,

    /// The total number of `Var` fields, including the `Var` fields of all referenced
    /// structs.
    ///
    /// The format of this is `n + sum(Field::FIELD_NUM)` where `n` is the number
    /// of `Var` fields in this struct and `Field` are the fields referencing other
    /// structs. The `FIELD_NUM` is an associated constant of the PilotAccess trait,
    /// which these fields should implement.
    compound_field_num: Vec<TokenStream>,

    /// Contains an implementation for the `PilotAccess::VARIABLES` constant, which is
    /// a hierarchy of `VariableInfo` structs that can be used to read out the information
    /// about all `Var` fields from the staticlib.
    variables: Vec<TokenStream>,
}
