#!/usr/bin/env python3
from __future__ import print_function  # disables annoying pylint print warning

import sys
import json
import requests
import subprocess
import re
import shlex
import time
import os
import getpass
import argparse
import base64
import gettext
import tarfile
import yaml
import bugsnag
import logging
import paramiko
import scp

from uuid import getnode as get_mac
from bugsnag.handlers import BugsnagHandler
from threading import Thread
from colorama import Fore
from colorama import Style
from colorama import init

init(autoreset=True)  # colorama color autoreset

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'VERSION'), encoding='utf-8') as f:
  VERSION = f.read().strip()

DEBUG = False
MODULE_COUNT = 4
RETRY_COUNT = 2
EMPTYSTR = '-'

PILOT_DRIVER_ROOT = '/proc/pilot'
PILOT_SERVER = 'https://mypilot.io'

API_PATH = '/api'
PILOTRC = '~/.pilotrc'
TMP_DIR = '/tmp/pilot'
PILOT_DIR = '/etc/pilot'

REMOTE_CLIENT = None

KERNMODULE_LIST = ['pilot', 'pilot_plc', 'pilot_tty', 'pilot_rtc', 'pilot_fpga', 'pilot_io', 'pilot_slcd']

EXECVP_ENABLED = False

bugsnag.configure(
    api_key="2d614bb3561d92fbd3b6f371e39b554a",
    project_root=".",
    app_version=VERSION,
    release_stage='production'
)

logger = logging.getLogger()
handler = BugsnagHandler()
# send only ERROR-level logs and above
handler.setLevel(logging.ERROR)
logger.addHandler(handler)


#config file
pilotcfg = { 'username': '', 'token': ''}
terminal = True
eeproms = {}
modules = {}

############## PROC FILE ACCESS #####################

def dbg(*text):
  if DEBUG:
    print(*text)

def exit_app(retcode):
  global REMOTE_CLIENT
  if REMOTE_CLIENT != None:
    REMOTE_CLIENT.close()
  sys.exit(retcode)

def cmd(command, throw_on_nonzero_retcode=False):
  global REMOTE_CLIENT
  if not REMOTE_CLIENT:
    p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    output, err = p.communicate()

    if throw_on_nonzero_retcode and p.returncode != 0:
      raise Exception('Cound not execute {} \nError: {}'.format(command, err))

    return output
  else:
    chan = REMOTE_CLIENT.get_transport().open_session()
    _stdin, stdout, stderr = chan.exec_command(command)
    chan.close()
    if throw_on_nonzero_retcode and chan.recv_exit_status() != 0:
      raise Exception('Cound not execute {} \nError: {}'.format(command, stderr))

    return ''.join(stdout)

