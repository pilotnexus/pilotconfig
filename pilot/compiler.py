#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import json
from distutils.dir_util import copy_tree
from shutil import copyfile, move
import yaml
import importlib.util

def find_fw_toplevel():
  dir = os.getcwd()
  olddir = ''
  while dir != olddir:
    olddir = dir
    if os.path.isfile(os.path.join(dir, '.pilotfwconfig.json')):
      return dir
    dir = os.path.abspath(os.path.join(dir, '..'))
  return ''

def get_compilers():
  compilers = []
  directories = []
  for subdir, dirs, files in os.walk(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'compiler')):
    for dir in dirs:
      compilerinfofile = os.path.join(subdir, dir, 'template.yml')
      if os.path.isfile(compilerinfofile):
        with open(compilerinfofile, 'r') as f:
          try:
            compilers.append(yaml.load(f.read(), Loader=yaml.FullLoader))
            directories.append(os.path.join(subdir, dir))
          except Exception as e: 
            print('Error parsing {}'.format(compilerinfofile))
            print(e)
  return compilers, directories

def show_compilers():
  compilers, _ = get_compilers()
  for compiler in compilers:
    print('{}: {} (extension: {})'.format(compiler['name'], compiler['description'], compiler['filter']))

def get_config(args):
  try:
    if args.configfile == None:
      configfile = os.path.join(args.workdir, '.pilotfwconfig.json') if args.workdir else './.pilotfwconfig.json'
      if os.path.isfile(configfile):
        args.configfile = configfile
      else:
        configfile = os.path.join(find_fw_toplevel(), '.pilotfwconfig.json')
        if os.path.isfile(configfile):
          args.configfile = configfile
        else:
          args.configfile = os.environ['PILOT_CONFIG']
        
    with open(args.configfile) as configfile:
      config = json.load(configfile)
    print('Using config file ' + args.configfile)
    return config
  except:
    print("Configuration file (usually .pilotfwconfig.json) found, exiting")
    exit(1)

def main(args):
  compilerdirectory = None
  if ('show_compilers' in args and args.show_compilers):
    show_compilers()
  elif (args.fw_subparser_name == 'build'):
    config = get_config(args)
    compilers, directories = get_compilers()
    for index, compiler in enumerate(compilers):
      if compiler['name'] == config['compiler']:
        compilerdirectory = directories[index]
  if compilerdirectory == None:
    print('Compiler {} defined in configuration file not found.'.format(config['compiler']))
    return 1
  
  spec = importlib.util.spec_from_file_location("module.name", os.path.join(compilerdirectory, 'compiler.py'))
  compiler = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(compiler)
  compiler.main(args)
  return 0      