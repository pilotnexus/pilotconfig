import os
import distutils
import json
import yaml
from .sbc import Sbc
from .pilotdriver import PilotDriver
from .pilotserver import PilotServer
from . import helper 
import importlib.util
from colorama import Fore

def download_base_firmware(args):
  modules = {}
  eeproms = {}
  detect_modules = True 
  for mod in range(1, PilotDriver.MODULE_COUNT+1):
    modarg = 'm{}'.format(mod)
    if modarg in args and getattr(args, modarg) is not None:
      detect_modules = False
      eeproms[mod] = {'uid': 0, 'hid': '', 'fid': getattr(args,modarg)}

  if detect_modules:        
    if not args.node:
      print('We need a nodename or IP and username/password (ssh) of the Node you want to configure.')
      args.node = input('node/IP of Node to get Firmware Configuration from: ')

    with Sbc(args) as sbc:
      pilotserver = PilotServer(sbc)
      pilotdriver = PilotDriver(pilotserver, sbc)

      if args.server != None:
        pilotserver.pilot_server = args.server

      modules, success = pilotdriver.load_pilot_defs()
  else:
    pilotserver = PilotServer(None)
    pilotdriver = PilotDriver(pilotserver, None)
    modules, success = pilotdriver.getmodules(eeproms)

  if modules != None:
    for module in modules:
      print('Module {}: {}{}'.format(
          module['module'], Fore.GREEN, module['currentfid_nicename']))
  if pilotdriver.get_firmware(False, os.path.join(args.workdir, 'basefw') if args.workdir else './basefw', True) != 0:
    print(Fore.RED + 'Could not download firmware source!')
    exit(1)


  return modules

def init(args, version):
  use_compiler = None
  print('This will create a new Pilot firmware project in the current folder')

  node_user = args.user
  node_password = args.password

  compilers, _ = helper.get_compilers()

  if args.compiler:
    if next(x for x in compilers if x['name'] == args.compiler) == None:
      print('Could not find compiler {}. Use --show-compilers to get available compilers.'.format(args.compiler))
      return 1 

  if not args.compiler:
    compiler_index = -1
    if (len(compilers) == 0):
      print('No compilers found, exiting')
      return 1
    elif (len(compilers) == 1): #only one compiler available
      compiler_index = 0

    while (compiler_index < 0 or compiler_index > len(compilers)):
      print('Please specify the compiler toolchain to use:')
      for index, compiler in enumerate(compilers):
        print('[{}] {}: {}'.format(index+1, compiler['name'], compiler['description']))
      try:
        compiler_index = int(input('[1-{}]: '.format(len(compilers)))) - 1
      except KeyboardInterrupt:
        exit(1)
      except: pass
    args.compiler = compilers[compiler_index]['name']

  try:
    modules = download_base_firmware(args)
    # create credentials.json
    #cred = {}
    #try:
    #  nodeconf = yaml.load(sbc.getFileContent('/etc/pilot/pilotnode.yml'), Loader=yaml.FullLoader)
    #  node = {}
    #  node['nodeid'] = nodeconf['nodeid']
    #  node['apikey'] = nodeconf['apikey']
    #  node['node'] = args.node
    #  node['user'] = node_user
    #  node['password'] = node_password
    #  cred['nodes'] = [node]
    #except:
    #  print(Fore.YELLOW + 'WARNING: Could not load Node Configuration (pilotnode not configured on target?). Continuing without it.')

    #with open(os.path.join(args.workdir, 'credentials.json') if args.workdir else './credentials.json', 'w') as credfile:
    #  json.dump(cred, credfile)

    # create .pilotfwconfig.json
    config = {}
    config['compiler'] = args.compiler
    config['generated_by'] = "pilot-node v{}".format(version)
    config['modules'] = []

    for mod in modules:
      if mod['currentfid']:
        module = {}
        module['slot'] = mod['module']
        module['fid'] = mod['currentfid']
        module['fid_nicename'] = mod['currentfid_nicename']
        if 'hid' in mod and 'title' in mod and 'subtitle' in mod and 'description' in mod:
          module['hid'] = mod['hid']
          module['title'] = mod['title']
          module['subtitle'] = mod['subtitle']
          module['description'] = mod['description']

        devicefile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'devices', module['fid'] + '.py') 
        if os.path.isfile(devicefile):
          spec = importlib.util.spec_from_file_location("module.name", devicefile)
          device = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(device)
          module['config'] = device.default_config()
        config['modules'].append(module)

    if args.node:
      config['nodes'] = [{'name': 'default', 'node': args.node}]

    with open(os.path.join(args.workdir, '.pilotfwconfig.json') if args.workdir else './.pilotfwconfig.json', 'w') as configfile:
      json.dump(config, configfile)

    # copy default project files
    targetpath = os.path.join(args.workdir) if args.workdir else './'
    distutils.dir_util.copy_tree(os.path.join(os.path.dirname(os.path.realpath(__file__)),'project', args.compiler.lower(), 'default'), targetpath)
  
    print("Project generated")
    #print( """{}
    #├─ src/
    #│  ├─ program.st    /* IEC 61131-3 code */
    #│  └─ *.c, *.h      /* custom C code compiled into firmware image */
    #├─ .pilotfwconfig.json      /* firmware configuration (memory mapping, module configuration, etc.) */
    #├─ credentials.json /* authentication credentials (sensitive data) */
    #└─ basefw/          /* firmware base code folder */""".format(args.workdir if args.workdir else os.getcwd()))
  except Exception as error:
    print('An error occured creating the project')
    print(error)
    exit(1) 

def update(args):
  print("Updating base firmware")
  args = helper.get_node_from_config(args)
  toplevel = helper.find_fw_toplevel(args)
  if toplevel != '':
    args.workdir = toplevel
    download_base_firmware(args)
  else:
    print("Could not find project configuration file '.pilotfwconfig.json', firmware not updated")

def main(args, version, mode):
  if mode == 'init':
    init(args, version)
  elif mode == 'update':
    update(args)


