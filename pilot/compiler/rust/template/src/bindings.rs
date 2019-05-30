#[no_mangle]
extern "C" { 
  pub fn pilot_usart_send_string ( format: *const u8) ; 
  pub fn pilot_usart_send_char(c: u8);
  }

pub fn serial_debug(format: &str) {
  unsafe {
      pilot_usart_send_string(format.as_ptr());
  }
}

macro_rules! print {
  ($f:expr) => (
    unsafe {
      for c in $f.chars() { 
        pilot_usart_send_char(c as u8);
      }
    }
  )
}

macro_rules! println {
  ($f:expr) => (
    print!($f);
    unsafe {
      pilot_usart_send_char(10);
      pilot_usart_send_char(13);
    }
  )
}