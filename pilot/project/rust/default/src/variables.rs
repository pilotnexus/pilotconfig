#![macro_use]
extern crate pilot_macro;
extern crate pilot_types;

use pilot_macro::*;

#[allow(unused_imports)]
use pilot_types::var::*;

#[derive(PilotBindings)]
pub struct PlcVars {
    /* Example for hieracical var structure */
    #[bind_read]
    pub inputs: IOModule,
    #[bind_write]
    pub outputs: IOModule,

    /* Example usage for a boolean input variable (assuming 16 Digital IO Module in module slot 4) */
    #[bind_read(m1.0)]
    pub i8_0: Var<bool>,

    #[bind_write(m2.0)]
    pub o8_0: Var<bool>,

    #[bind_read(m3.0)]
    pub demo_i0: Var<bool>,
    #[bind_read(m3.1)]
    pub demo_i1: Var<bool>,
    #[bind_read(m3.2)]
    pub demo_i2: Var<bool>,
    #[bind_read(m3.3)]
    pub demo_i3: Var<bool>,

    #[bind_write(m3.4)]
    pub demo_o0: Var<bool>,
    #[bind_write(m3.5)]
    pub demo_o1: Var<bool>,
    #[bind_write(m3.6)]
    pub demo_o2: Var<bool>,
    #[bind_write(m3.7)]
    pub demo_o3: Var<bool>,

    //unbound variables
    pub start: Var<bool>,
}

#[derive(PilotBindings)]
pub struct IOModule {
    #[bind_read(m1.0)]
    #[bind_write(m2.0)]
    pub io0: Var<bool>,
    #[bind_write(m2.1)]
    #[bind_read(m1.1)]
    pub io1: Var<bool>,
    #[bind_read(m1.2)]
    #[bind_write(m2.2)]
    pub io2: Var<bool>,
    #[bind_read(m1.3)]
    #[bind_write(m2.3)]
    pub io3: Var<bool>,
    #[bind_read(m1.4)]
    #[bind_write(m2.4)]
    pub io4: Var<bool>,
    #[bind_read(m1.5)]
    #[bind_write(m2.5)]
    pub io5: Var<bool>,
    #[bind_read(m1.6)]
    #[bind_write(m2.6)]
    pub io6: Var<bool>,
    #[bind_read(m1.7)]
    #[bind_write(m2.7)]
    pub io7: Var<bool>,
}
