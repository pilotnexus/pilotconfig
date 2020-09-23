use core::task::{RawWaker, RawWakerVTable};
use futures::{future, Future};

/// Becomes ready as soon as one of the given futures becomes ready.
pub async fn either(fut1: impl Future<Output = ()>, fut2: impl Future<Output = ()>) {
    futures::pin_mut!(fut1);
    futures::pin_mut!(fut2);
    future::select(fut1, fut2).await;
}

/// Creates an RawWaker that does nothing.
pub fn raw_waker() -> RawWaker {
    fn clone(_: *const ()) -> RawWaker {
        raw_waker()
    }
    fn wake(_: *const ()) {}
    fn drop(_: *const ()) {}

    let vtable = &RawWakerVTable::new(clone, wake, wake, drop);
    RawWaker::new(0 as *const (), vtable)
}
