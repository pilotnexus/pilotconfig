import os
import distutils
import json
import yaml
from .Sbc import Sbc
from .PilotDriver import PilotDriver
from .PilotServer import PilotServer
from . import helper 
from colorama import Fore

def download_base_firmware(args):
  with Sbc(args) as sbc:
    pilotserver = PilotServer(sbc)
    pilotdriver = PilotDriver(pilotserver, sbc)

    if args.server != None:
      pilotserver.pilot_server = args.server

    modules, success = pilotdriver.load_pilot_defs()
    if modules != None:
      for module in modules:
        print('Module {}: {}{}'.format(
            module['module'], Fore.GREEN, module['currentfid_nicename']))

    if pilotdriver.get_firmware(False, os.path.join(args.workdir, 'basefw') if args.workdir else './basefw', True) != 0:
      print(Fore.RED + 'Could not download firmware source!')
      exit(1)
    return modules

def init(args):
  use_compiler = None
  print('This will create a new Pilot firmware project in the current folder')

  node_user = args.user
  node_password = args.password

  if not args.host:
    print('We need a hostname or IP and username/password (ssh) of the Node you want to configure.')
    args.host = input('Host/IP of Node to get Firmware Configuration from: ')

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

    while (compiler_index < 0 or compiler_index > len(compilers)):
      print('Please specify the compiler toolchain to use:')
      for index, compiler in enumerate(compilers):
        print('[{}] {}: {}'.format(index+1, compiler['name'], compiler['description']))
      try:
        compiler_index = int(input('[1-{}]: '.format(len(compilers)))) - 1
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
    #  node['host'] = args.host
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
    config['modules'] = []

    for mod in modules:
      if mod['currentfid']:
        module = {}
        module['slot'] = mod['module']
        module['fid'] = mod['currentfid']
        module['fid_nicename'] = mod['currentfid_nicename']
        module['hid'] = mod['hid']
        module['title'] = mod['title']
        module['subtitle'] = mod['subtitle']
        module['description'] = mod['description']

        # TODO: move to plugin
        if module['fid'] == 'io16':
          module['config'] = { 'direction': {'0_3': 'in', '4_7': 'in', '8_11': 'in', '12_15': 'in'} }
        config['modules'].append(module)

    with open(os.path.join(args.workdir, '.pilotfwconfig.json') if args.workdir else './.pilotfwconfig.json', 'w') as configfile:
      json.dump(config, configfile)

    # copy default project files
    targetpath = os.path.join(args.workdir, 'src') if args.workdir else './src'
    distutils.dir_util.copy_tree(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'project', 'default'), targetpath)
  
    print("Project generated:")
    print( """{}
    ├─ src/
    │  ├─ program.st    /* IEC 61131-3 code */
    │  └─ *.c, *.h      /* custom C code compiled into firmware image */
    ├─ .pilotfwconfig.json      /* firmware configuration (memory mapping, module configuration, etc.) */
    ├─ credentials.json /* authentication credentials (sensitive data) */
    └─ basefw/          /* firmware base code folder */""".format(args.workdir if args.workdir else os.getcwd()))
  except Exception as error:
    print(error)
    exit(1) 

def update(args):
  print("Updating base firmware")
  args = helper.get_host_from_config(args)
  toplevel = helper.find_fw_toplevel(args)
  if toplevel != '':
    args.workdir = toplevel
    download_base_firmware(args)
  else:
    print("Could not find project configuration file '.pilotfwconfig.json', firmware not updated")

def main(args, mode):
  if mode == 'init':
    init(args)
  elif mode == 'update':
    update(args)


