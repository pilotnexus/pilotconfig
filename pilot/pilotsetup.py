#!/usr/bin/env python3

from __future__ import print_function  # disables annoying pylint print warning

import lazy_import
from . import arguments

sys = lazy_import.lazy_module("sys")
json = lazy_import.lazy_module("json")
re = lazy_import.lazy_module("re")
shlex = lazy_import.lazy_module("shlex")
time = lazy_import.lazy_module("time")
os = lazy_import.lazy_module("os")
argparse = lazy_import.lazy_module("argparse")
base64 = lazy_import.lazy_module("base64")
gettext = lazy_import.lazy_module("gettext")
bugsnag = lazy_import.lazy_module("bugsnag")
logging = lazy_import.lazy_module("logging")
paramiko = lazy_import.lazy_module("paramiko")

from uuid import getnode as get_mac
from bugsnag.handlers import BugsnagHandler
from threading import Thread
from colorama import Fore
from colorama import Style
from colorama import init

# class imports
from .PilotDriver import PilotDriver
from .PilotServer import PilotServer
from .Sbc import Sbc

############### INIT ###################

init(autoreset=True)  # colorama color autoreset

DEBUG = False
EXECVP_ENABLED = False

############## PROC FILE ACCESS #####################

def main(args):

  logger = logging.getLogger()
  handler = BugsnagHandler()
  # send only ERROR-level logs and above
  handler.setLevel(logging.ERROR)
  logger.addHandler(handler)

  logging.getLogger("paramiko").setLevel(logging.ERROR)
  
  result = 0
  with Sbc(args) as sbc:
    # PilotServer
    pilotserver = PilotServer(sbc)
    if args.server != None:
      pilotserver.pilot_server = args.server
    
    #PilotDriver
    pilotdriver = PilotDriver(pilotserver, sbc)

    #if not pilotdriver.check_raspberry() and not args.host:
    #  print('This does not seem to be a Raspberry Pi. Please use the --host option to remote connect to it.')
    #  return 2

    if os.getuid() != 0 and not args.host:
      print('Please run with sudo permissions.')
      return 2

    if not args.node:
      if sbc.need_sudo_pw():
        print('we need sudo on remote machine (without interactive authentication)')
        return 2

      if (args.reset):
        print('Resetting Pilot Mainboard')
        print(pilotdriver.reset_pilot())
        return 0

      ret = pilotdriver.check_driver()
      if ret != 0:
        if ret == 1:
          print('Reboot required')
          return 0
        return 1
    
      # do not continue if driveronly is specified
      if args.driveronly:
        return 0

      modules, success = pilotdriver.load_pilot_defs()
      trywritedefaultfirmware = False
      if not success:
        print(Fore.YELLOW, 'Could not read module data. Maybe the firmware is outdated, trying to write base firmware image.')
        trywritedefaultfirmware = True
      if modules != None:
        if args.source == None:
          while(True):
            print()
            modules_with_multiple_fids = []
            for module in modules:
              multiple_fids = len(module['fids']) > 1
              if multiple_fids:
                modules_with_multiple_fids.append(int(module['module']))
              if not trywritedefaultfirmware:
                print('Module {}: {}{} {}'.format(
                  module['module'], Fore.GREEN, module['currentfid_nicename'], '*' if multiple_fids else ''))

            ch = ''
            modsel = '/'.join([str(x) for x in modules_with_multiple_fids])
            if len(modules_with_multiple_fids) > 0:
              print('Modules marked with an Asterisk (*) have multiple firmware configurations')
              print('Press Module Number [{}] to change selected firmware.'.format(modsel))
            if (args.noninteractive or trywritedefaultfirmware):
              ch = 'y'
            else:
              ch = input('Do you want to build and program the Pilot Nexus Firmware? (y/n{}): '.format('/'+modsel if len(modules_with_multiple_fids) > 0 else '')).strip().lower()
            if ch == 'y' or ch == 'yes':
              if pilotdriver.build_firmware() == 0:
                result = pilotdriver.program()
                pilotdriver.reset_pilot()
              else:
                print('Could not write firmware')
              
              break
            elif ch.isdigit() and int(ch) in range(1, pilotdriver.MODULE_COUNT) and len(modules_with_multiple_fids) > 0:
              changemodulenr = int(ch)
              print()
              print('Select Firmware for Module {}:'.format(changemodulenr))
              for idx, fid in enumerate(modules[changemodulenr-1]['fids']):
                print('{}. {}{}'.format(idx+1, Fore.GREEN, fid['name']))
              ch = input('0=Cancel, [1-{}]: '.format(len(modules[changemodulenr-1]['fids'])))
              if (ch.isdigit() and int(ch) > 0 and int(ch) <= len(modules[changemodulenr-1]['fids'])):
                pilotdriver.set_module_fid(changemodulenr, modules[changemodulenr-1]['fids'][int(ch)-1]['fid'])
                modules, success = pilotdriver.load_pilot_defs()
            else:
              break

        else:
          srcpath = os.path.abspath(args.source)
          pilotdriver.get_firmware(False, srcpath, True)
        
      else:
        print('No modules found, is the driver loaded?')
      fwconfig = {}
      fwconfig['modules'] = modules
      if not args.noninteractive and not trywritedefaultfirmware and result == 0:
        pilotserver.registernode(fwconfig)
    elif not args.noninteractive:
      pilotserver.registernode(None)

  if result == 0:
    if trywritedefaultfirmware:
      print("Default firmware written. Run the setup tool again to program firmware for your modules")
    else:
      print ("To get help on how to use the modules, run 'pilot --module'")
  return result

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Setup Pilot Nexus')
  arguments.setup_arguments(parser)
  sys.exit(main(parser.parse_args()))
