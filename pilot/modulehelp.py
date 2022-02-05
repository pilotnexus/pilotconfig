from asyncore import file_dispatcher
from pathlib import Path
from .pilotdriver import PilotDriver
from .pilotserver import PilotServer
from .sbc import Sbc

import re

import lazy_import
Compiler = lazy_import.lazy_callable("pybars.Compiler")

from tabulate import tabulate
from colorama import Fore
from colorama import Style
from colorama import init

init(autoreset=True)  # colorama color autoreset

class ModuleHelp():
    sbc = None
    module = None
    
    def gpiochip_base(self, _, offset):
        p = re.compile('^gpiochip([0-9]+)$', re.MULTILINE)
        l = re.compile('^pilot.*?_([0-9]+)$')
        matches = p.findall(self.sbc.cmd('ls /sys/class/gpio'))
        for gc_str in matches:
            gpio_start = int(gc_str)
            if gpio_start >= 60 and gpio_start < 500: #min gpio number of pilot GPIOs
                label = self.sbc.cmd('cat /sys/class/gpio/gpiochip{}/label'.format(gpio_start))
                num_match = l.match(label)
                if num_match and int(num_match.group(1)) == self.number: 
                    if offset != None:
                        gpio_start += offset
                    return gpio_start
        return -1
    
    def tty(self, data):
        return "/dev/ttyP{}".format((self.number)*2)


    def help(self, args):
        with Sbc(args) as sbc:
            self.sbc = sbc
            pilotserver = PilotServer(sbc)
            if 'server' in args and args.server != None:
                pilotserver.pilot_server = args.server
            
            #PilotDriver
            pilotdriver = PilotDriver(pilotserver, sbc)
    
            modules, success = pilotdriver.load_pilot_defs()
            if success:
                for mod in modules:
                    if mod['module'] == args.module:
                        self.number = args.module-1
                        self.printhelp(args, mod, sbc)
    
    def loop(self, _, block, start, to, incr):
        accum = '' 
        for i in range(start, to, incr):
            accum += "".join(block['fn'](i))
        return accum

    def printhelp(self, args, module, sbc):
            helpers = {'gpio_base': self.gpiochip_base, 'tty': self.tty, 'for': self.loop }

            print("")
            print(Fore.GREEN + 'Module [{}]: {}'.format(args.module, module['currentfid_nicename']))
            print("")
    
            if module != None:
                compiler = Compiler()

                if args.pinout:
                    if 'pinout' in module and 'default' in module['pinout'] and 'pins' in module['pinout']['default']:
                        pins = module['pinout']['default']['pins'] 
                        print(tabulate(pins, tablefmt="fancy_grid"))
                    else:
                        print("No pinout available for this module")
                elif args.usage:
                    if 'usage' in module and module['usage'] != None:
                        template = compiler.compile(module['usage'])
                        text = template({}, helpers)
                        for line in text.split('\n'):
                            if line.strip().startswith("#"):
                                print(Fore.GREEN+line)
                            else:
                                print(line)
                    else:
                        print("No usage description available for this module")
                else:
                    if 'description' in module and module['description'] != None:
                        print(module['description'])
                    else:
                        print("No description available for this module")

                    print("")
                    print("Run with --pinout to see pinout")
                    print("Run with --usage to get usage examples")
            else:
                print("Module not found")



