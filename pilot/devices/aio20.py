def getDevice(model, module, compiler, helpers):
  return AIO20Device(model, module, compiler, helpers)

def toGPIO(this, items):
  return 'GPIO' + chr(items+65)

def default_config():
  return {}

class AIO20Device():
  size = 1
  ctype = 'uint16_t[16]'
  rusttype = 'u8'
  include = ['aio20.h'] 
  init_source = ''
  dev_to_mem_source = ''
  mem_to_dev_source = ''
  mem_doc = {
    "read": [
    {
      "byte": 2,
      "bit": 0,
      "length": 16,
      "name": "aio0",
      "desc": "Analog I/O 0",
      "signed": False
    },
    {
      "byte": 0,
      "bit": 0,
      "length": 16,
      "name": "aio1",
      "desc": "Analog I/O 1",
      "signed": False
    },
    {
      "byte": 6,
      "bit": 0,
      "length": 16,
      "name": "aio2",
      "description": "Analog I/O 2",
      "signed": False
    },
    {
      "byte": 4,
      "bit": 0,
      "length": 16,
      "name": "aio3",
      "desc": "Analog I/O 3",
      "signed": False
    },
    {
      "byte": 12,
      "bit": 0,
      "length": 16,
      "name": "aio4",
      "desc": "Analog I/O 4",
      "signed": False
    },
    {
      "byte": 10,
      "bit": 0,
      "length": 16,
      "name": "aio5",
      "desc": "Analog I/O 5",
      "signed": False
    },
    {
      "byte": 18,
      "bit": 0,
      "length": 16,
      "name": "aio6",
      "desc": "Analog I/O 6",
      "signed": False
    },
    {
      "byte": 16,
      "bit": 0,
      "length": 16,
      "name": "aio7",
      "desc": "Analog I/O 7",
      "signed": False
    },
    {
      "byte": 22,
      "bit": 0,
      "length": 16,
      "name": "aio8",
      "desc": "Analog I/O 8",
      "signed": False
    },
    {
      "byte": 20,
      "bit": 0,
      "length": 16,
      "name": "aio9",
      "desc": "Analog I/O 9",
      "signed": False
    },
    {
      "byte": 28,
      "bit": 0,
      "length": 16,
      "name": "aio10",
      "desc": "Analog I/O 10",
      "signed": False
    },
    {
      "byte": 26,
      "bit": 0,
      "length": 16,
      "name": "aio11",
      "desc": "Analog I/O 11",
      "signed": False
    },
    {
      "byte": 32,
      "bit": 0,
      "length": 16,
      "name": "aio12",
      "desc": "Analog I/O 12",
      "signed": False
    },
    {
      "byte": 30,
      "bit": 0,
      "length": 16,
      "name": "aio13",
      "desc": "Analog I/O 13",
      "signed": False
    },
    {
      "byte": 36,
      "bit": 0,
      "length": 16,
      "name": "aio14",
      "desc": "Analog I/O 14",
      "signed": False
    },
    {
      "byte": 38,
      "bit": 0,
      "length": 16,
      "name": "aio15",
      "desc": "Analog I/O 15",
      "signed": False
    },
    {
      "byte": 8,
      "bit": 0,
      "length": 16,
      "name": "r1",
      "desc": "Analog Frontend 1 Id Resistor",
      "signed": False
    },
    {
      "byte": 14,
      "bit": 0,
      "length": 16,
      "name": "r2",
      "desc": "Analog Frontend 2 Id Resistor",
      "signed": False
    },
    {
      "byte": 24,
      "bit": 0,
      "length": 16,
      "name": "r3",
      "desc": "Analog Frontend 3 Id Resistor",
      "signed": False
    },
    {
      "byte": 34,
      "bit": 0,
      "length": 16,
      "name": "r4",
      "desc": "Analog Frontend 4 Id Resistor",
      "signed": False
    }
  ],
  "write": []
  }

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
} aio20_t;
"""},
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
}
""" }
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
  get_module_info()->m{{device.index}}_status |= single_ended_adc_read_all({{device.index}}, (uint8_t *) &plc_mem_devices.m{{device.slot}}); 
  """

    init_str = "  // initialization for device {{device.name}}\n  int32_t status = 1;\n  if (aio20_get_device_id({{device.index}}) == 0x424)\n  {\n    status = 0;\n    AIO20_init({{device.index}});\n  }\n  return status;"
    init_template = self.compiler.compile(init_str)
    dev_to_mem_template = self.compiler.compile(dev_to_mem_str)

    self.dev_to_mem_source = dev_to_mem_template(self.module, self.helpers)
    self.init_source = init_template(self.module, self.helpers)

