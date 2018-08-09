import paramiko
import subprocess

class Sbc():
  remote_client = None
  args = None

  def __init__(self, args):
    self.args = args

  def __enter__(self):
    if self.args.host != None:
      print('Connecting to remote host {}'.format(self.args.host))
      client = paramiko.SSHClient()
      client.load_system_host_keys()
      client.set_missing_host_key_policy(paramiko.WarningPolicy())
      client.connect(self.args.host, username=self.args.user, password=self.args.password)
      self.remote_client = client
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    if self.remote_client != None:
      self.remote_client.close()

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
      _stdin, stdout, _stderr = self.remote_client.exec_command(command)
      return ''.join(stdout)

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
    return self.cmd('printf "{}" | sudo tee {} >/dev/null'.format(content.replace('\n', '\\n').replace('"', '\\"'), file), True)
