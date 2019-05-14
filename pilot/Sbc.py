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
    if 'hardware' in self.args and self.args.hardware:
      self.target = next(x for x in self.targethardwarelist if x['name'] == self.args.hardware)
      self.connect(self.args.user, self.args.password)
    else:
      for hw in self.targethardwarelist:
        try:
          user = self.args.user if 'user' in self.args and self.args.user else hw['defaultuser']
          password = self.args.password if 'password' and self.args.user in self.args else hw['defaultpassword']
          self.connect(user, password)
          print(Fore.GREEN + 'succeeded')
          if self.cmd(hw['hardware']['runcheck']).strip() == hw['hardware']['checkresult']:
            self.target = hw
            print("{} detected".format(self.target['fullname']))
            break
        except: 
          print(Fore.YELLOW + 'failed')
    if not self.target:
      print('Could not detect target hardware, exiting.')
      if self.remote_client != None:
        self.remote_client.close()
      exit(1)
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    if self.remote_client != None:
      self.remote_client.close()

  def connect(self, user, password):
    if 'host' in self.args and self.args.host != None:
      print('trying to connect to {} with user {}...'.format(self.args.host, user), end='')
      client = paramiko.SSHClient()
      client.load_system_host_keys()
      client.set_missing_host_key_policy(paramiko.WarningPolicy())
      client.connect(self.args.host, username=user, password=password)
      self.remote_client = client
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
                          universal_newlines=True)
      output, err = p.communicate()

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


  def getFileContent(self, file):
    return self.cmd('sudo cat {}'.format(file), True)

  def setFileContent(self, file, content):
    cmdstr = 'sudo mkdir -p "{}" && printf "{}" | sudo tee {} >/dev/null'.format(os.path.dirname(file), content.replace('"', '\\"'), file)
    return self.cmd(cmdstr, True)

  def check_hardware(self):
    if not 'hardware' in self.args:
      try:
        for hw in targethardwarelist:
          self.sbc.cmd(hw['hardware']['runcheck'])
      except:
        return True #for now do nothing on error, assume that it is a raspberry