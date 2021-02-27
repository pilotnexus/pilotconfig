use core::fmt;

pub struct SerialWriter;

impl fmt::Write for SerialWriter {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        unsafe {
            for c in s.chars() {
                crate::pilot::_putchar(c as u8);
            }
        }
        Ok(())
    }
}

#[macro_export]
macro_rules! crate_version {
    () => {
        env!("CARGO_PKG_VERSION")
    };
}

#[macro_export]
macro_rules! start_print {
    ($f:expr) => {
        unsafe {
          crate::pilot::_putchar(0x27); // start of logstring
        }
    };
}

#[macro_export]
macro_rules! print {
    ($f:expr) => {
        unsafe {
            for c in $f.chars() {
                crate::pilot::_putchar(c as u8);
            }
        }
    };
}

#[macro_export]
macro_rules! println {
    ($f:expr) => {
        unsafe {
          crate::pilot::_putchar(0x27); // start of logstring
        }
        print!($f);
        unsafe {
            crate::pilot::_putchar(10);
            crate::pilot::_putchar(13);
        }
    };
}

#[macro_export]
macro_rules! on_posedge {
  ( $x:expr => $f:expr ) => {
    if $x.pos() { $f; }
  };

  ( $first:expr, $($x:expr),+ => $f:expr ) => {
    if $first.pos() $(|| $x.pos())* { $f; }
  };
}

#[macro_export]
macro_rules! on_negedge {
  ( $x:expr => $f:expr ) => {
    if $x.neg() { $f; }
  };

  ( $first:expr, $($x:expr),+ => $f:expr ) => {
    if $first.neg() $(|| $x.neg())* { $f; }
  };
}

#[macro_export]
macro_rules! on_posedge_all {
  ( $first:expr,$($x:expr),+ => $f:expr ) => {
    if $first.pos() $(&& $x.pos())* { $f; }
  };
}
