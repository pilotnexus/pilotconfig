import os
import argparse
import json
from distutils.dir_util import copy_tree
from shutil import copyfile, move
import yaml
from . import pilotplc

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

def main(args):

  #if no iec path parameter is given try the environment var
  if args.iec2cdir == None:
    try:
      args.iec2cdir = os.environ['IEC2C_DIR']
    except:
      print("No parameter IEC2C directory given and no IEC2C_DIR environment variable defined, exiting")
      exit(1)

  #if no source path parameter is given try the environment var
  if args.source == None:
    try:
      args.source = os.environ['PILOT_SOURCE']
    except:
      print("No parameter source directory given and no PILOT_SOURCE environment variable defined, exiting")
      exit(1)

  if args.configfile == None:
    try:
      args.configfile = os.environ['PILOT_CONFIG']
    except:
      print("No configuration file given, exiting")
      exit(1)


  stmmodel = {}
  modules = {}

  with open(os.path.join(os.path.abspath(args.source), 'stmmodel.json')) as stmmodelfile:
    stmmodel.update(json.load(stmmodelfile))

  #if no target path parameter is given try the environment var
  if args.target == None:
    args.target = os.path.join(os.getcwd(), "out")
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

  copy_tree(args.source, args.target)
  copy_tree(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), 'template', 'inc'), os.path.join(args.target, 'inc'))

  #additional model data
  if 'includes' in config:
    stmmodel['includes'] = config['includes']

  stfiles = list(filter(lambda x: x.endswith('.st'), args.files))
  codefilearr = list(filter(lambda x: not x.endswith('.st'), args.files))
  codefiles = ' '.join(codefilearr)
 
  if len(stfiles) > 0:
    stfile = stfiles[0]
    if len(stfiles) > 1:
      stfile = os.path.join(args.target, 'program.st')
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
    new.write('EXTRAFILES='+codefiles+'\n')
    with open(makefile) as old:
      new.write(old.read())

  move(newMakefile, makefile)

if (__name__ == "__main__"):
  parser = argparse.ArgumentParser(
    description='Compile Pilot PLC and custom code')
  arguments(parser)
  main(parser.parse_args())

