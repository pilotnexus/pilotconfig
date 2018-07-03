#!/usr/bin/env python3

print('Pilot Config')

import argparse
import os
from . import pilotsetup
from . import compile

def main():
  with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'VERSION'), encoding='utf-8') as f:
    VERSION = f.read().strip()

  argparser = argparse.ArgumentParser(description='Pilot Command-Line Interface')
  subparsers = argparser.add_subparsers(dest='subparser_name')

  parser_a = subparsers.add_parser('setup', help="Configure Pilot Firmware")
  pilotsetup.arguments(parser_a)

  parser_b = subparsers.add_parser('build', help="Compile additional software into firmware")
  compile.arguments(parser_b)

  args = argparser.parse_args()
  if ('subparser_name' in args):
    if (args.subparser_name == 'setup'):
      pilotsetup.main(args)
    elif (args.subparser_name == 'build'):
      compile.main(args)
    else:
      pilotsetup.main(parser_a.parse_args())

if __name__ == '__main__':
  main()
