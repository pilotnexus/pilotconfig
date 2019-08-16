import os
import json
import lazy_import
import importlib.util

#from collections import defaultdict
defaultdict = lazy_import.lazy_callable("collections.defaultdict")
fnmatch = lazy_import.lazy_module("fnmatch")

class Plc():
  targetdevice = { 'flashaddress': 0x08000000, 'ramaddress': 0x20000000, 'bitbandaddress': 0x22000000, 'flash': 512, 'ram': 48 } # STM32F103CBxx
  model = {}
  config = {}
  compiler = None
  helpers = None

  def __init__(self, args, model, config, compiler, helpers):
    self.config = config
    self.model = model
    self.compiler = compiler
    self.helpers = helpers


    mem_modules = self.init_memory_mapped_modules()

  def init_memory_mapped_modules(self):
    memmodules = self.config["modules"]
    if 'plugins' in self.config:
      memmodules = memmodules + self.config['plugins']

    # Initialize device data 
    # create device properties
    # spec - hw specs (I/Os, GPIO banks, Interrupts, etc)
    # name - name to be used in code gen
    # absaddress - absolute RAM address in MCU
    # NOTE that 'Slot' in spec is zero based whereas 'slot' is 1 based.
    self.config['plc_memory_size'] = 0
    for mod in memmodules:
      dev = {}
      mod['device'] = dev
      dev['hw'] = next(iter(next(iter([v for k, v in self.model.items() if isinstance(v, list) and 
               [x for x in v if k != 'Modules' and 'Slot' in x and 'slot' in mod and x['Slot']+1 == int(mod['slot'])]]))))
      dev['name'] = "m{}_{}".format(mod['slot'], mod['fid']) # TODO naming for plugins
      dev['slot'] = mod['slot']
      dev['index'] = int(mod['slot']) - 1
      dev['spec'] = self.getDevice(mod)
      if dev['spec'] == None:
        print("Warning: No device found for module firmware {}, this module firmware does not have PLC support".format(mod['fid']))
      else:
        self.config['plc_memory_size'] = self.config['plc_memory_size'] + dev['spec'].size
        dev['spec'].compile()

    # memory size in kb
    plcmemsize = int((self.config['plc_memory_size']  + 1024 - 1) / 1024)

    # memory mapped modules
    self.model['memmodules'] = memmodules 

    # generate data for linker script
    self.model['memory'] = self.targetdevice
    self.model['ld'] = { 'flashaddress': hex(self.targetdevice['flashaddress']),
                          'plcaddress': hex(self.targetdevice['ramaddress']),
                          'ramaddress': hex(self.targetdevice['ramaddress'] + (plcmemsize * 1024)),
                          'flash': str(self.targetdevice['flash']) + 'k', 
                          'ram': str(int(self.targetdevice['ram']) - plcmemsize) + 'k',
                          'plc': str(int(plcmemsize)) + 'k'}
    
  def getDevice(self, module):
    devicefile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'devices', module['fid'] + '.py') 
    if os.path.isfile(devicefile):
      spec = importlib.util.spec_from_file_location("module.name", devicefile)
      device = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(device)
      return device.getDevice(self.model, module, self.compiler, self.helpers)
    return None