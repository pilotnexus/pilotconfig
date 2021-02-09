//! Extracts the `PLC_VARIABLES` variable from the given executable and creates a
//! CSV file with information about variables, which then can be used by `pilot fw`.
//!
//! Note that this binary is intended to run on the host operating system. However, the
//! .cargo/config file in the parent directory sets a default embedded ARM target, so
//! a simple `cargo build` will not work in this directory. You have to either specify
//! your host target explicitly (e.g. `cargo build --target x86_64-unknown-linux-gnu`) or
//! run the build command from the parent's parent directory and use the `manifest-path`
//! option (see the call in the Makefile).

use anyhow::anyhow;
use bytes::Buf;
use goblin::{
    elf::{program_header::PT_LOAD, ProgramHeader},
    Object,
};
use std::{collections::HashMap, convert::TryInto, fs, io::Write, ops::Range, path::Path};

fn main() -> anyhow::Result<()> {
    // this executable is only called by the Makefile, so this very simple argument parsing
    // should suffice
    let mut args = std::env::args();
    let file_arg = args.nth(1).ok_or_else(|| anyhow!("No file name given"))?;
    let csv_arg = args
        .next()
        .ok_or_else(|| anyhow!("No csv output path given"))?;

    // read the ELF file and try to parse it
    let file = Path::new(&file_arg);
    let buffer = fs::read(file)?;
    let object = Object::parse(&buffer)?;

    // only elf files are supported
    let elf = match object {
        Object::Elf(elf) => elf,
        other => return Err(anyhow!("Unexpected object type `{:?}`", other)),
    };

    // find the `PLC_VARIABLES` symbol
    let sym = elf
        .syms
        .iter()
        .find(|sym| {
            if let Some(Ok(name)) = elf.strtab.get(sym.st_name) {
                name == "PLC_VARIABLES"
            } else {
                false
            }
        })
        .ok_or_else(|| anyhow!("No PLC_VARIABLES symbol found"))?;

    // Ensure that the symbol has the expected size. A mismatch here indicates that the struct
    // was updated without updating this parser.
    assert_eq!(sym.st_size, VARIABLE_INFO_SIZE.into());

    // traverse the hierarchical `VariableInfo` structure starting at the root
    let mut variables = Vec::new();
    visit_var(
        sym.st_value.try_into().unwrap(),
        None,
        0,
        &mut variables,
        &buffer,
        &elf.program_headers,
    )?;

    // sort the variables by number and generate the CSV file for them
    variables.sort_by_key(|var_info| var_info.number);
    write_csv(csv_arg, &variables)?;

    Ok(())
}

/// Translates a virtual address range specified in the ELF file to a byte range in the file.
fn vaddr_to_offset(
    vaddr: u64,
    size: u64,
    program_headers: &[ProgramHeader],
) -> anyhow::Result<Range<usize>> {
    // find the program segment that contains the given address range
    let program_header = program_headers
        .iter()
        .find(|ph| {
            ph.p_type == PT_LOAD && vaddr >= ph.p_vaddr && vaddr + size <= ph.p_vaddr + ph.p_memsz
        })
        .ok_or_else(|| anyhow!("No program segment found for virtual address {:#x}", vaddr))?;

    // perform the translation
    let offset = vaddr - program_header.p_vaddr + program_header.p_offset;
    Ok(offset as usize..(offset + size) as usize)
}

/// Size of the `VariableInfo` struct of the ELF binary (in bytes).
const VARIABLE_INFO_SIZE: u32 = 28;

/// Size of the `VariableInfo` struct of the ELF binary inclusive struct padding (in bytes).
const VARIABLE_INFO_SIZE_WITH_PADDING: u32 = 28;

/// Traverses a `VariableInfo` struct, adding all variables to the given `variables` list.
fn visit_var(
    vaddr: u32,
    prefix: Option<&str>,
    number_offset: u16,
    variables: &mut Vec<VarInfo>,
    buffer: &[u8],
    program_headers: &[ProgramHeader],
) -> anyhow::Result<()> {
    // get the corresponding bytes from the executable
    let range = vaddr_to_offset(vaddr.into(), VARIABLE_INFO_SIZE.into(), program_headers)?;
    let value = &buffer[range];
    let mut buf = bytes::Bytes::copy_from_slice(value);

    // parse the fields of the `VariableInfo` struct
    let name_ptr = buf.get_u32_le();
    let name_len = buf.get_u32_le();
    let ty_ptr = buf.get_u32_le();
    let ty_len = buf.get_u32_le();
    let fields_ptr = buf.get_u32_le();
    let fields_len = buf.get_u32_le();
    let field_number_offset = buf.get_u16_le();

    // read out the string fields
    let name = std::str::from_utf8(
        &buffer[vaddr_to_offset(name_ptr.into(), name_len.into(), program_headers)?],
    )?;
    let name = if let Some(prefix) = prefix {
        format!("{}.{}", prefix, name)
    } else {
        name.into()
    };
    let ty = std::str::from_utf8(
        &buffer[vaddr_to_offset(ty_ptr.into(), ty_len.into(), program_headers)?],
    )?;

    if fields_len == 0 {
        // this field is a leaf in the tree, which indicates that this is a `Var` type
        let var_info = VarInfo {
            name: name.strip_suffix(".value").unwrap_or(&name).into(),
            number: number_offset,
            ty: ty.into(),
        };
        variables.push(var_info);
    } else {
        // this field has children -> traverse them recursively
        for i in 0..fields_len {
            let vaddr = fields_ptr + i * VARIABLE_INFO_SIZE_WITH_PADDING;
            visit_var(
                vaddr,
                Some(&name),
                number_offset + field_number_offset,
                variables,
                buffer,
                program_headers,
            )?;
        }
    }

    Ok(())
}

/// Description of a variable of type `Var`, required for creating the CSV file
#[derive(Debug)]
struct VarInfo {
    name: String,
    number: u16,
    ty: String,
}

/// Creates a CSV file for the `pilot fw` tool from the given variable list.
fn write_csv(csv_arg: String, variables: &[VarInfo]) -> anyhow::Result<()> {
    // create csv file
    let dest_path = Path::new(&csv_arg);
    let mut f = fs::OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(&dest_path)
        .unwrap();

    // translations for the different type names
    let iecvars = {
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

    // write out the variable info
    for var in variables {
        writeln!(
            f,
            "{0};VAR;CONFIG.{1};CONFIG.{1};{2};",
            var.number,
            &var.name,
            iecvars.get(&var.ty.as_ref()).unwrap_or(&"UNKNOWN"),
        )?
    }
    Ok(())
}