def cmd_retcode(command):
  global REMOTE_CLIENT
  if not REMOTE_CLIENT:
    return subprocess.run(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
  else:
    chan = REMOTE_CLIENT.get_transport().open_session()
    chan.exec_command(command)
    chan.close()
    return chan.recv_exit_status()

def get_modules():
  memregs = ['uid', 'hid', 'fid']
  strmlist = list(filter(None, cmd('find /proc/pilot/module* -maxdepth 0 -printf "%f\n"').split('\n')))
  matches = filter(None, map(lambda x: re.match('module(\d+)', x), strmlist))
  modlist = {int(x.group(1)): {'uid': '', 'hid': '', 'fid': ''} for x in matches}
  for mod in modlist:
    for memreg in memregs:
      retry = RETRY_COUNT
      while retry > 0:
        retry = retry - 1
        try:
          regfile = cmd('cat {}/module{}/eeprom/{}'.format(PILOT_DRIVER_ROOT, mod, memreg))
          modlist[mod][memreg] = ''.join(char for char in regfile if str.isprintable(char)).strip()
          break
        except:
          modlist[mod][memreg] = ''
          dbg('could not read {} of module {}'.format(memreg, mod))
  return modlist

def load_config():
  global pilotcfg
  #first check if a .pilotrc file exists
  try:
    with open(os.path.expanduser(PILOTRC), 'r') as rcfile:
      pilotcfg = yaml.safe_load(rcfile)
      if pilotcfg == None:
        pilotcfg = {}
      if not 'username' in pilotcfg:
        pilotcfg['username'] = ''
      if not 'token' in pilotcfg:
        pilotcfg['token'] = ''      
  except:
    pass

def save_config():
  global pilotcfg
  try:
    with open(os.path.expanduser(PILOTRC), 'w') as rcfile:
      yaml.dump(pilotcfg, rcfile)
  except:
    pass

def login(user, password):
  global pilotcfg
  try:
    address = get_mac()
    h = iter(hex(address)[2:].zfill(12))
    mac = ":".join(i + next(h) for i in h)
    res = requests.post(PILOT_SERVER + '/authenticate', json={"username": user, "password": password, "hash": mac})
    if res.status_code == 200:
      return res.status_code, res.json()
    else:
      return res.status_code, res.text
  except:
    e = sys.exc_info()[0]

    if e is requests.exceptions.ConnectionError:
      print('Cannot connect to server!')
      bugsnag.notify(Exception(e), user={"username": pilotcfg['username']})
    else:
      bugsnag.notify(Exception(e), user={"username": pilotcfg['username']})
    return 0, e

def authenticate():
  global pilotcfg
  global terminal
  retrycount = 3
  successful = False

  while retrycount > 0 and successful == False:
    retrycount = retrycount - 1
    if terminal:
      user = input('Username: ')
      pswd = getpass.getpass('Password: ')
    else:
      pass #todo - add gui for login

    pilotcfg['username'] = user
    ret, obj = login(user, pswd)
    if ret == 200 and obj and 'success' in obj:
      if obj['success'] == True:
        print(Fore.GREEN + 'Authentication successful!')
        pilotcfg['token'] = obj['token']
        save_config()
        successful = True
      else:
        print('Error authenticating')
        bugsnag.notify(Exception(obj['message'] if 'message' in obj else 'unknown error'),
                      user={"username": pilotcfg['username']})
        exit_app(2)
    elif ret == 404:
      print('Authentication Server not found')
      bugsnag.notify(Exception("Authentication Server not found"),
                    user={"username": pilotcfg['username']})
      exit_app(2)
    else:
      print('Invalid Username or Password')

def query_graphql(s):
  global pilotcfg
  try:
    headers = {
        'Authorization': "Bearer " + pilotcfg['token']
    }

    res = requests.post(PILOT_SERVER + API_PATH,
                        headers=headers,
                        json={"query": s})

    if 'Authorization' in res.headers:
      pilotcfg['token'] = res.headers['Authorization'].replace('Bearer ', '')
      save_config()
    if res.status_code == 401: #unauthorized
      authenticate()
      return query_graphql(s)

    return res.status_code, res.json()
  except:
    e = sys.exc_info()[0]
    if e is requests.exceptions.ConnectionError:
      print('Cannot connect to server!')
      bugsnag.notify(Exception('Connection Error - cannot connect to server ' +
        PILOT_SERVER), user={"username": pilotcfg['username']})
    else:
      bugsnag.notify(Exception(e), user={"username": pilotcfg['username']})
    return 0, e

def load_pilot_defs():
  global eeproms
  eeproms = get_modules()
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
                for key, value in eeproms.items() if value['fid'] != '']),
      ','.join(['{{number: {}, hid: "{}"}}'.format(key, value['hid'])
                for key, value in eeproms.items()])
  )
  ret, obj = query_graphql(query)

  if ret == 200:
    fidmap = {v['fid'].strip(): v['name'] for v in obj['data']['fid']}
    
    if obj['data']['hid']:
      for module in obj['data']['hid']:
        fid = eeproms[int(module['module'])]['fid']
        module['currentfid'] = fidmap[fid] if fid in fidmap and fid != '' else EMPTYSTR
    else:
      print('error reading modules, please try again')
      exit_app(1)

    return sorted(obj['data']['hid'], key=lambda x: x['module']) if ret == 200 and obj['data']['hid'] != None else None


def driver_loaded():
  return os.path.exists(PILOT_DRIVER_ROOT)

def getFileContent(file):
  return cmd('sudo cat {}'.format(file), True)

def setFileContent(file, content):
  return cmd('printf "{}" | sudo tee {} >/dev/null'.format(content.replace('\n', '\\n').replace('"', '\"'), file), True)

def getModuleEeprom(module, memregion):
  try:
    return getFileContent('{}/module{}/eeprom/{}'.format(PILOT_DRIVER_ROOT, module, memregion))
  except:
    return ''

