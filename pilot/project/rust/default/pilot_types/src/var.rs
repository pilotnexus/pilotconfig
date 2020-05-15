pub trait MemVar: Sync {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32;
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32;
  unsafe fn is_dirty(&self) -> bool;
  unsafe fn clear_dirty_or_update(&mut self);
  unsafe fn get_subscribed(&self) -> bool;
  unsafe fn set_subscribed(&mut self, value: bool);
}

pub trait VarProps<T> {
  fn get(&self) -> T; 
  fn set(&mut self, value: T);
}

pub trait VarChange {
  fn pos(&self) -> bool;
  fn neg(&self) -> bool;
  fn posorneg(&self) -> bool;
}

pub struct Var<T: Default> {
  v: T,
  changed: T,
  forced: Option<T>,
  dirty: bool,
  subscribed: bool,
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

  fn posorneg(&self) -> bool {
    self.pos || self.neg
  }
}

/////////////////////////////////
//Simple Type implementations 
////////////////////////////////

// ********** i64 *********** //
impl Var<i64> {
  pub const fn new() -> Var<i64> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<i64> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut i64) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };

    8
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut i64),
      1 => self.changed = *(buffer as *mut i64),
      2 => self.forced = Some(*(buffer as *mut i64)),
      _ => self.v = *(buffer as *mut i64),
    };
    8
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
    self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** u64 *********** //
impl Var<u64> {
  pub const fn new() -> Var<u64> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<u64> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut u64) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };
    8
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut u64),
      1 => self.changed = *(buffer as *mut u64),
      2 => self.forced = Some(*(buffer as *mut u64)),
      _ => self.v = *(buffer as *mut u64),
    };
    8
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
    self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** i32 *********** //
impl Var<i32> {
  pub const fn new() -> Var<i32> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<i32> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut i32) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };
    4
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut i32),
      1 => self.changed = *(buffer as *mut i32),
      2 => self.forced = Some(*(buffer as *mut i32)),
      _ => self.v = *(buffer as *mut i32),
    };
    4
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
    self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** u32 *********** //
impl Var<u32> {
  pub const fn new() -> Var<u32> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<u32> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut u32) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };
    4
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut u32),
      1 => self.changed = *(buffer as *mut u32),
      2 => self.forced = Some(*(buffer as *mut u32)),
      _ => self.v = *(buffer as *mut u32),
    };
    4
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
    self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** i16 *********** //
impl Var<i16> {
  pub const fn new() -> Var<i16> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<i16> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut i16) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };
    2
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut i16),
      1 => self.changed = *(buffer as *mut i16),
      2 => self.forced = Some(*(buffer as *mut i16)),
      _ => self.v = *(buffer as *mut i16),
    };
    2
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
    self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** u16 *********** //
impl Var<u16> {
  pub const fn new() -> Var<u16> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<u16> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut u16) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };
    2
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut u16),
      1 => self.changed = *(buffer as *mut u16),
      2 => self.forced = Some(*(buffer as *mut u16)),
      _ => self.v = *(buffer as *mut u16),
    };
    2
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
    self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** i8 *********** //
impl Var<i8> {
  pub const fn new() -> Var<i8> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<i8> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut i8) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };
    1
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut i8),
      1 => self.changed = *(buffer as *mut i8),
      2 => self.forced = Some(*(buffer as *mut i8)),
      _ => self.v = *(buffer as *mut i8),
    };
    1
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
      self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** u8 *********** //
impl Var<u8> {
  pub const fn new() -> Var<u8> {
    Var { v: 0, forced: None, pos: false, neg: false, subscribed: false, changed: 0, dirty: false }
  } 
}

impl MemVar for Var<u8> {
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut u8) = match subvalue {
      0 => self.v,
      1 => self.changed,
      2 => match self.forced {
          Some(v) => v,
          None => 0
      },
      _ => self.v,
    };
    1
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut u8),
      1 => self.changed = *(buffer as *mut u8),
      2 => self.forced = Some(*(buffer as *mut u8)),
      _ => self.v = *(buffer as *mut u8),
    };
    1
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
      self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}

// ********** bool *********** //
impl Var<bool> {
  pub const fn new() -> Var<bool> {
    Var { v: false, forced: None, pos: false, neg: false, subscribed: false, changed: false, dirty: false }
  } 
}

impl MemVar for Var<bool> {
  
  unsafe fn to_buffer(&mut self, buffer: *mut u8, subvalue: u8) -> i32 {
    *(buffer as *mut u8) = match subvalue {
      0 => match self.v { true => 1, false => 0 },
      1 => match self.changed { true => 1, false => 0 },
      2 => match self.forced {
          Some(v) => match v { true => 1, false => 0},
          None => 0
      },
      _ => match self.v { true => 1, false => 0 }
    };
    1
  }
  
  unsafe fn from_buffer(&mut self, buffer: *const u8, subvalue: u8) -> i32{
    match subvalue {
      0 => self.v = *(buffer as *mut u8) > 0,
      1 => self.changed = *(buffer as *mut u8) > 0,
      2 => self.forced = Some(*(buffer as *mut u8)>0),
      _ => self.v = *(buffer as *mut u8) > 0,
    };
    1
  }

  unsafe fn is_dirty(&self) -> bool {
    self.dirty
  }

  unsafe fn clear_dirty_or_update(&mut self) {
    if self.v != self.changed {
      self.changed = self.v;
    } else {
      self.dirty = false;
    }
  }

  unsafe fn get_subscribed(&self) -> bool {
    self.subscribed
  }

  unsafe fn set_subscribed(&mut self, value: bool) {
    self.subscribed = value;
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
      if !self.dirty && self.changed != value {
        self.changed = value;
        self.dirty = true;
      }
    }
  }
}