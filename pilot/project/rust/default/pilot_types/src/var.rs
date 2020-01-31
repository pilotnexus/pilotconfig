use core::sync::atomic::{Ordering, AtomicBool, AtomicI32, AtomicU32, AtomicI16, AtomicU16, AtomicI8, AtomicU8};

pub trait MemVar: Sync {
  unsafe fn to_buffer(&self, buffer: *mut u8);
  unsafe fn from_buffer(&mut self, buffer: *const u8);
  fn len(&self) -> i32;
}

pub trait VarProps<T> {
  fn get(&self) -> T; 
  fn set(&mut self, value: T);
}

pub trait VarChange {
  fn pos(&self) -> bool;
  fn neg(&self) -> bool;
  fn changed(&self) -> bool;
}

pub struct Var<T: Default> {
  v: T,
  forced: Option<T>,
  pos: bool,
  neg: bool
}

impl<T: Default> VarChange for Var<T> {
  fn pos(&self) -> bool {
    self.pos
  }

  fn neg(&self) -> bool {
    self.neg
  }

  fn changed(&self) -> bool {
    self.pos || self.neg
  }
}

impl Var<AtomicI32> {
  pub const fn new() -> Var<AtomicI32> {
    Var { v: AtomicI32::new(0), forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<AtomicI32> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut i32) = self.v.load(Ordering::SeqCst);
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    *self.v.get_mut() = *(buffer as *mut i32);
  }

  fn len(&self) -> i32 {
    4
  }
}

impl VarProps<i32> for Var<AtomicI32> {
  fn get(&self) -> i32 {
    match &self.forced {
      Some(f) => f.load(Ordering::SeqCst),
      None => self.v.load(Ordering::SeqCst)
    }
  }

