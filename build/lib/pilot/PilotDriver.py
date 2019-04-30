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

from .PilotServer import PilotServer
from .Sbc import Sbc

from shutil import copyfile

from colorama import Fore
from colorama import Style
from colorama import init

class PilotDriver():
  MODULE_COUNT = 4
  retry_count = 2
  emptystr = '-'
  pilot_driver_root = '/proc/pilot'
  tmp_dir = '/tmp/pilot'
  kernmodule_list = ['pilot', 'pilot_plc', 'pilot_tty',
                     'pilot_rtc', 'pilot_fpga', 'pilot_io', 'pilot_slcd']

  binpath = '{}/bin'.format(os.path.join(
    os.path.abspath(os.path.dirname(__file__))))

  eeproms = {}
  modules = {}

  ps = None
  sbc = None
  target = None

  def __init__(self, pilotserver: PilotServer, sbc: Sbc, target):
    self.ps = pilotserver
    self.sbc = sbc
    self.target = target

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
        while retry > 0:
          retry = retry - 1
          try:
            regfile = self.sbc.cmd(
                'cat {}/module{}/eeprom/{}'.format(self.pilot_driver_root, mod, memreg))
            modlist[mod][memreg] = ''.join(
                char for char in regfile if str.isprintable(char)).strip()
            break
          except:
            modlist[mod][memreg] = ''
            #dbg('could not read {} of module {}'.format(memreg, mod))
    return modlist

  def set_module_fid(self, number, fid):
    self.sbc.setFileContent(self.pilot_driver_root + '/module{}/eeprom/fid'.format(number), fid + '       ')

  def load_pilot_defs(self):
    try:
      self.eeproms = self.get_modules()
      query = u"""
      {{
        fid(fids:[{}]) {{
        fid
        name
        }}
        hid(hids: [{}]) {{
          module
          hid
          title
          subtitle
          description
        fids {{
          fid
          name
          isdefault
        }}
        }}
      }}
      """.format(
          ','.join(['"{}"'.format(value['fid'])
                    for key, value in self.eeproms.items() if value['fid'] != '']),
          ','.join(['{{number: {}, hid: "{}"}}'.format(key, value['hid'])
                    for key, value in self.eeproms.items()])
      )
      ret, obj = self.ps.query_graphql(query)

      if ret == 200:
        fidmap = {v['fid'].strip(): v['name'] for v in obj['data']['fid']}

        if obj['data']['hid']:
          for module in obj['data']['hid']:
            fid = self.eeproms[int(module['module'])]['fid']
            module['currentfid_nicename'] = fidmap[fid] if fid in fidmap and fid != '' else self.emptystr
            module['currentfid'] = fid
        else:
          print('error reading modules, please try again')
          return None
        return sorted(obj['data']['hid'], key=lambda x: x['module']) if ret == 200 and obj['data']['hid'] != None else None
      else:
        return None
    except:
      e = sys.exc_info()[0]
      print(e)
    return None

  def driver_loaded(self):
    return os.path.exists(self.pilot_driver_root)

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

  def reset_pilot(self):
    try:
      reset_pin = self.target['reset_pin']['number']
      # TODO check if gpio are exported as outputs first
      self.sbc.cmd('[ ! -f /sys/class/gpio/gpio{}/value ] && sudo echo "{}" > /sys/class/gpio/export'.format(reset_pin, reset_pin))
      self.sbc.cmd('sudo echo "out" > /sys/class/gpio/gpio{}/direction'.format(reset_pin))
      self.sbc.cmd('echo -n "1" > /sys/class/gpio/gpio{}/value'.format(reset_pin))
      time.sleep(2)
      self.sbc.cmd('echo -n "0" > /sys/class/gpio/gpio{}/value'.format(reset_pin))
    except:
      pass


  def check_raspberry(self):
    try:
      hardware = ['BCM2835', 'BCM2836']
      match = re.search(r'Hardware\s*?:\s*(?P<hw>[\S]*)', self.sbc.cmd('cat /proc/cpuinfo'))
      if match and match.group('hw') in hardware:
        return True
      return False
    except:
      return True #for now do nothing on error, assume that it is a raspberry

  def install_driver(self):
    try:
      match = re.match(
          r'Linux (?P<name>.*?) (?P<version>\d+.\d+.\d+-.*?) #(?P<buildnum>\d+).*?', self.sbc.cmd('uname -a'))
      if match:
        packagename = "pilot-{}{}".format(match.group('version'),
                                          match.group('buildnum'))
        print('trying to install package ''{}'''.format(packagename))
        if self.sbc.cmd_retcode("""sudo sh -c 'echo "deb http://archive.amescon.com/ ./" > /etc/apt/sources.list.d/amescon.list'""") != 0:
          return 1
        self.sbc.cmd_retcode('sudo apt-get update')
        return self.sbc.cmd_retcode('sudo apt-get install -y --allow-unauthenticated {}'.format(packagename))
      else:
        print('Could not detect your linux version')
        return 1
    except:
      bugsnag.notify(Exception(sys.exc_info()[0]), user={
          "username": self.ps.pilotcfg['username']})
    return 1

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
          self.get_kernel_info()
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
    try:
      query = u"""
      mutation {{
        build(modules: [{}]) {{
          id
          isComplete
          status
          url
        }}
      }}
      """.format(','.join(['{{number: {}, uid: "{}", fid: "{}"}}'.format(key, value['uid'], value['fid']) for key, value in self.eeproms.items() if value['fid'] != '']))
      ret, obj = self.ps.query_graphql(query)
      if ret == 200 and obj['data'] and obj['data']['build']:
        return obj['data']['build']
    except:
      pass
    return None

  def build_status(self, id):
    try:
      query = u"""
      {{
        buildstatus(id: {}) {{
          id
          isComplete
          status
          url
        }}
      }}
      """.format(id)
      ret, obj = self.ps.query_graphql(query)
      if ret == 200 and obj['data'] and obj['data']['buildstatus']:
        return obj['data']['buildstatus']
    except:
      pass
    return None

  def build(self):
    try:
      spinner = itertools.cycle(['-', '/', '|', '\\'])
      sys.stdout.write('checking if firmware is available...')
      sys.stdout.flush()
      ret = self.run_build()
      if ret != None:
        if ret['isComplete'] and ret['status'] == 0: #already built
          print(Fore.GREEN + 'available')
          return ret['url'], None
        elif ret['id'] > 0:
          print(Fore.GREEN + 'needs compilation')
          sys.stdout.write('compiling firmware ')
          sys.stdout.flush()
          while True:
            sys.stdout.write(Fore.GREEN + next(spinner))   # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            sys.stdout.write('\b')            # erase the last written char
            time.sleep(1)
            ret = self.build_status(ret['id'])
            if ret != None:
              if ret['isComplete']:
                if ret['status'] == 0:
                  sys.stdout.write('\b')
                  print('...' + Fore.GREEN + 'done')
                  return ret['url'], None
                else:
                  return None, 'Could not create firmware'
            else:
              return None, 'Error contacting server'
        else:
          return None, 'Error, could not get the build status'
    except:
      return None, sys.exc_info()[0]

  def get_firmware(self, loadbin, extractDir, savelocal):
    gzbinfile = 'firmware.tar.gz'
    gzsrcfile = 'firmware_src.tar.gz'

    url, error = self.build()

    if error == None:
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
        command = 'mkdir -p {0} && mkdir -p {2} && wget -O {0}/pilot_tmp_fw.tar.gz {1} && tar -zxf {0}/pilot_tmp_fw.tar.gz -C {2}'.format(self.tmp_dir, url, extractDir)
        if (self.sbc.cmd_retcode(command)) == 0:
          print(Fore.GREEN + 'done')
          return 0
    else: # error building firmware
      print(Fore.RED + error)
      bugsnag.notify(Exception(error))

  def build_firmware(self):
    return self.get_firmware(True, self.tmp_dir, False)

  def program_cpld(self, binfile, erase=False):
    return self.tryrun('erasing CPLD' if erase else 'programming CPLD', 2,
                 'sudo {}/jamplayer -a{} {}'.format(self.binpath, 'erase' if erase else 'program', binfile))

  def program_mcu(self, binfile): #use 115200, 57600, 38400 baud rates sequentially
    return self.tryrun('programming MCU', 4, 'sudo {}/stm32flash -w {} -b 115200 -g 0 /dev/ttyAMA0'.format(self.binpath, binfile))

  def program(self, program_cpld=True, program_mcu=True, cpld_file=None, mcu_file=None, var_file=None):
    res = 0
    if self.sbc.remote_client:
      self.sbc.cmd_retcode('mkdir -p {}'.format(self.tmp_dir))
      if self.sbc.cmd_retcode('sudo chown $USER {}'.format(self.tmp_dir)) == 0:
        with scp.SCPClient(self.sbc.remote_client.get_transport()) as scp_client:
          scp_client.put(self.binpath + '/jamplayer', remote_path=self.tmp_dir)
          scp_client.put(self.binpath + '/stm32flash', remote_path=self.tmp_dir)
          if cpld_file != None:
            scp_client.put(cpld_file, remote_path=os.path.join(self.tmp_dir,'cpld.jam'))
          if mcu_file != None:
            scp_client.put(mcu_file, remote_path=os.path.join(self.tmp_dir, 'stm.bin'))
          if var_file != None:
            scp_client.put(var_file, remote_path=os.path.join(self.tmp_dir, 'variables'))

          self.binpath = self.tmp_dir        
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
      res = self.program_cpld(os.path.join(self.tmp_dir, 'cpld.jam'), True)

    if program_mcu and res == 0:
      self.program_mcu(os.path.join(self.tmp_dir, 'stm.bin'))

    if program_cpld and res == 0:
      res = self.program_cpld(os.path.join(self.tmp_dir, 'cpld.jam'))

    self.reload_drivers()

    if var_file != None:
      res = self.tryrun('setting PLC variables', 4, 'sudo cp {}/variables /proc/pilot/plc/varconf/variables'.format(self.tmp_dir))
      self.tryrun('setting PLC variables permanently', 4, 'sudo cp {}/variables /etc/pilot/variables'.format(self.tmp_dir))     

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
