import os
import argparse

from .Sbc import Sbc
from .PilotServer import PilotServer
from .PilotDriver import PilotDriver

def arguments(parser):
  parser.add_argument('--binary', '-b', default=None, dest='bin',
                      help='Write binary image to the Pilot Microcontroller')
  parser.add_argument('--variables', '-v', default=None, dest='vars',
                      help='Set PLC variables')

def main(args):

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

    vars = None
    if args.vars:
      if os.path.isfile(args.vars):
        vars = args.vars
      else:
        print('You need to specify a valid file for the --variables attribute.')
        exit(1)

    if args.bin:
      if os.path.isfile(args.bin):
        pilotdriver.program(program_cpld=False, program_mcu=True, mcu_file=args.bin, var_file=vars)
      else:
        print('You need to specify a valid file for the --binary attribute.')
        exit(1)
    else:
      print('You need to specify an image file to write with the --binary attribute.')
      exit(1)

if (__name__ == "__main__"):
  parser = argparse.ArgumentParser(
    description='Write custom firmware')
  arguments(parser)
  main(parser.parse_args())