def build(loadbin = True, buildSilent = False, extractDir = TMP_DIR, savelocal = False):
  global eeproms
  gzbinfile = 'firmware.tar.gz'
  gzsrcfile = 'firmware_src.tar.gz'
  try:
    query = u"""
    {{
      build(modules: [{}]) {{
        guid
        url
        successful
      }}
    }}
    """.format(','.join(['{{number: {}, uid: "{}", fid: "{}"}}'.format(key, value['uid'], value['fid']) for key, value in eeproms.items() if value['fid'] != '']))
    ret, obj = query_graphql(query)
    if ret == 200 and obj['data'] and obj['data']['build']:
      if obj['data']['build']['successful']:
        if obj['data']['build']['guid']:
          if not buildSilent:
            print('building firmware...', end='')
            sys.stdout.flush()
          return 1      
        elif obj['data']['build']['url']:
          url = obj['data']['build']['url']
          if not loadbin:
            url = url.replace(gzbinfile, gzsrcfile)
          sys.stdout.write('downloading firmware {}'.format('source to ' + extractDir + ' ...' if not loadbin else ' ...'))
          sys.stdout.flush()
          if savelocal:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
              if not os.path.exists(TMP_DIR):
                os.makedirs(TMP_DIR)
              fname = '{}/{}'.format(TMP_DIR,
                                    gzbinfile if loadbin else gzsrcfile)
              with open(fname, 'wb') as f:
                f.write(r.content)
              tar = tarfile.open(fname, "r:gz")
              if not os.path.exists(extractDir):
                os.makedirs(extractDir)
              tar.extractall(path=extractDir)
              tar.close()
              print(Fore.GREEN + 'done')
              return 0
          else:
            command = 'mkdir -p {0} && mkdir -p {2} && wget -O {0}/pilot_tmp_fw.tar.gz {1} && tar -zxf {0}/pilot_tmp_fw.tar.gz -C {2}'.format(TMP_DIR, url, extractDir)
            if (cmd_retcode(command)) == 0:
              print (Fore.GREEN + 'done')
              return 0

          print(Fore.RED + 'error')
          exit_app(2)
      else:
          print(Fore.RED + 'failed on server')
          bugsnag.notify(Exception('Error building firmware on server side'), user={"username": pilotcfg['username']})
          exit_app(2)
    else:
      print('Error building firmware.')
      bugsnag.notify(Exception('Error building firmware'), user={"username": pilotcfg['username']})
      exit_app(3)
  except:
    bugsnag.notify(Exception(sys.exc_info()[0]), user={"username": pilotcfg['username']})
    print('Oops! An error occured downloading the firmware. We have been notified of the problem.')
    exit_app(3)

def registernode():
  nodeconffile = PILOT_DIR + '/config.yml'
  nodeconf = {}
  nodeid = None
  apikey = None

  address = get_mac()
  h = iter(hex(address)[2:].zfill(12))
  mac = "".join(i + next(h) for i in h)

  try:
    nodeconf = yaml.load(getFileContent(nodeconffile))
  except:
    nodeconf = None
  
  if nodeconf != None and nodeconf['nodeid'] and nodeconf['apikey']:
    nodeid = nodeconf['nodeid']
    apikey = nodeconf['apikey']
    query = u"""
    {{
      nodebyid(id: "{}") {{
        name
        apikey
      }}
    }}
    """.format(nodeconf['nodeid'])
    ret, obj = query_graphql(query)
    if ret == 200 and obj['data'] and obj['data']['nodebyid']:
      if obj['data']['nodebyid']['apikey'] != nodeconf['apikey']:
        print('The API key is wrong, correcting using your credentials.')
        apikey = obj['data']['nodebyid']['apikey']
      print('Your Node was already registered as \'{}\''.format(obj['data']['nodebyid']['name']))
    elif ret == 200 and not obj['data']['nodebyid']:
      apikey = None

  if apikey == None:
    ch = input('Do you want to register the Node with mypilot.io? (required for remote access) (y/n)')
    # ch = read_single_keypress()
    if ch.strip() == 'y':
      #Register unassigned Node
      name = input('Enter the Name for this Node (Unassigned Node): ')
      if name == '':
        name = 'Unassigned Node'
      query = u"""
      mutation {{
        upsertNode (node: {{
          name: "{}",
          mac: "{}"}} ) {{
         id
         apikey
       }}
      }}
      """.format(name, mac)
      ret, obj = query_graphql(query)
      if ret == 200 and obj['data'] and obj['data']['upsertNode']:
        nodeid = obj['data']['upsertNode']['id']
        apikey = obj['data']['upsertNode']['apikey']

  if nodeid != None and apikey != None:
    if nodeconf == None:
      nodeconf = {}
    nodeconf['nodeid'] = nodeid
    nodeconf['apikey'] = apikey

    setFileContent(nodeconffile, yaml.dump(nodeconf, default_flow_style=False))

