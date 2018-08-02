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
from .PilotServer import PilotServer
from .PilotDriver import PilotDriver
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
  parser.add_argument('--server', '-s', default=None, dest='server',
                      help='Alternative URL for the pilot server API to contact')
  parser.add_argument('--source', '-c', default=None, dest='source',
                      help='Download Sourcecode only')
  parser.add_argument('--node', '-n', default=None, dest='node',
                      help='Configure node only')
  parser.add_argument('--reset', '-r', default=None, action='store_const', const='reset', dest='reset',
                      help='Resets the Pilot Mainboard')


def main(args):
  print('Version {}'.format(VERSION))
  # print('Amescon/Daniel Amesberger 2018, www.amescon.com')

  with Sbc(args) as sbc:
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
        for module in modules:
          print('Module {}: {} {}'.format(
              module['module'], module['currentfid_nicename'], '*' if len(module['fids']) > 1 else ''))

        if args.source == None:
          ch = input('Do you want to build and program the PiloT Mainboard Firmware? (y/n): ').strip().lower()
          if ch == 'y' or ch == 'yes':
            if pilotdriver.build_firmware():
              pilotdriver.program()
              pilotdriver.reset_pilot()
        else:
          srcpath = os.path.abspath(args.source)
          pilotdriver.wait_build(False, srcpath, True)

    pilotserver.registernode()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Setup PiloT')
  arguments(parser)
  main(parser.parse_args())
