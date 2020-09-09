#[macro_export]
macro_rules! print {
    ($f:expr) => {
        unsafe {
            _putchar(0x27); // start of logstring
            for c in $f.chars() {
                _putchar(c as u8);
            }
        }
    };
}

#[macro_export]
macro_rules! println {
    ($f:expr) => {
        print!($f);
        unsafe {
            _putchar(10);
            _putchar(13);
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