def tryrun(text, retries, cmd):
  print(text + '...', end='')
  sys.stdout.flush()
  while retries > 0:
    retries = retries - 1
    try:
      if cmd_retcode(cmd) == 0:
        print(Fore.GREEN + 'done')
        return 0
    except:
      print('.', end='')
      sys.stdout.flush()
  print(Fore.RED + 'failed')
  return 1

def reload_drivers():
  ok = True
  print('reloading drivers...', end='')
  sys.stdout.flush()
  for module in KERNMODULE_LIST[::-1]:
    try:
      cmd_retcode("sudo modprobe -r {}".format(module))
    except:
      pass

  for module in KERNMODULE_LIST:
    try:
      cmd_retcode("sudo modprobe {}".format(module))
    except:
      ok = False

  if ok:
    print(Fore.GREEN + 'done')
  else:
    print(Fore.RED + 'failed')

  return ok

def program():
  binpath = '{}/bin'.format(os.path.join(os.path.abspath(os.path.dirname(__file__))))
  
  if REMOTE_CLIENT:
    with scp.SCPClient(REMOTE_CLIENT.get_transport()) as scp_client:
      scp_client.put(binpath + '/jamplayer', remote_path=TMP_DIR)
      scp_client.put(binpath + '/stm32flash', remote_path=TMP_DIR)
      binpath = TMP_DIR

  res = tryrun('erasing CPLD', 2, 'sudo {}/jamplayer -aerase {}/cpld.jam'.format(binpath, TMP_DIR))
  if res != 0:
    return 1
  res = tryrun('programming MCU', 4, 'sudo {}/stm32flash -w {}/stm.bin -g 0 /dev/ttyAMA0'.format(binpath, TMP_DIR))
  if res != 0:
    return 1
  res = tryrun('programming CPLD', 2, 'sudo {}/jamplayer -aprogram {}/cpld.jam'.format(binpath, TMP_DIR))
  reload_drivers()
  if res != 0:
    return 1

def need_sudo_pw():
  try:
    if cmd_retcode('sudo -n true') == 0:
      return False
  except:
    pass
  return True

def load_driver():
  try:
    match = re.match(r'Linux (?P<name>.*?) (?P<version>\d+.\d+.\d+-.*?) #(?P<buildnum>\d+)', cmd('uname -a'))
    if match:
      packagename = "pilot-{}{}".format(match.group('version'), match.group('buildnum'))
      print('trying to install package ''{}'''.format(packagename))
      if cmd_retcode("""sudo sh -c 'echo "deb http://archive.amescon.com/ ./" > /etc/apt/sources.list.d/amescon.list'""") != 0:
        return 1
      cmd_retcode('sudo apt-get update')
      return cmd_retcode('sudo apt-get install -y --allow-unauthenticated {}'.format(packagename))
    else:
      print('Could not detect your linux version')
      return 1
  except:
    bugsnag.notify(Exception(sys.exc_info()[0]), user={
        "username": pilotcfg['username']})
  return 1

# def run(checksudo):
#   global terminal
#   if os.geteuid() != 0 and checksudo:
#     #we are not root, check if we need a password
#     if need_sudo_pw() and EXECVP_ENABLED:
#       if terminal:
#         os.execvp("sudo", ["sudo"] + sys.argv)
#       else:
#         try:
#           os.execvp("gksudo", ["gksudo"] + sys.argv)
#         except:
#           os.execvp("sudo", ["sudo"] + sys.argv)
#     else:
#       if not EXECVP_ENABLED:
#         print("Please start again with sudo permissions")
#         exit_app(1)
#       else:
#         os.execvp("sudo", ["sudo"] + sys.argv)
#         exit_app(0)

#   if os.environ.get('DISPLAY') == None:
#     terminal = True

#   if terminal:
#     main()
#   else:
#     pass # webserver starts here

