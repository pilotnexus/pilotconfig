import lazy_import

sys = lazy_import.lazy_module("sys")
time = lazy_import.lazy_module("time")
re = lazy_import.lazy_module("re")
os = lazy_import.lazy_module("os")
scp = lazy_import.lazy_module("scp")
tarfile = lazy_import.lazy_module("tarfile")
itertools = lazy_import.lazy_module("itertools")
requests = lazy_import.lazy_module("requests")
bugsnag = lazy_import.lazy_module("bugsnag")

import traceback

from pathlib import Path

from .pilotserver import PilotServer
from .sbc import Sbc

from shutil import copyfile
from gql import gql 

from colorama import Fore
from colorama import Style
from colorama import init

from enum import Enum
class BuildStep(Enum):
  Error = -2
  QueueFull = -1
  Done = 0
  Queued = 1
  ValidateRequest = 2
  GenerateCpldSource = 3
  CompileCpldSource = 4
  CleanStmOutputDirectory = 5
  GenerateStmSource = 6
  CompileStmSource = 7
  PackageFirmware = 8
  PackageSource = 9
  Cleanup = 10

class PilotDriver():
  MODULE_COUNT = 4
  retry_count = 2
  emptystr = '-'
  pilot_driver_root = '/proc/pilot'
  tmp_dir = '/tmp/pilot'
  kernmodule_list = ['pilot', 'pilot_plc', 'pilot_tty',
                     'pilot_rtc', 'pilot_fpga', 'pilot_io', 'pilot_slcd']

  binpath = ''

  eeproms = {}
  modules = {}

  ps = None
  sbc = None

  def __init__(self, pilotserver: PilotServer, sbc: Sbc):
    self.ps = pilotserver
    self.sbc = sbc

    if sbc is not None:
      self.binpath = '{}/bin/{}'.format(os.path.join(
      os.path.abspath(os.path.dirname(__file__))), self.sbc.target['architecture'])

  def get_modules(self):
    memregs = ['uid', 'hid', 'fid']
    strmlist = list(filter(
        None, self.sbc.cmd('find /proc/pilot/module* -maxdepth 0 -printf "%f\\n"').split('\n')))
    matches = filter(None, map(lambda x: re.match(r'module(\d+)', x), strmlist))
    modlist = {int(x.group(1)): {'uid': '', 'hid': '', 'fid': ''}
              for x in matches}
    for mod in modlist:
      for memreg in memregs:
        retry = self.retry_count
        errcount = 0
        while retry > 0:
          retry = retry - 1
          try:
            regfile = self.sbc.cmd(
                'cat {}/module{}/eeprom/{}'.format(self.pilot_driver_root, mod, memreg), True)
            modlist[mod][memreg] = ''.join(
                char for char in regfile if str.isprintable(char)).strip()
            
            if memreg == 'fid': # additional plausibility checks
              if len(list(filter(lambda x: ord(x) > 255, regfile))) > 0:
                modlist[mod][memreg] = ''
              else:
                break
            else:
              break
          #except:
          except Exception as e:
            modlist[mod][memreg] = ''
            errcount = errcount + 1
            if errcount >= self.retry_count:
              return modlist, False
            #dbg('could not read {} of module {}'.format(memreg, mod))
    return modlist, True

  def set_module_fid(self, number, fid):
    self.sbc.setFileContent(self.pilot_driver_root + '/module{}/eeprom/fid'.format(number), fid + '       ')

  def getmodules(self, mod):
    self.eeproms = mod
    try:
      variables = {
        'fids': ['{}'.format(value['fid'])
                    for key, value in mod.items() if value['fid'] != ''],
        'hids': ['{}'.format(value['hid'])
                    for key, value in mod.items() if value['hid'] != '']
      }
    
      obj = self.ps.query(gql("""
      query get_fids($fids: [bpchar!], $hids: [bpchar!]) {
        pilot_fid(where: {fid: {_in: $fids} }) {
          fid
          name
        }
        pilot_hid(where: {hid: {_in: $hids} }) {
          hid
          title
          subtitle
          description
          hid2fids {
            fid {
              fid
              name
            }
            isdefault
          }
        }
      }
      """), variables, True)

      self.modules = [{
                  'module': key,
                  'currentfid': value['fid'],
                  'hid': value['hid'],
                  'currentfid_nicename': next(iter(y['name']  for y in filter(lambda x: x['fid'].strip() == value['fid'].strip(), obj['pilot_fid'])), value['fid'].strip()),
                  'fids': next(iter([{'isdefault': x['isdefault'], 'fid': x['fid']['fid'], 'name': x['fid']['name']} for x in y['hid2fids']] for y in filter(lambda x: x['hid'].strip() == value['hid'].strip(), obj['pilot_hid'])), []),
                } for key, value in mod.items()]

      return self.modules, True
    except:
      e = sys.exc_info()[0]
      print(e)
    return {}, False

  def load_pilot_defs(self):
    success = False
    try:
      eeproms, success = self.get_modules()
      return self.getmodules(eeproms)
    except:
      return {}, False

  def driver_loaded(self):
    return self.sbc.cmd_retcode('test -e {}'.format(self.pilot_driver_root)) == 0

  def getModuleEeprom(self, module, memregion):
    try:
      return self.sbc.getFileContent('{}/module{}/eeprom/{}'.format(self.pilot_driver_root, module, memregion))
    except:
      return ''

  def tryrun(self, text, retries, cmd):
    print(text + '...', end='')
    sys.stdout.flush()
    while retries > 0:
      retries = retries - 1
      try:
        if self.sbc.cmd_retcode(cmd) == 0:
          print(Fore.GREEN + 'done')
          return 0
      except:
        print('.', end='')
        sys.stdout.flush()
    print(Fore.RED + 'failed')
    return 1

  def reset_pilot(self, wait_bootmsg=False):
    try:
      if not wait_bootmsg:
        print('Resetting MCU...', end='')
      sys.stdout.flush()
      reset_pin = self.sbc.target['reset_pin']['number']
      self.sbc.cmd('sudo sh -c \'[ ! -f /sys/class/gpio/gpio{0}/value ] && echo "{0}" > /sys/class/gpio/export\''.format(reset_pin))
      self.sbc.cmd('sudo sh -c \'echo "out" > /sys/class/gpio/gpio{}/direction\''.format(reset_pin))
      self.sbc.cmd('sudo sh -c \'echo -n "1" > /sys/class/gpio/gpio{}/value\''.format(reset_pin))
      time.sleep(2)
      if wait_bootmsg:
        missing_commands = ''
        if self.sbc.cmd_retcode('command -v stty') != 0:
          missing_commands = missing_commands + 'stty '
        if self.sbc.cmd_retcode('command -v timeout') != 0:
          missing_commands = missing_commands + 'timeout '

        if missing_commands == '':
          return self.sbc.cmd("sudo sh -c 'stty -F {0} 921600;sleep 0.1;timeout 2 cat {0} & sleep 0.5; echo 0 > /sys/class/gpio/gpio{1}/value;wait'".format(self.sbc.target['tty'], reset_pin))
        else:
          return self.sbc.cmd("/sys/class/gpio/gpio{0}/value".format(reset_pin))
      else:
        self.sbc.cmd('sudo sh -c \'echo -n "0" > /sys/class/gpio/gpio{}/value\''.format(reset_pin))
        print(Fore.GREEN + 'done')
    except:
      print(Fore.RED + 'failed')
    return ''

  def install_driver(self):
    try:
      match = re.match(self.sbc.target['kernelversionre'], self.sbc.cmd('uname -a'))
      if match:
        packagename = "pilot-{}{}".format(match.group('version'),
                                          match.group('buildnum') if 'buildnum' in match.groupdict() else '')
        print('trying to install package ''{}'''.format(packagename))
        if self.sbc.cmd_retcode("""sudo sh -c 'echo "{}" > /etc/apt/sources.list.d/amescon.list'""".format(self.sbc.target['apt_source'])) != 0:
          print('Could not add source to /etc/apt/sources.list.d/amescon.list')
          return 1
        if self.sbc.cmd_retcode("""sudo sh -c 'wget -qO - http://archive.amescon.com/amescon.asc | sudo apt-key add -'""") != 0:
          print('Could not get signing keys from amescon keyserver')
          return 1
        self.sbc.cmd_retcode('sudo apt-get update')
        self.sbc.cmd_retcode("sudo apt-get remove '^pilot-.*' -y")
        self.sbc.cmd('sudo apt-get install -y {}'.format(packagename), True)
      else:
        print('Could not detect your linux version')
        return 1
    except Exception as e:
      # bugsnag.notify(e, user={
      #     "username": self.ps.pilotcfg['username']})
      return 1
    return 0

  def get_kernel_info(self):
    try:
      fwhash = self.sbc.cmd("echo $(/bin/zgrep '* firmware as of' /usr/share/doc/raspberrypi-bootloader/changelog.Debian.gz | head -1 | awk '{ print $5 }') && /usr/bin/wget https://raw.github.com/raspberrypi/firmware/$FIRMWARE_HASH/extra/git_hash -O - 2> NUL", True)
      if self.sbc.cmd_retcode('sudo modprobe configs') == 0:
        print ('If you want us to build a kernel for you, send us the following firmware hash AND the file on your Raspberry Pi located in: /proc/config.gz')
        print ('Firmware Hash: {}'.format(fwhash))
        return 0
      else:
        print('Could not load configs. Check if the target Hardware is a Raspberry Pi and your user is sudoer.')
    except:
      print("Could not get your Firmware Hash. Check if the target Hardware is a Raspberry Pi and it is online.")
    return 1

  def check_driver(self):
    if self.sbc.cmd_retcode('ls ' + self.pilot_driver_root) != 0:
      print('Pilot driver is not loaded. Trying to load')
      if self.reload_drivers(False):
        print('Drivers loaded')
      else:
        if self.install_driver() == 0:
          print('Pilot driver installed.')
          return 1
        else:
          print('Could not install the pilot driver, most likely there is no driver compiled for your kernel.')
          #self.get_kernel_info()
          return -1
    return 0
        
  def reload_drivers(self, verbose = True):
    ok = True
    if verbose:
      print('reloading drivers...', end='')
    sys.stdout.flush()
    for module in self.kernmodule_list[::-1]:
      try:
        self.sbc.cmd_retcode("sudo modprobe -r {}".format(module))
      except:
        pass

    for module in self.kernmodule_list:
      try:
        if self.sbc.cmd_retcode("sudo modprobe {}".format(module)) != 0:
          ok = False
      except:
        ok = False

    if verbose:
      if ok:
        print(Fore.GREEN + 'done')
      else:
        print(Fore.RED + 'failed')

    return ok

  def run_build(self):
    modules = [{"number": key, "fid": value['fid']} for key, value in self.eeproms.items() if value['fid'] != '']
    variables = {"request": { "modules": modules}}
    try:
      obj = self.ps.query(gql(u"""
      mutation createBuild($request: jsonb) {
        insert_pilot_build(objects: { request: $request}) {
          returning {
            id
          }
        }
      }
      """),variables, True)   # .format(','.join(['{{number: {}, uid: "{}", fid: "{}"}}'.format(key, value['uid'], value['fid']) for key, value in self.eeproms.items() if value['fid'] != '']))

      if 'insert_pilot_build' in obj and 'returning' in obj['insert_pilot_build'] and len(obj['insert_pilot_build']['returning']) > 0:
        return obj['insert_pilot_build']['returning'][0]['id']
    except Exception as e:
      print(e)
    return None

  def build_status(self, id):
    try:
      query = gql(u"""
        query getbuild($id: Int) {
          pilot_build(where: {id: {_eq: $id}}) {
            iscomplete
            status
            relativeurl
          }
        }
      """)
      obj = self.ps.query(query, {"id": id}, True)
      if 'pilot_build' in obj and len(obj['pilot_build']) > 0:
        return obj['pilot_build'][0]
      else:
        return None
    except Exception as e:
      print(e)
    return None

  def statestring(state):
    return ('(' + str(state) + ') ').ljust(30)

  def build(self):
    try:
      spinner = itertools.cycle(['-', '/', '|', '\\'])
      sys.stdout.write('checking if firmware is available...')
      sys.stdout.flush()
      id = self.run_build()
      # wait a second to process
      time.sleep(1)
      if id is not None:
        ret = self.build_status(id)

        if ret != None and ret['iscomplete'] and ret['status'] == 0: #already built
          print(Fore.GREEN + 'available')
          return ret['relativeurl'], None
        else:
          print(Fore.GREEN + 'needs compilation')
          sys.stdout.write('compiling firmware ')
          sys.stdout.flush()
          statestr = lambda state : ('(' + str(state) + ') ').ljust(30)
          currentstate = BuildStep(ret['status']) 
          previousstate = currentstate
          sys.stdout.write(statestr(currentstate))
          while True:
            currentstate = BuildStep(ret['status'])
            if currentstate != previousstate:
              sys.stdout.write('\b' * 30)
              sys.stdout.write(statestr(currentstate))
            sys.stdout.write(Fore.GREEN + next(spinner))   # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            sys.stdout.write('\b')            # erase the last written char
            time.sleep(5)
            ret = self.build_status(id)
            if ret != None:
              if ret['iscomplete']:
                if ret['status'] == 0:
                  sys.stdout.write('\b')
                  print('...' + Fore.GREEN + 'done')
                  return ret['relativeurl'], None
                else:
                  return None, 'Could not create firmware'
            else:
              return None, 'Error contacting server'
      else:
        return None, 'Error, the server could not build your request. Do you have a valid module combination?'
    except:
      return None, sys.exc_info()[0]

  def get_firmware(self, loadbin, extractDir, savelocal):
    gzbinfile = 'firmware.tar.gz'
    gzsrcfile = 'firmware_src.tar.gz'

    relativeurl, error = self.build()

    if error == None and relativeurl != None and relativeurl != '':
      url = "https://firmware.pilotnexus.io/" + relativeurl
      if not loadbin:
        url = url.replace(gzbinfile, gzsrcfile)
      sys.stdout.write('downloading firmware{}'.format(
          ' source to ' + extractDir + '...' if not loadbin else '...'))
      sys.stdout.flush()
      if savelocal:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
          try:
            #self.sbc.cmd('mkdir -p {}'.format(self.tmp_dir), throw_on_nonzero_retcode=True)
            if not os.path.exists(self.tmp_dir):
              os.makedirs(self.tmp_dir)
            fname = '{}/{}'.format(self.tmp_dir, gzbinfile if loadbin else gzsrcfile)
            with open(fname, 'wb') as f:
              f.write(r.content)
            tar = tarfile.open(fname, "r:gz")
            if not os.path.exists(extractDir):
              os.makedirs(extractDir)
            tar.extractall(path=extractDir)
            tar.close()
          except:
            print("Error writing firmware file. Please check if you have write permissions to required directories {} and {}".format(self.tmp_dir, extractDir))
            exit(1)
          print(Fore.GREEN + 'done')
          return 0
      else:
        command = 'sudo rm -Rf {0} && mkdir -p {0} && mkdir -p {2} && wget -O {0}/pilot_tmp_fw.tar.gz {1} && tar -zxf {0}/pilot_tmp_fw.tar.gz -C {2}'.format(self.tmp_dir, url, extractDir)
        if (self.sbc.cmd_retcode(command)) == 0:
          print(Fore.GREEN + 'done')
          return 0
    else: # error building firmware
      print(Fore.RED + error)
      bugsnag.notify(Exception(error))

  def build_firmware(self):
    return self.get_firmware(True, self.tmp_dir, False)

  def program_cpld(self, binpath, binfile, erase=False):
    cmd = 'sudo chmod +x {0}/jamplayer; sudo {0}/jamplayer -a{1} -g{2},{3},{4},{5} {6}'.format(binpath, 
          'erase' if erase else 'program', 
          self.sbc.target['tdi_pin']['number'], 
          self.sbc.target['tms_pin']['number'], 
          self.sbc.target['tdo_pin']['number'], 
          self.sbc.target['tck_pin']['number'], 
          binfile)
    return self.tryrun('erasing CPLD' if erase else 'programming CPLD', 3, cmd)
  
  def serial_used(self):
    res = self.sbc.cmd('sudo fuser -v {0}'.format(self.sbc.target['tty']))
    if len(res.strip()) > 0:
      return self.tryrun('killing process accessing tty', 2, 'sudo fuser -k {0}; sleep 1'.format(self.sbc.target['tty']))
    return True

  def program_mcu(self, binpath, binfile): #use 115200, 57600, 38400 baud rates sequentially
    return self.tryrun('programming MCU', 4, 'sudo chmod +x {0}/stm32flash; sudo {0}/stm32flash -w {1} -b 115200 -g 0 -x {2} -z {3} {4}'.format(binpath, binfile, self.sbc.target['reset_pin']['number'], self.sbc.target['boot_pin']['number'], self.sbc.target['tty']))

  def program(self, program_cpld=True, program_mcu=True, cpld_file=None, mcu_file=None, var_file=None, bootmsg=False):
    res = 0
    binpath = self.binpath
    if self.sbc.remote_client:
      self.sbc.cmd_retcode('mkdir -p {}'.format(self.tmp_dir))
      if self.sbc.cmd_retcode('sudo chown -R $USER {}'.format(self.tmp_dir)) == 0:
        with scp.SCPClient(self.sbc.remote_client.get_transport()) as scp_client:
          scp_client.put(self.binpath + '/jamplayer', remote_path=self.tmp_dir)
          scp_client.put(self.binpath + '/stm32flash', remote_path=self.tmp_dir)
          scp_client.put(self.binpath + '/stm32flash', remote_path=self.tmp_dir)
          binpath = self.tmp_dir
          if cpld_file != None:
            scp_client.put(cpld_file, remote_path=os.path.join(self.tmp_dir,'cpld.jam'))
          if mcu_file != None:
            scp_client.put(mcu_file, remote_path=os.path.join(self.tmp_dir, 'stm.bin'))
          if var_file != None:
            scp_client.put(var_file, remote_path=os.path.join(self.tmp_dir, 'variables'))
      else:
        print('Error setting permissions to folder {}'.format(self.tmp_dir))
    else:
      if cpld_file != None:
        copyfile(cpld_file, os.path.join(self.tmp_dir, 'cpld.jam'))
      if mcu_file != None:
        copyfile(mcu_file, os.path.join(self.tmp_dir, 'stm.bin'))
      if var_file != None:
        copyfile(var_file, os.path.join(self.tmp_dir, 'variables'))

    if program_cpld and res == 0:
      res = self.program_cpld(binpath, Path(self.tmp_dir).joinpath('cpld.jam').as_posix(), True)

    if program_mcu and res == 0:
      self.serial_used()
      res = self.program_mcu(binpath, Path(self.tmp_dir).joinpath('stm.bin').as_posix())

    if program_cpld and res == 0:
      res = self.program_cpld(binpath, Path(self.tmp_dir).joinpath('cpld.jam').as_posix())

    print(self.reset_pilot(bootmsg))
    self.reload_drivers()

    if res == 0 and var_file != None:
      res = self.tryrun('setting PLC variables', 4, 'sudo cp {}/variables /proc/pilot/plc/varconf/variables'.format(self.tmp_dir))
      self.tryrun('setting PLC variables permanently', 4, 'sudo mkdir -p /etc/pilot; sudo cp {}/variables /etc/pilot/variables'.format(self.tmp_dir))     

    return res

  def get_help(self):
    try:
      query = u"""
      {{
        modulehelp(modules: [{}]) {{
          number
          help
          examples {{title  example}}
        }}
      }}
      """.format(','.join(['{{number: {}, fid: "{}"}}'.format(key, value['fid']) for key, value in self.eeproms.items() if value['fid'] != '']))
      ret, obj = self.ps.query_graphql(query)
      if ret == 200 and obj['data'] and obj['data']['modulehelp']:
        return obj['data']['modulehelp']
    except:
      e = sys.exc_info()[0]
      print('Could not contact Pilot Nexus API to get help data')
      bugsnag.notify(e)
    return None
