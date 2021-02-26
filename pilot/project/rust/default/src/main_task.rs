use crate::{async_util::either, print, println, time, VARS};
use futures::future::{self, Either};
use pilot_types::var::{VarChange, VarProps, SubscribeMode};
use time::{current_time, wait_next_cycle, wait_until, SECOND};

pub async fn main_task() {

    // Application loop
    loop {
      //add your application code here
        
      //you can remove this, if you have something to await
      //in the application loop
      //(otherwise the loop would hang)
      wait_next_cycle().await; 
    }
}