def read_single_keypress():
    """Waits for a single keypress on stdin.

    This is a silly function to call if you need to do it a lot because it has
    to store stdin's current setup, setup stdin for reading single keystrokes
    then read the single keystroke then revert stdin back after reading the
    keystroke.

    Returns the character of the key that was pressed (zero on
    KeyboardInterrupt which can happen when a signal gets handled)

    """
    import termios
    import fcntl
    import sys
    import os
    fd = sys.stdin.fileno()
    # save old state
    flags_save = fcntl.fcntl(fd, fcntl.F_GETFL)
    attrs_save = termios.tcgetattr(fd)
    # make raw - the way to do this comes from the termios(3) man page.
    attrs = list(attrs_save)  # copy the stored version to update
    # iflag
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK
                  | termios.ISTRIP | termios.INLCR | termios. IGNCR
                  | termios.ICRNL | termios.IXON)
    # oflag
    attrs[1] &= ~termios.OPOST
    # cflag
    attrs[2] &= ~(termios.CSIZE | termios. PARENB)
    attrs[2] |= termios.CS8
    # lflag
    attrs[3] &= ~(termios.ECHONL | termios.ECHO | termios.ICANON
                  | termios.ISIG | termios.IEXTEN)
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    # turn off non-blocking
    fcntl.fcntl(fd, fcntl.F_SETFL, flags_save & ~os.O_NONBLOCK)
    # read a single keystroke
    try:
        ret = sys.stdin.read(1)  # returns a single character
    except KeyboardInterrupt:
        ret = 0
    finally:
        # restore old state
        termios.tcsetattr(fd, termios.TCSAFLUSH, attrs_save)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags_save)
    return ret

def arguments(parser):
  # parser.add_argument('--terminal', '-t', action='store_true', help='forces the terminal version instead of GUI')
  parser.add_argument('--server', '-s', default=None, dest='server',
                      help='Alternative URL for the pilot server API to contact')
  parser.add_argument('--source', '-c', default=None, dest='source',
                      help='Download Sourcecode only')
  parser.add_argument('--host', '-o', default=None, dest='host',
                      help='Hostname to remote configure')
  parser.add_argument('--user', '-u', default='pi', dest='user',
                      help='Remote SSH User (default: pi)')
  parser.add_argument('--password', '-p', default='raspberry', dest='password',
                      help='Remote SSH Password (default: raspberry)')

def reset_pilot():
  try:
    with open('/sys/class/gpio/gpio17/value', 'w') as f:
      f.write('1')
    time.sleep(2)
    with open('/sys/class/gpio/gpio17/value', 'w') as f:
      f.write('0')
  except:
    pass

def check_driver():
  if cmd_retcode('ls ' + PILOT_DRIVER_ROOT) != 0:
    print('Pilot driver is not loaded. Trying to install')
    if load_driver() == 0:
      print('Pilot driver installed, please reboot your system')
      exit_app(0)
    else:
      exit_app(1)

def wait_build(loadbin, extractDir = TMP_DIR, savelocal = False):
  silent = False
  while build(loadbin, silent, extractDir, savelocal) == 1:
    silent = True
    time.sleep(5)
    
def main(args):
  global modules
  global PILOT_SERVER
  global REMOTE_CLIENT

  print('Version {}'.format(VERSION))
  # print('Amescon/Daniel Amesberger 2018, www.amescon.com')

  if args.server != None:
    PILOT_SERVER = args.server

  if args.host != None:
    print('Connecting to remote host {}'.format(args.host))
    try:
      client = paramiko.SSHClient()
      client.load_system_host_keys()
      client.set_missing_host_key_policy(paramiko.WarningPolicy())
      client.connect(args.host, username=args.user, password=args.password)
      REMOTE_CLIENT = client
      if need_sudo_pw():
        print('we need sudo on remote machine (without interactive authentication)')
        exit_app(1)
      #REMOTE_CLIENT.exec_command('uname - a')
      #print(REMOTE_CLIENT)
    except:
      print('failed to connect to remote client.')
      print(sys.exc_info()[0])
      exit_app(1)

  check_driver()
  load_config()
  modules = load_pilot_defs()
  if modules != None:
    for module in modules:
      print('Module {}: {} {}'.format(module['module'], module['currentfid'], '*' if len(module['fids']) > 1 else ''))

    if args.source == None:
      print('Do you want to build and program the PiloT Mainboard Firmware? (y/n): ', end='')
      ch = read_single_keypress()
      print (ch)
      if ch == 'y':
        wait_build(True)
        program()
        reset_pilot()
    else:
      srcpath = os.path.abspath(args.source)
      wait_build(False, srcpath, True)

    registernode()
    # addnode()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Setup PiloT')
  arguments(parser)
  main(parser.parse_args())
