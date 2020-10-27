// build.rs

use std::env;

///
/// This sets the PILOT_OUT_DIR environment variable. This is needed for the pilot_macro crate to write the variables file (VARIABLES.csv)
///
fn main() {
    println!(
        "cargo:rustc-env=PILOT_OUT_DIR={}/out",
        env::var("CARGO_MANIFEST_DIR").unwrap()
    );
}
