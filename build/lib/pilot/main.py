#!/usr/bin/env python3
import argparse
import pilotsetup
import compile

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
