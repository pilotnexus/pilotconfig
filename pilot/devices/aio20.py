def getDevice(model, module, compiler, helpers):
  return I8Device(model, module, compiler, helpers)

def toGPIO(this, items):
  return 'GPIO' + chr(items+65)

def default_config():
  return {}

class I8Device():
  size = 1
  ctype = 'uint16_t[16]'
  rusttype = 'u8'
  include = ['aio20.h'] 
  init_source = ''
  dev_to_mem_source = ''
  mem_to_dev_source = ''
  mem_doc = []

  decl = {
    'c': { 'name': 'aio20_t', 'decl': """typedef struct { 
  uint16_t aio1;
  uint16_t aio0;
  uint16_t aio3;
  uint16_t aio2;
  uint16_t r1;
  uint16_t aio5;
  uint16_t aio4;
  uint16_t r2;
  uint16_t aio7;
  uint16_t aio6;
  uint16_t aio9;
  uint16_t aio8;
  uint16_t r3;
  uint16_t aio11;
  uint16_t aio10;
  uint16_t aio13;
  uint16_t aio12;
  uint16_t r4;
  uint16_t aio14;
  uint16_t aio15;
} aio20_t;"""},
    'rust': { 'name': 'Aio20', 'decl': """#[repr(C)]
pub struct Aio20 { 
  pub aio1: u16,
  pub aio0: u16,
  pub aio3: u16,
  pub aio2: u16,
  r1: u16,
  pub aio5: u16,
  pub aio4: u16,
  r2: u16,
  pub aio7: u16,
  pub aio6: u16,
  pub aio9: u16,
  pub aio8: u16,
  r3: u16,
  pub aio11: u16,
  pub aio10: u16,
  pub aio13: u16,
  pub aio12: u16,
  r4: u16,
  pub aio14: u16,
  pub aio15: u16,
}""" }
  }

  module = None
  model = None
  compiler = None
  helpers = None 
  
  def __init__(self, model, module, compiler, helpers):
    self.size = 1
    self.module = module
    self.helpers = {'gpio': toGPIO, **helpers}
    self.compiler = compiler
    self.model = model

  def compile(self):
    dev_to_mem_str = """// source for device {{device.name}}
  single_ended_adc_read_all({{device.index}}, (uint8_t *) &plc_mem_devices.m{{device.slot}}); 
  """
    dev_to_mem_template = self.compiler.compile(dev_to_mem_str)
    self.dev_to_mem_source = dev_to_mem_template(self.module, self.helpers)