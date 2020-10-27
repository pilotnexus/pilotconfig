//! This build script links the `libpilot.a` staticlib to the executable.

use llvm_tools::{exe, LlvmTools};
use std::{env, fs, path::Path, process::Command};

const STATICLIB_PATH: &str = "../lib/libpilot.a";

fn main() {
    let out_dir_str = env::var("OUT_DIR").unwrap();
    let out_dir = Path::new(&out_dir_str);
    let llvm_tools = LlvmTools::new().expect("LLVM tools not found");
    let objcopy = llvm_tools
        .tool(&exe("llvm-objcopy"))
        .expect("llvm-objcopy not found");

    let path = out_dir.join("libpilot.a");

    fs::copy(Path::new(STATICLIB_PATH), &path).unwrap();

    // localize symbols to avoid errors because of duplicated rust_begin_unwind symbols
    let mut cmd = Command::new(objcopy);
    cmd.arg("-G").arg("PLC_VARIABLES");
    cmd.arg(path);
    let status = cmd.status().unwrap();
    assert!(status.success());

    println!("cargo:rustc-link-search={}", out_dir_str);
    println!("cargo:rustc-link-lib=pilot");

    println!("cargo:rerun-if-changed={}", STATICLIB_PATH);
}
