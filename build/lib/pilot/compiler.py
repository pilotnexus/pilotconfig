#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import json
from distutils.dir_util import copy_tree
from shutil import copyfile, move
import yaml

from . import arguments

from . import pilotplc


def arguments(parser):
  parser.add_argument('--config', dest='configfile',
                      default=None, help='module config file (.json or .yml)')
  parser.add_argument('--iec2c', dest='iec2cdir',
                      default=None, help='directory of iec2c compiler')
  parser.add_argument('--source', dest='source',
                      default=None, help='source directory')
  parser.add_argument('--target', dest='target',
                      default=None, help='target directory')
  parser.add_argument('--verbose', action='store_const',
                      const=True, help='verbose output')
  parser.add_argument('files', nargs='*', default=None,
                      help='IEC Structured Text File')
  parser.add_argument('--ignore-files', default=None, action='store_const', const='ignore_files', dest='ignore_files',
                      help='If no files are given, do not automatically use source files found in src folder')
  
def main(args, target):
  config = None

  #if no iec path parameter is given try the environment var
  if args.iec2cdir == None:
    try:
      args.iec2cdir = os.environ['IEC2C_DIR']
    except:
      args.iec2cdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'matiec')
 
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

  if args.configfile == None:
    try:
      config = os.path.join(args.workdir, '.pilotfwconfig.json') if args.workdir else './.pilotfwconfig.json'
      if os.path.isfile(config):
        args.configfile = config
      else:
        args.configfile = os.environ['PILOT_CONFIG']
      print('Using config file ' + args.configfile)

    except:
      print("No configuration file found, continuing without it")


  stmmodel = {}
  modules = {}

  with open(os.path.join(os.path.abspath(args.source), 'stmmodel.json')) as stmmodelfile:
    stmmodel.update(json.load(stmmodelfile))

  #if no target path parameter is given try the environment var
  if args.target == None:
    args.target = os.path.join(args.workdir, "out") if args.workdir else os.path.join(os.getcwd(), "out")
    if not os.path.exists(args.target):
      os.makedirs(args.target)

  print("Writing output to " + args.target)

  if args.configfile != None:
    print("loading configfiles")
    with open(args.configfile) as configfile:
      if (args.configfile.endswith('.json')):
        config = json.load(configfile)
    modules, overlaps, misalignedmodules, mem = pilotplc.init(config, stmmodel)

    for overlap in overlaps:
      print("Overlapping memory regions! Module in slot {} and slot {} overlap in {} memory at byte position {}".format(overlap['elementa']['slot'], overlap['elementb']['slot'], overlap['memory'], ', '.join(str(s) for s in overlap['address'])))
      exit(2)

    if misalignedmodules != []:
      print("Modules in Firmware Source do not match modules in config file:")
      print("   Firmware   Config File")
      for module in stmmodel['Modules']:
        m = list(filter(lambda x: x['slot'] - 1 == module['Slot'] ,config['modules']))
        print("{0:1}: {1:10} {2:10}".format(module['Slot']+1, module['Name'], m[0]['fid'] if len(m) == 1 else 'None'))
      exit(2)

  #print(mem)
  #print(modules)

  copy_tree(args.source, args.target)
  copy_tree(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), 'template', 'inc'), os.path.join(args.target, 'inc'))

  #additional model data
  if config and 'includes' in config:
    stmmodel['includes'] = config['includes']

  stfiles = []
  codefilearr = []
  if len(args.files) != 0 or 'ignore_files' in args:
    stfiles = list(filter(lambda x: x.endswith('.st'), args.files))
    codefilearr = list(filter(lambda x: not x.endswith('.st'), args.files))
  else:
    for file in os.listdir(os.path.join(args.workdir, 'src')):
      if file.endswith(".st"):
        stfiles.append(os.path.join(args.workdir, 'src', file))
      elif file.endswith(".c"):
        codefilearr.append(os.path.join(args.workdir, 'src', file))
  codefiles = ' '.join(codefilearr)
 
  plcfiles = ''
  if len(stfiles) > 0:
    plcfiles = 'config.h config.c resource1.c POUS.h ' # TODO - check if hardcoded files make sense here. can't use make plc with that. always use make default
    stfile = stfiles[0]
    if len(stfiles) > 1:
      stfile = os.path.join(args.target, '__program.st')
      with open(stfile, 'w') as outfile:
        for fname in stfiles:
          with open(fname) as infile:
            for line in infile:
              outfile.write(line)

    #iec2c compile and extract variables
    if pilotplc.iec2c_compile(args.iec2cdir, stfile, args.target) == 0:
      print('parsing variables')
      programs, variables, locatedvariables, locations = pilotplc.parseplcvariables(args.target, mem)

      if args.verbose:
        print(yaml.dump(mem, Dumper=yaml.Dumper, default_flow_style=False))

      calls = pilotplc.parsemodules(mem, modules)
      stmmodel['PLC'] = {'programs': programs, 'variables': variables, 'locatedvariables': locatedvariables, 'locations': locations, 'mem': mem, 'calls': calls}
      stmmodel['PLC']['modules'] = modules
      if 'subscriptions' in config:
        stmmodel['PLC']['subscriptions'] = pilotplc.parsesubscriptions(config['subscriptions'])
      pilotplc.parsetemplate(args.target, stmmodel)

      with open(os.path.join(args.workdir, "out", 'stmmodel.json'), 'w') as stmmodelfile:
        json.dump(stmmodel, stmmodelfile)

    else:
      print("Error executing IEC2C Compiler")
      exit(1)

  # codefiles
  for codefile in codefilearr:
    copyfile(codefile, os.path.join(args.target, os.path.basename(os.path.abspath(codefile))))

  # extra compilation files
  newMakefile = os.path.join(args.target, 'newMakefile')
  makefile = os.path.join(args.target, 'Makefile')
  with open(newMakefile, 'w') as new:
    new.write('EXTRAFILES='+plcfiles+codefiles+'\n')
    with open(makefile) as old:
      new.write(old.read())

  move(newMakefile, makefile)

  #run make - only works with installed arm-none-eabi-gcc
  #TODO - enable using docker container for the compiler
  subprocess.call(['make', '-C', args.target])

  return 0

if (__name__ == "__main__"):
  parser = argparse.ArgumentParser(
    description='Compile Pilot PLC and custom code')
  arguments.compiler_arguments(parser)
  sys.exit(main(parser.parse_args()))

