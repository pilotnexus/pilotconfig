#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from distutils.dir_util import copy_tree
from shutil import copyfile, move
import yaml
import lazy_import
from sys import platform as _platform

#Pilot PLC and custom code scripts

Compiler = lazy_import.lazy_callable("pybars.Compiler")
# from pybars import Compiler

os = lazy_import.lazy_module("os")
json = lazy_import.lazy_module("json")
itertools = lazy_import.lazy_module("itertools")
string = lazy_import.lazy_module("string")
re = lazy_import.lazy_module("re")

#from collections import defaultdict
defaultdict = lazy_import.lazy_callable("collections.defaultdict")
fnmatch = lazy_import.lazy_module("fnmatch")


def init(config, model):
  pass

def program(config):
  pass

def parsetemplate(out_path, templatedata, dir):
  #printable = set(string.printable)
  #filecontent = filter(lambda x: x in printable, templatefile.read())
  template_path = os.path.join(dir, 'template')

  for _root, _dirs, files in os.walk(template_path):
    templfiles = map(lambda x: os.path.join(template_path, x) ,filter(lambda x: x.endswith('.templ'), files))

    for templfile in templfiles:
      with open(templfile) as f:
        compiler = Compiler()
        template = compiler.compile(f.read())

        output = template(templatedata)

        with open(os.path.join(out_path, os.path.splitext(os.path.basename(templfile))[0]), 'w') as f:
          f.write(output)          

def main(args, config, model, projectdir, compilerdir):
  
  parsetemplate(projectdir, model, compilerdir)
  #run make - only works with installed arm-none-eabi-gcc
  #TODO - enable using docker container for the compiler
  subprocess.call(['make', '-C', args.workdir])

  return 0