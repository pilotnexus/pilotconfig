use proc_macro2::TokenStream;
use quote::{quote, quote_spanned};
use syn::{spanned::Spanned, DataStruct, DeriveInput, Error, Result};

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

    let struct_name = &node.ident;

    Ok(quote! {
        impl #struct_name {
            pub const fn new() -> Self {
                Self {
                    #(#field_initializers)*
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

        field_initializers.push(quote_spanned!(field.ty.span()=>
            #field_name: <#field_ty>::new(),
        ));
    }

    field_initializers
}
