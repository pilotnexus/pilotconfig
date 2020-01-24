import os
import json
import argparse
from . import arguments
from . import helper 
from .sbc import Sbc
from .pilotserver import PilotServer
from .pilotdriver import PilotDriver


def main(args):
  args = helper.get_host_from_config(args)
  program(args)

def program(args):
  try:
    with Sbc(args) as sbc:
      # PilotServer
      pilotserver = PilotServer(sbc)
      if args.server != None:
        pilotserver.pilot_server = args.server
      
      #PilotDriver
      pilotdriver = PilotDriver(pilotserver, sbc)

      if not pilotdriver.driver_loaded():
        print('Drivers are not loaded. Please use --host if you connect remotely or install pilot drivers first by running sudo pilot setup.')
        return 2

      #if not pilotdriver.check_raspberry() and not args.host:
      #  print('This does not seem to be a Raspberry Pi. Please use the --host option to remote connect to it.')
      #  return 2

      vars = None
      if args.vars:
        if os.path.isfile(args.vars):
          vars = args.vars
        else:
          print('You need to specify a valid file for the --variables attribute.')
          exit(1)
      else:
        varfile = os.path.join(args.workdir, 'out/VARIABLES.csv') if args.workdir else './out/VARIABLES.csv'
        if os.path.isfile(varfile):
          print('Using variable file ' + varfile)
          vars = varfile

      if args.bin:
        if not os.path.isfile(args.bin):
          print('You need to specify a valid file for the --binary attribute.')
          exit(1)
      elif os.path.isfile(os.path.join(args.workdir, 'out/stm.bin') if args.workdir else './out/stm.bin'):
        args.bin = os.path.join(args.workdir, 'out/stm.bin') if args.workdir else './out/stm.bin'
      else:
        print('You need to specify an image file to write with the --binary attribute.')
        exit(1)
      pilotdriver.program(program_cpld=False, program_mcu=True, mcu_file=args.bin, var_file=vars)
  except Exception as error:
    print(error)

if (__name__ == "__main__"):
  parser = argparse.ArgumentParser(
    description='Write custom firmware')
  arguments.program_arguments(parser)
  main(parser.parse_args())