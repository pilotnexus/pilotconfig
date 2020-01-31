#[macro_export]
macro_rules! print {
  ($f:expr) => (
    unsafe {
      for c in $f.chars() { 
        _putchar(c as u8);
      }
    }
  )
}

#[macro_export]
macro_rules! println {
  ($f:expr) => (
    print!($f);
    unsafe {
      _putchar(10);
      _putchar(13);
    }
  )
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
macro_rules! on_posedge_all {
  ( $x:expr => $f:expr ) => {
    if $x.pos() { $f; }
  };

  ( $first:expr, $($x:expr),+ => $f:expr ) => {
    if $first.pos() $(&& $x.pos())* { $f; }
  };
}
