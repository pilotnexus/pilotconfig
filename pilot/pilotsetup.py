#!/usr/bin/env python3
from __future__ import print_function  # disables annoying pylint print warning

import sys
import json
import re
import shlex
import time
import os
import argparse
import base64
import gettext
import bugsnag
import logging
import paramiko

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

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'VERSION'), encoding='utf-8') as f:
  VERSION = f.read().strip()

DEBUG = False
EXECVP_ENABLED = False

logger = logging.getLogger()
handler = BugsnagHandler()
# send only ERROR-level logs and above
handler.setLevel(logging.ERROR)
logger.addHandler(handler)

############## PROC FILE ACCESS #####################

def arguments(parser):
  # parser.add_argument('--terminal', '-t', action='store_true', help='forces the terminal version instead of GUI')
  parser.add_argument('--source', '-c', default=None, dest='source',
                      help='Download Sourcecode only')
  parser.add_argument('--node', '-n', default=None, dest='node',
                      help='Configure node only')
  parser.add_argument('--reset', '-r', default=None, action='store_const', const='reset', dest='reset',
                      help='Resets the Pilot Mainboard')


def main(args):
  print('Version {}'.format(VERSION))
  # print('Amescon/Daniel Amesberger 2018, www.amescon.com')

  with Sbc(args, True) as sbc:
    # PilotServer
    pilotserver = PilotServer(sbc)
    if args.server != None:
      pilotserver.pilot_server = args.server
    
    #PilotDriver
    pilotdriver = PilotDriver(pilotserver, sbc)

    if not pilotdriver.check_raspberry() and not args.host:
      print('This does not seem to be a Raspberry Pi. Please use the --host option to remote connect to it.')
      return 2

    if not args.node:
      if sbc.need_sudo_pw():
        print('we need sudo on remote machine (without interactive authentication)')
        return 2

      if (args.reset):
        print('Resetting Pilot Mainboard')
        pilotdriver.reset_pilot()
        print('Done')
        return 0

      ret = pilotdriver.check_driver()
      if ret != 0:
        return 1

      modules = pilotdriver.load_pilot_defs()
      if modules != None:
        if args.source == None:
          while(True):
            print()
            modules_with_multiple_fids = []
            for module in modules:
              multiple_fids = len(module['fids']) > 1
              if multiple_fids:
                modules_with_multiple_fids.append(int(module['module']))
              print('Module {}: {}{} {}'.format(
                  module['module'], Fore.GREEN, module['currentfid_nicename'], '*' if multiple_fids else ''))

            ch = ''
            modsel = '/'.join([str(x) for x in modules_with_multiple_fids])
            if len(modules_with_multiple_fids) > 0:
              print('Modules marked with an Asterisk (*) have multiple firmware configurations')
              print('Press Module Number [{}] to change selected firmware.'.format(modsel))
            ch = input('Do you want to build and program the Pilot Nexus Firmware? (y/n{}): '.format('/'+modsel if len(modules_with_multiple_fids) > 0 else '')).strip().lower()
            if ch == 'y' or ch == 'yes':
              if pilotdriver.build_firmware() == 0:
                pilotdriver.program()
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
                modules = pilotdriver.load_pilot_defs()
            else:
              break

        else:
          srcpath = os.path.abspath(args.source)
          pilotdriver.get_firmware(False, srcpath, True)
        
      else:
        print('No modules found, is the driver loaded?')
      fwconfig = {}
      fwconfig['modules'] = modules
      pilotserver.registernode(fwconfig)
    else:
      pilotserver.registernode(None)

  print ("To get help on how to use the modules, run 'pilot module'")

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Setup Pilot Nexus')
  arguments(parser)
  main(parser.parse_args())
