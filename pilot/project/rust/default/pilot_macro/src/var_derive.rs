use crate::{extract_type_from_var, parse_path, BINDINGS, ROOT};
use itertools::Itertools;
use proc_macro2::TokenStream;
use quote::quote;
use regex::Regex;
use std::collections::HashMap;
use syn::{DataStruct, DeriveInput, Error, Result};

const ROOT_ATTR_NAME: &'static str = "root";
const BIND_ATTR_NAME: &'static str = "bind";

pub fn expand(
    node: &DeriveInput,
    map: &mut HashMap<String, Vec<(String, String, Option<String>)>>,
) -> Result<TokenStream> {
    let (m, initializers) = match &node.data {
        syn::Data::Struct(data) => expand_struct(node, data),
        _other => {
            return Err(Error::new_spanned(
                node,
                "Deriving `Var` for enums is not supported",
            ))
        }
    };

    map.insert(node.ident.to_string(), m);

    let structname = &node.ident;

    Ok(quote!(
        impl #structname {
            pub const fn new() -> #structname {
                #structname { #(#initializers),* }
            }
        }
    ))
}

fn expand_struct(
    node: &DeriveInput,
    s: &DataStruct,
) -> (Vec<(String, String, Option<String>)>, Vec<TokenStream>) {
    let mut m: Vec<(String, String, Option<String>)> = Vec::new();
    let mut initializers = Vec::new();

    // Looks for state_change attriute (our attribute)
    if let Some(ref _a) = node.attrs.iter().find(|a| a.path.is_ident(ROOT_ATTR_NAME)) {
        //eprintln!("Found root on {}", name);
        *(ROOT.lock().unwrap()) = Some(node.ident.to_string());
    }
    for f in s.fields.iter() {
        let vartype = match extract_type_from_var(&f.ty) {
            Some(p) => match p {
                syn::Type::Path(s) => Some(parse_path(&s.path)),
                _ => panic!("type needs to be path"),
            },
            None => None,
        };
        //eprintln!("type is {:?}", vartype);

        //look for bind attributes
        if let Some(b) = f
            .attrs
            .iter()
            .find(|a| parse_path(&a.path) == BIND_ATTR_NAME)
        {
            let mut bindings = BINDINGS.lock().unwrap();
            let tts_str = b.tokens.to_string().replace(&['(', ')', ' '][..], "");
            for v in tts_str.split(",").map(|item| {
                item.split("=>")
                    .next_tuple::<(&str, &str)>()
                    .expect("Cannot extract tuple, are you missing the => operator?")
            }) {
                let re = Regex::new(r"\|(?P<rw>.*?)\|(?P<fqn>.*)").unwrap();
                let result = re.captures(v.0).unwrap();
                let fqn = format!(
                    "{}{}{}",
                    &result["fqn"],
                    if let 0 = &result["fqn"].len() {
                        ""
                    } else {
                        "."
                    },
                    f.ident.clone().unwrap().to_string()
                );
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

        let f_ident = f.ident.as_ref().unwrap();
        let f_ty = &f.ty;
        initializers.push(quote!(
            #f_ident: <#f_ty>::new()
        ));
        m.push((f.ident.clone().unwrap().to_string(), ty.clone(), vartype));
    }
    (m, initializers)
}
