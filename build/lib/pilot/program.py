#!/usr/bin/env python3
from __future__ import print_function  # disables annoying pylint print warning

import sys
import json
import subprocess
import paramiko
import scp
import os
import argparse

def arguments(parser):
  parser.add_argument('--directory', '-d', default='.', dest='dir',
                      help='Directory for the binary files to program')
  parser.add_argument('--host', '-o', default=None, dest='host',
                      help='Hostname to remote configure')
  parser.add_argument('--user', '-u', default='pi', dest='user',
                      help='Remote SSH User (default: pi)')
  parser.add_argument('--password', '-p', default='raspberry', dest='password',
                      help='Remote SSH Password (default: raspberry)')

REMOTE_CLIENT = None

def exit_app(retcode):
  global REMOTE_CLIENT
  if REMOTE_CLIENT != None:
    REMOTE_CLIENT.close()
  sys.exit(retcode)

def cmd(command):
  global REMOTE_CLIENT
  if not REMOTE_CLIENT:
    p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    output, _err = p.communicate()
    return output
  else:
    _stdin, stdout, _stderr = REMOTE_CLIENT.exec_command(command)
    return ''.join(stdout)

def cmd_retcode(command):
  global REMOTE_CLIENT
  if not REMOTE_CLIENT:
    return subprocess.run(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
  else:
    chan = REMOTE_CLIENT.get_transport().open_session()
    chan.exec_command(command)
    return chan.recv_exit_status()

def need_sudo_pw():
  try:
    if cmd_retcode('sudo -n true') == 0:
      return False
  except:
    pass
  return True

def main(args):
  global REMOTE_CLIENT

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

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Program Pilot')
  arguments(parser)
  main(parser.parse_args())
