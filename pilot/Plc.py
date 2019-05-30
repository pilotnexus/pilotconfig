import os
import json
import lazy_import
import importlib.util

#from collections import defaultdict
defaultdict = lazy_import.lazy_callable("collections.defaultdict")
fnmatch = lazy_import.lazy_module("fnmatch")

class Plc():
  targetdevice = { 'flashaddress': 0x08000000, 'ramaddress': 0x20000000, 'flash': 512, 'ram': 48 } # STM32F103CBxx
  model = {}
  config = {}
  compiler = None

  def __init__(self, args, config, compiler):
    self.config = config
    self.compiler = compiler
    #if no source path parameter is given try the environment var
    if args.source == None:
      try:
        source = os.path.join(args.workdir, 'basefw/stm') if args.workdir else './basefw/stm'
        if os.path.isdir(source):
          args.source = source
        else: 
          args.source = os.environ['PILOT_SOURCE']
      except:
        print("No parameter source directory given, no './basefw/stm' folder found and no PILOT_SOURCE environment variable defined, exiting")
        exit(1) 

    with open(os.path.join(os.path.abspath(args.source), 'stmmodel.json')) as stmmodelfile:
      self.model.update(json.load(stmmodelfile))
      self.model['devices'] = []

    mem_modules = self.init_memory_mapped_modules()

  def init_memory_mapped_modules(self):
    memmodules = self.config["modules"]
    if 'plugins' in self.config:
      memmodules = memmodules + self.config['plugins']

    # generate device data
    for mod in memmodules:
      mod['device'] = self.getDevice(mod)
      if mod['device'] == None:
        print("Warning: No device found for module firmware {}, this module firmware does not have PLC support".format(mod['fid']))
      else:
        self.model['devices'].append(mod)

    # Initialize device data 
    # create device properties
    # spec - hw specs (I/Os, GPIO banks, Interrupts, etc)
    # name - name to be used in code gen
    # absaddress - absolute RAM address in MCU
    # NOTE that 'Slot' in spec is zero based whereas 'slot' is 1 based.
    self.config['plc_memory_size'] = 0
    for dev in self.model['devices']:
      dev['spec'] = next(iter(next(iter([v for k, v in self.model.items() if isinstance(v, list) and 
               [x for x in v if k != 'Modules' and 'Slot' in x and 'slot' in dev and x['Slot']+1 == int(dev['slot'])]]))))
      dev['name'] = "m{}_{}".format(dev['slot'], dev['fid']) # TODO naming for plugins
      dev['absaddress'] = self.targetdevice['ramaddress'] + self.config['plc_memory_size']
      self.config['plc_memory_size'] = self.config['plc_memory_size'] + dev['device'].size

    # memory size in kb
    plcmemsize = int((self.config['plc_memory_size']  + 1024 - 1) / 1024)
    
    # generate data for linker script
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
      return device.getDevice(self.model, module, self.compiler)
    return None