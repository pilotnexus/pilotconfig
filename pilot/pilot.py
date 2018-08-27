#!/usr/bin/env python3

import argparse
import os
import sys
import bugsnag
from . import pilotsetup
from . import compiler
from . import program
from . import project

print('Pilot Configuration Tool')

def my_except_hook(exectype, value, traceback):
  if exectype == KeyboardInterrupt:
    print("Keyboard Interrupt, cancelling. Bye!")
    exit(3)
  else:
    bugsnag.notify(Exception('Unhandled Exception, type: {}, value: {}, traceback: {}'.format(exectype, value, traceback)))
    sys.__excepthook__(exectype, value, traceback)

sys.excepthook = my_except_hook

def remoteargs(argparser):
    # Arguments available for all subparsers
  argparser.add_argument('--server', '-s', default=None, dest='server',
                  help='Alternative URL for the pilot server API to contact')
  argparser.add_argument('--host', '-o', default=None, dest='host',
                         help='Hostname to remote configure')
  argparser.add_argument('--user', '-u', default='pi', dest='user',
                         help='Remote SSH User (default: pi)')
  argparser.add_argument('--password', '-p', default='raspberry', dest='password',
                         help='Remote SSH Password (default: raspberry)')

def main():
  with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'VERSION'), encoding='utf-8') as f:
    VERSION = f.read().strip()

  bugsnag.configure(
      api_key="2d614bb3561d92fbd3b6f371e39b554a",
      project_root=".",
      app_version=VERSION,
      release_stage='production'
  )

  sys.excepthook = my_except_hook

  argparser = argparse.ArgumentParser(description='Pilot Command-Line Interface')

  # Subparsers
  subparsers = argparser.add_subparsers(dest='subparser_name')

  parser_a = subparsers.add_parser('setup', help="Configure Pilot Firmware")
  remoteargs(parser_a)
  pilotsetup.arguments(parser_a)

  parser_b = subparsers.add_parser('build', help="Compile additional software into firmware (IEC 61131-3 or C)")
  remoteargs(parser_b)
  compiler.arguments(parser_b)

  parser_c = subparsers.add_parser('program', help="Remote program PLC")
  remoteargs(parser_c)
  program.arguments(parser_c)

  parser_d = subparsers.add_parser('init', help="Initialize a new firmware project")
  remoteargs(parser_d)
  project.arguments(parser_d)

  args = argparser.parse_args()

  if ('subparser_name' in args):
    if (args.subparser_name == 'setup'):
      pilotsetup.main(args)
    elif (args.subparser_name == 'build'):
      compiler.main(args)
    elif (args.subparser_name == 'program'):
      program.main(args)
    elif (args.subparser_name == 'init'):
      project.main(args)
    elif (args.subparser_name == 'version'):
      print(VERSION)
    else:
      pilotsetup.main(parser_a.parse_args())

if __name__ == '__main__':
  main()