  fn set(&mut self, value: i32) {
    let mutval = self.v.get_mut();
    if value == *mutval {
      self.pos = false;
      self.neg = false;
    } else {
      *mutval = value;
      if value > *mutval {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

impl Var<AtomicU32> {
  pub const fn new() -> Var<AtomicU32> {
    Var { v: AtomicU32::new(0), forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<AtomicU32> {
unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u32) = self.v.load(Ordering::SeqCst);
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    *self.v.get_mut() = *(buffer as *mut u32);
  }

  fn len(&self) -> i32 {
    4
  }
}

impl VarProps<u32> for Var<AtomicU32> {
  fn get(&self) -> u32 {
    match &self.forced {
      Some(f) => f.load(Ordering::SeqCst),
      None => self.v.load(Ordering::SeqCst)
    }
  }

  fn set(&mut self, value: u32) {
    let mutval = self.v.get_mut();
    if value == *mutval {
      self.pos = false;
      self.neg = false;
    } else {
      *mutval = value;
      if value > *mutval {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

impl Var<AtomicI16> {
  pub const fn new() -> Var<AtomicI16> {
    Var { v: AtomicI16::new(0), forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<AtomicI16> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut i16) = self.v.load(Ordering::SeqCst);
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    *self.v.get_mut() = *(buffer as *mut i16);
  }

  fn len(&self) -> i32 {
    2
  }
}

impl VarProps<i16> for Var<AtomicI16> {
  fn get(&self) -> i16 {
    match &self.forced {
      Some(f) => f.load(Ordering::SeqCst),
      None => self.v.load(Ordering::SeqCst)
    }
  }

  fn set(&mut self, value: i16) {
    let mutval = self.v.get_mut();
    if value == *mutval {
      self.pos = false;
      self.neg = false;
    } else {
      *mutval = value;
      if value > *mutval {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

impl Var<AtomicU16> {
  pub const fn new() -> Var<AtomicU16> {
    Var { v: AtomicU16::new(0), forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<AtomicU16> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u16) = self.v.load(Ordering::SeqCst);
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    *self.v.get_mut() = *(buffer as *mut u16);
  }

  fn len(&self) -> i32 {
    2
  }
}

impl VarProps<u16> for Var<AtomicU16> {
  fn get(&self) -> u16 {
    match &self.forced {
      Some(f) => f.load(Ordering::SeqCst),
      None => self.v.load(Ordering::SeqCst)
    }
  }

  fn set(&mut self, value: u16) {
    let mutval = self.v.get_mut();
    if value == *mutval {
      self.pos = false;
      self.neg = false;
    } else {
      *mutval = value;
      if value > *mutval {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

impl Var<AtomicI8> {
  pub const fn new() -> Var<AtomicI8> {
    Var { v: AtomicI8::new(0), forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<AtomicI8> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut i8) = self.v.load(Ordering::SeqCst);
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    *self.v.get_mut() = *(buffer as *mut i8);
  }

  fn len(&self) -> i32 {
    1
  }
}

impl VarProps<i8> for Var<AtomicI8> {
  fn get(&self) -> i8 {
    match &self.forced {
      Some(f) => f.load(Ordering::SeqCst),
      None => self.v.load(Ordering::SeqCst)
    }
  }

  fn set(&mut self, value: i8) {
    let mutval = self.v.get_mut();
    if value == *mutval {
      self.pos = false;
      self.neg = false;
    } else {
      *mutval = value;
      if value > *mutval {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

impl Var<AtomicU8> {
  pub const fn new() -> Var<AtomicU8> {
    Var { v: AtomicU8::new(0), forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<AtomicU8> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u8) = self.v.load(Ordering::SeqCst);
  }

  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    *self.v.get_mut() = *buffer;
  }

  fn len(&self) -> i32 {
    1
  }
}

impl VarProps<u8> for Var<AtomicU8> {
  fn get(&self) -> u8 {
    match &self.forced {
      Some(f) => f.load(Ordering::SeqCst),
      None => self.v.load(Ordering::SeqCst)
    }
  }

  fn set(&mut self, value: u8) {
    let mutval = self.v.get_mut();
    if value == *mutval {
      self.pos = false;
      self.neg = false;
    } else {
      *mutval = value;
      if value > *mutval {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

impl Var<AtomicBool> {
  pub const fn new() -> Var<AtomicBool> {
    Var { v: AtomicBool::new(false), forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<AtomicBool> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut bool) = self.v.load(Ordering::SeqCst);
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    *self.v.get_mut() = *(buffer as *mut bool);
  }

  fn len(&self) -> i32 {
    4
  }
}

impl VarProps<bool> for Var<AtomicBool> {
  fn get(&self) -> bool {
    match &self.forced {
      Some(f) => f.load(Ordering::SeqCst),
      None => self.v.load(Ordering::SeqCst)
    }
  }

  fn set(&mut self, value: bool) {
    let mutval = self.v.get_mut();
    if value == *mutval {
      self.pos = false;
      self.neg = false;
    } else {
      *mutval = value;
      if value == true {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

/////////////////////////////////
//Simple Type implementations 
////////////////////////////////

// ********** i64 *********** //
impl Var<i64> {
  pub const fn new() -> Var<i64> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<i64> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut i64) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut i64);
  }

  fn len(&self) -> i32 {
    8
  }
}

impl VarProps<i64> for Var<i64> {
  fn get(&self) -> i64 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: i64) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** u64 *********** //
impl Var<u64> {
  pub const fn new() -> Var<u64> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<u64> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u64) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut u64);
  }

  fn len(&self) -> i32 {
    8
  }
}

impl VarProps<u64> for Var<u64> {
  fn get(&self) -> u64 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: u64) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** i32 *********** //
impl Var<i32> {
  pub const fn new() -> Var<i32> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<i32> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut i32) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut i32);
  }

  fn len(&self) -> i32 {
    4
  }
}

impl VarProps<i32> for Var<i32> {
  fn get(&self) -> i32 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: i32) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** u32 *********** //
impl Var<u32> {
  pub const fn new() -> Var<u32> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<u32> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u32) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut u32);
  }

  fn len(&self) -> i32 {
    4
  }
}

impl VarProps<u32> for Var<u32> {
  fn get(&self) -> u32 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: u32) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** i16 *********** //
impl Var<i16> {
  pub const fn new() -> Var<i16> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<i16> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut i16) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut i16);
  }

  fn len(&self) -> i32 {
    2
  }
}

impl VarProps<i16> for Var<i16> {
  fn get(&self) -> i16 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: i16) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** u16 *********** //
impl Var<u16> {
  pub const fn new() -> Var<u16> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<u16> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u16) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut u16);
  }

  fn len(&self) -> i32 {
    2
  }
}

impl VarProps<u16> for Var<u16> {
  fn get(&self) -> u16 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: u16) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** i8 *********** //
impl Var<i8> {
  pub const fn new() -> Var<i8> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<i8> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut i8) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut i8);
  }

  fn len(&self) -> i32 {
    1
  }
}

impl VarProps<i8> for Var<i8> {
  fn get(&self) -> i8 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: i8) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** u8 *********** //
impl Var<u8> {
  pub const fn new() -> Var<u8> {
    Var { v: 0, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<u8> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u8) = self.v;
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut u8);
  }

  fn len(&self) -> i32 {
    1
  }
}

impl VarProps<u8> for Var<u8> {
  fn get(&self) -> u8 {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: u8) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value > self.v {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}

// ********** bool *********** //
impl Var<bool> {
  pub const fn new() -> Var<bool> {
    Var { v: false, forced: None, pos: false, neg: false }
  } 
}

impl MemVar for Var<bool> {
  unsafe fn to_buffer(&self, buffer: *mut u8) {
    *(buffer as *mut u8) = match self.v { true => 1, false => 0 };
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8) {
    self.v = *(buffer as *mut u8) > 0;
  }

  fn len(&self) -> i32 {
    1
  }
}

impl VarProps<bool> for Var<bool> {
  fn get(&self) -> bool {
    match self.forced {
      Some(f) => f,
      None => self.v
    }
  }

  fn set(&mut self, value: bool) {
    if value == self.v {
      self.pos = false;
      self.neg = false;
    } else {
      self.v = value;
      if value == true {
        self.pos = true;
        self.neg = false;
      } else {
        self.pos = false;
        self.neg = true;
      }
    }
  }
}