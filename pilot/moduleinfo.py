import argparse

# class imports
from .PilotDriver import PilotDriver
from .PilotServer import PilotServer
from .Sbc import Sbc

from colorama import Fore
from colorama import Style
from colorama import init


def arguments(parser):
  # parser.add_argument('--terminal', '-t', action='store_true', help='forces the terminal version instead of GUI')
  parser.add_argument('--help', '-h', default=None, dest='source',
                      help='Get help on modules')

def main(args):
  with Sbc(args) as sbc:
    pilotserver = PilotServer(sbc)
    if args.server != None:
      pilotserver.pilot_server = args.server
    
    #PilotDriver
    pilotdriver = PilotDriver(pilotserver, sbc)

    if not pilotdriver.check_raspberry() and not args.host:
      print('This does not seem to be a Raspberry Pi. Please use the --host option to remote connect to it.')
      return 2

    if sbc.need_sudo_pw():
      print('we need sudo on remote Node (without interactive authentication)')
      return 2

    modules = pilotdriver.load_pilot_defs()

    #Print module help
    moduleinfos = pilotdriver.get_help()

    if moduleinfos:
      for module in moduleinfos:
        print()
        print(Fore.GREEN + 'Module [{}] {}:'.format(module['number'], modules[module['number']-1]['currentfid_nicename']))
        print(module['help'])
        if module['examples'] and len(module['examples']) > 0:
          for idx,example in enumerate(module['examples']):
            print(Fore.CYAN + 'Example {}: {}'.format(idx+1, example['title']))
            print(example['example'])
        
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Module Info')
  arguments(parser)
  main(parser.parse_args())