use crate::sync::SyncCell;
use core::{
    future::Future,
    pin::Pin,
    task::{Context, Poll},
};

pub trait MemVar: Sync {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32;
    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32;
    unsafe fn is_dirty(&self) -> bool;
    unsafe fn clear_dirty_or_update(&self);
    unsafe fn get_subscribed(&self) -> bool;
    unsafe fn set_subscribed(&self, value: bool);
}

pub trait VarProps<T> {
    fn get(&self) -> T;
    fn set(&self, value: T);
}

pub trait VarChange {
    fn pos(&self) -> bool;
    fn neg(&self) -> bool;
    fn posorneg(&self) -> bool;

    fn wait_pos(&self) -> WaitChange<'_, Self>
    where
        Self: Sized,
    {
        WaitChange {
            var: self,
            event: Event::Pos,
        }
    }

    fn wait_neg(&self) -> WaitChange<'_, Self>
    where
        Self: Sized,
    {
        WaitChange {
            var: self,
            event: Event::Neg,
        }
    }

    fn wait_posorneg(&self) -> WaitChange<'_, Self>
    where
        Self: Sized,
    {
        WaitChange {
            var: self,
            event: Event::PosOrNeg,
        }
    }
}

#[derive(Debug, Copy, Clone, Eq, PartialEq)]
enum Event {
    Pos,
    Neg,
    PosOrNeg,
}

pub struct WaitChange<'a, V> {
    var: &'a V,
    event: Event,
}

impl<V> Future for WaitChange<'_, V>
where
    V: VarChange,
{
    type Output = ();

    fn poll(self: Pin<&mut Self>, _cx: &mut Context) -> Poll<Self::Output> {
        let &Self { var, event } = self.into_ref().get_ref();
        let finished = match event {
            Event::Pos => var.pos(),
            Event::Neg => var.neg(),
            Event::PosOrNeg => var.pos() || var.neg(),
        };
        if finished {
            Poll::Ready(())
        } else {
            Poll::Pending
        }
    }
}

pub struct Var<T: Default> {
    v: SyncCell<T>,
    changed: SyncCell<T>,
    forced: SyncCell<Option<T>>,
    dirty: SyncCell<bool>,
    subscribed: SyncCell<bool>,
    pos: SyncCell<bool>,
    neg: SyncCell<bool>,
}

impl<T: Default> VarChange for Var<T> {
    fn pos(&self) -> bool {
        self.pos.get()
    }

    fn neg(&self) -> bool {
        self.neg.get()
    }

    fn posorneg(&self) -> bool {
        self.pos.get() || self.neg.get()
    }
}

/////////////////////////////////
//Simple Type implementations
////////////////////////////////

// ********** i64 *********** //
impl Var<i64> {
    pub const fn new() -> Var<i64> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<i64> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut i64) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };

        8
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut i64)),
            1 => self.changed.set(*(buffer as *mut i64)),
            2 => self.forced.set(Some(*(buffer as *mut i64))),
            _ => self.set(*(buffer as *mut i64)),
        };
        8
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        let v = self.v.get();
        if v != self.changed.get() {
            self.changed.set(v);
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<i64> for Var<i64> {
    fn get(&self) -> i64 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: i64) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** u64 *********** //
impl Var<u64> {
    pub const fn new() -> Var<u64> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<u64> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut u64) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };
        8
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut u64)),
            1 => self.changed.set(*(buffer as *mut u64)),
            2 => self.forced.set(Some(*(buffer as *mut u64))),
            _ => self.set(*(buffer as *mut u64)),
        };
        8
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<u64> for Var<u64> {
    fn get(&self) -> u64 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: u64) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** i32 *********** //
impl Var<i32> {
    pub const fn new() -> Var<i32> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<i32> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut i32) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };
        4
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut i32)),
            1 => self.changed.set(*(buffer as *mut i32)),
            2 => self.forced.set(Some(*(buffer as *mut i32))),
            _ => self.set(*(buffer as *mut i32)),
        };
        4
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<i32> for Var<i32> {
    fn get(&self) -> i32 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: i32) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** u32 *********** //
impl Var<u32> {
    pub const fn new() -> Var<u32> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<u32> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut u32) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };
        4
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut u32)),
            1 => self.changed.set(*(buffer as *mut u32)),
            2 => self.forced.set(Some(*(buffer as *mut u32))),
            _ => self.set(*(buffer as *mut u32)),
        };
        4
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<u32> for Var<u32> {
    fn get(&self) -> u32 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: u32) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** i16 *********** //
