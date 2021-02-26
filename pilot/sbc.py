import lazy_import
from colorama import Fore
os = lazy_import.lazy_module("os")
paramiko = lazy_import.lazy_module("paramiko")
logging = lazy_import.lazy_module("logging")
subprocess = lazy_import.lazy_module("subprocess")
fnmatch = lazy_import.lazy_module("fnmatch")
json = lazy_import.lazy_module("json")

class Sbc():
  logging.getLogger("paramiko").setLevel(logging.ERROR)

  remote_client = None
  args = None
  targethardwarelist = {}
  target = {}

  def __init__(self, args):
    self.args = args

    # load target hardware list
    for root, _dirnames, filenames in os.walk(os.path.dirname(os.path.realpath(__file__))):
      for filename in fnmatch.filter(filenames, 'targethardware.json'):
        with open(os.path.join(root, filename)) as obj:
          self.targethardwarelist = json.load(obj)['targethardware']

  def __enter__(self):
    usecredentials = False
    usekeyfile = False
    if 'user' in self.args and self.args.user and 'sshkey_file' in self.args and self.args.sshkey_file != '/':
      if self.args.sshkey_file == None:
        self.args.sshkey_file = os.path.expanduser('~/.ssh/id_rsa.pub')
      usekeyfile = True
    elif 'user' in self.args and self.args.user and 'password' in self.args and self.args.password:
      usecredentials = True
    if 'hardware' in self.args and self.args.hardware:
      self.target = next(x for x in self.targethardwarelist if x['name'] == self.args.hardware)
      if usekeyfile:
        self.connect_with_key(self.args.user, self.args.sshkey_file)
      elif usecredentials:
        self.connect(self.args.user, self.args.password)
      else:
        self.connect(self.target['defaultuser'], self.target['defaultpassword'])
    else:
      connected = False
      for hw in self.targethardwarelist:
        try:
          user = self.args.user if usecredentials else hw['defaultuser']
          if usekeyfile:
            self.connect_with_key(user, self.args.sshkey_file)
            connected = True
          else:
            password = self.args.password if usecredentials else hw['defaultpassword']
            self.connect(user, password)
            connected = True
          break
        except: 
          print(Fore.YELLOW + 'failed')
      if not connected:
        print('Could not connect to target') 
        exit(1)
        #raise Exception('Could not connect to target') 
      for hw in self.targethardwarelist:
        try:  
          if self.cmd(hw['hardware']['runcheck']).strip() == hw['hardware']['checkresult']:
            self.target = hw
            print("{} detected".format(self.target['fullname']))
            break
        except: 
          pass
    if not self.target:
      if self.remote_client != None:
        self.remote_client.close()
      print('Could not detect target hardware. If you want to use a remote node use the --node parameter to specify the IP address.')
      #raise Exception('Could not detect target hardware. If you want to use a remote node use the --node parameter to specify the IP address.')
      exit(1)
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    if self.remote_client != None:
      self.remote_client.close()

  def connect_with_key(self, user, key_filename):
    if 'node' in self.args and self.args.node != None:
      print('trying to connect to {} with user {} using keyfile {}...'.format(self.args.node, user, key_filename), end='')
      client = paramiko.SSHClient()
      client.load_system_host_keys()
      #client.set_missing_host_key_policy(paramiko.WarningPolicy())
      client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      client.connect(self.args.node, username=user, key_filename=key_filename)
      self.remote_client = client
      print(Fore.GREEN + 'succeeded')
    return self

  def connect(self, user, password):
    if 'node' in self.args and self.args.node != None:
      print('trying to connect to {} with user {}...'.format(self.args.node, user), end='')
      client = paramiko.SSHClient()
      client.load_system_host_keys()
      #client.set_missing_host_key_policy(paramiko.WarningPolicy())
      client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      client.connect(self.args.node, username=user, password=password)
      self.remote_client = client
      print(Fore.GREEN + 'succeeded')
    return self
    
  def need_sudo_pw(self):
    try:
      if self.cmd_retcode('sudo -n true') == 0:
        return False
    except:
      pass
    return True

  def cmd(self, command, throw_on_nonzero_retcode=False):
    if not self.remote_client:
      p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          )
      output, err = p.communicate()
      output = output.decode('utf-8', 'ignore')
      if throw_on_nonzero_retcode and p.returncode != 0:
        raise Exception('Cound not execute {} \nError: {}'.format(command, err))

      return output
    else:
      ret = -1
      chan = self.remote_client.get_transport().open_session()
      chan.exec_command(command)
      try:
        stdout = chan.makefile('rb').read().decode('ascii', 'replace')
        stderr = chan.makefile_stderr('rb').read().decode('ascii', 'replace')
      except Exception as e: 
        print(str(e))
      ret = chan.recv_exit_status()
      chan.close()
      if throw_on_nonzero_retcode and ret != 0:
        raise Exception('Cound not execute {} \nError: {}'.format(command, stderr))
      return stdout

  def cmd_retcode(self, command):
    if not self.remote_client:
      return subprocess.run(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    else:
      ret = -1
      chan = self.remote_client.get_transport().open_session()
      chan.exec_command(command)
      ret = chan.recv_exit_status()
      chan.close()
      return ret

  def reboot(self):
    return self.cmd_retcode('sudo reboot')

  def getFileContent(self, file):
    return self.cmd('sudo cat {}'.format(file), True)

  def setFileContent(self, file, content):
    cmdstr = 'sudo mkdir -p "{}" && printf "{}" | sudo tee {} >/dev/null'.format(os.path.dirname(file), content.replace('"', '\\"'), file)
    return self.cmd(cmdstr, True)

  def stop_service(self, name, verbose = True):
    trystop = False

    servicestarted = self.cmd_retcode('sudo systemctl is-active --quiet ' + name)
    if servicestarted == 0:
      if verbose:
        print(name + ' running, stopping...', end='')
        servicestopped = self.cmd_retcode('sudo service ' + name + ' stop')
        trystop = True # also set to true if stopping was unsucessful
        if verbose:
          if servicestopped == 0:
            print(Fore.GREEN + 'done')
          else:
            print(Fore.RED + 'failed')
    return trystop


  def start_service(self, name, verbose = True):
    if verbose:
      print('starting ' + name + '...', end='')
    servicestarted = self.cmd_retcode('sudo service ' + name + ' start')
    if verbose:
      if servicestarted == 0:
        print(Fore.GREEN + 'done')
      else:
        print(Fore.RED + 'failed')


  def check_hardware(self):
    if not 'hardware' in self.args:
      try:
        for hw in targethardwarelist:
          self.sbc.cmd(hw['hardware']['runcheck'])
      except:
        return True #for now do nothing on error, assume that it is a raspberry