impl Var<i16> {
    pub const fn new() -> Var<i16> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<i16> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut i16) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };
        2
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut i16)),
            1 => self.changed.set(*(buffer as *mut i16)),
            2 => self.forced.set(Some(*(buffer as *mut i16))),
            _ => self.set(*(buffer as *mut i16)),
        };
        2
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<i16> for Var<i16> {
    fn get(&self) -> i16 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: i16) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** u16 *********** //
impl Var<u16> {
    pub const fn new() -> Var<u16> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<u16> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut u16) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };
        2
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut u16)),
            1 => self.changed.set(*(buffer as *mut u16)),
            2 => self.forced.set(Some(*(buffer as *mut u16))),
            _ => self.set(*(buffer as *mut u16)),
        };
        2
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<u16> for Var<u16> {
    fn get(&self) -> u16 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: u16) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** i8 *********** //
impl Var<i8> {
    pub const fn new() -> Var<i8> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<i8> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut i8) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };
        1
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut i8)),
            1 => self.changed.set(*(buffer as *mut i8)),
            2 => self.forced.set(Some(*(buffer as *mut i8))),
            _ => self.set(*(buffer as *mut i8)),
        };
        1
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<i8> for Var<i8> {
    fn get(&self) -> i8 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: i8) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** u8 *********** //
impl Var<u8> {
    pub const fn new() -> Var<u8> {
        Var {
            v: SyncCell::new(0),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(0),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<u8> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut u8) = match subvalue {
            0 => self.get(),
            1 => self.changed.get(),
            2 => match self.forced.get() {
                Some(v) => v,
                None => 0,
            },
            _ => self.get(),
        };
        1
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut u8)),
            1 => self.changed.set(*(buffer as *mut u8)),
            2 => self.forced.set(Some(*(buffer as *mut u8))),
            _ => self.set(*(buffer as *mut u8)),
        };
        1
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<u8> for Var<u8> {
    fn get(&self) -> u8 {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: u8) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value > self.v.get() {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}

// ********** bool *********** //
impl Var<bool> {
    pub const fn new() -> Var<bool> {
        Var {
            v: SyncCell::new(false),
            forced: SyncCell::new(None),
            pos: SyncCell::new(false),
            neg: SyncCell::new(false),
            subscribed: SyncCell::new(false),
            changed: SyncCell::new(false),
            dirty: SyncCell::new(false),
        }
    }
}

impl MemVar for Var<bool> {
    unsafe fn to_buffer(&self, buffer: *mut u8, subvalue: u8) -> i32 {
        *(buffer as *mut u8) = match subvalue {
            0 => match self.get() {
                true => 1,
                false => 0,
            },
            1 => match self.changed.get() {
                true => 1,
                false => 0,
            },
            2 => match self.forced.get() {
                Some(v) => match v {
                    true => 1,
                    false => 0,
                },
                None => 0,
            },
            _ => match self.get() {
                true => 1,
                false => 0,
            },
        };
        1
    }

    unsafe fn from_buffer(&self, buffer: *const u8, subvalue: u8) -> i32 {
        match subvalue {
            0 => self.set(*(buffer as *mut u8) > 0),
            1 => self.changed.set(*(buffer as *mut u8) > 0),
            2 => self.forced.set(Some(*(buffer as *mut u8) > 0)),
            _ => self.set(*(buffer as *mut u8) > 0),
        };
        1
    }

    unsafe fn is_dirty(&self) -> bool {
        self.dirty.get()
    }

    unsafe fn clear_dirty_or_update(&self) {
        if self.v.get() != self.changed.get() {
            self.changed.set(self.v.get());
        } else {
            self.dirty.set(false);
        }
    }

    unsafe fn get_subscribed(&self) -> bool {
        self.subscribed.get()
    }

    unsafe fn set_subscribed(&self, value: bool) {
        self.subscribed.set(value);
    }
}

impl VarProps<bool> for Var<bool> {
    fn get(&self) -> bool {
        match self.forced.get() {
            Some(f) => f,
            None => self.v.get(),
        }
    }

    fn set(&self, value: bool) {
        if value == self.v.get() {
            self.pos.set(false);
            self.neg.set(false);
        } else {
            self.v.set(value);
            if value == true {
                self.pos.set(true);
                self.neg.set(false);
            } else {
                self.pos.set(false);
                self.neg.set(true);
            }
            if !self.dirty.get() && self.changed.get() != value {
                self.changed.set(value);
                self.dirty.set(true);
            }
        }
    }
}
