import sys
import requests
import bugsnag
import os
import yaml
import getpass
from uuid import getnode as get_mac

from colorama import Fore
from colorama import Style
from colorama import init

from Sbc import Sbc

class PilotServer():
  pilot_server = 'https://mypilot.io'
  api_path = '/api'
  pilotrc = '~/.pilotrc'
  pilotcfg = {'username': '', 'token': ''}
  pilot_dir = '/etc/pilot'
  terminal = True

  sbc = None

  def __init__(self, sbc: Sbc):
    self.sbc = sbc
    self.load_config()

  def login(self, user, password):
    try:
      address = get_mac()
      h = iter(hex(address)[2:].zfill(12))
      mac = ":".join(i + next(h) for i in h)
      res = requests.post(self.pilot_server + '/authenticate',
                          json={"username": user, "password": password, "hash": mac})
      if res.status_code == 200:
        return res.status_code, res.json()
      else:
        return res.status_code, res.text
    except:
      e = sys.exc_info()[0]

      if e is requests.exceptions.ConnectionError:
        print('Cannot connect to server!')
        bugsnag.notify(Exception(e), user={"username": self.pilotcfg['username']})
      else:
        bugsnag.notify(Exception(e), user={"username": self.pilotcfg['username']})
      return 0, e


  def authenticate(self):
    retrycount = 3
    successful = False

    while retrycount > 0 and successful == False:
      retrycount = retrycount - 1
      if self.terminal:
        user = input('Username: ')
        pswd = getpass.getpass('Password: ')
      else:
        pass  # todo - add gui for login

      self.pilotcfg['username'] = user
      ret, obj = self.login(user, pswd)
      if ret == 200 and obj and 'success' in obj:
        if obj['success'] == True:
          print(Fore.GREEN + 'Authentication successful!')
          self.pilotcfg['token'] = obj['token']
          self.save_config()
          successful = True
        else:
          print('Error authenticating')
          bugsnag.notify(Exception(obj['message'] if 'message' in obj else 'unknown error'),
                         user={"username": self.pilotcfg['username']})
          return False
      elif ret == 404:
        print('Authentication Server not found')
        bugsnag.notify(Exception("Authentication Server not found"),
                       user={"username": self.pilotcfg['username']})
        return False
      else:
        print('Invalid Username or Password')
    return True


  def query_graphql(self, s):
    try:
      headers = {
          'Authorization': "Bearer " + self.pilotcfg['token']
      }

      res = requests.post(self.pilot_server + self.api_path,
                          headers=headers,
                          json={"query": s})

      if 'Authorization' in res.headers:
        self.pilotcfg['token'] = res.headers['Authorization'].replace('Bearer ', '')
        self.save_config()
      if res.status_code == 401:  # unauthorized
        if not self.authenticate():
          # TODO Throw
          pass
        return self.query_graphql(s)

      return res.status_code, res.json()
    except:
      e = sys.exc_info()[0]
      if e is requests.exceptions.ConnectionError:
        print('Cannot connect to server!')
        bugsnag.notify(Exception('Connection Error - cannot connect to server ' +
                                self.pilot_server), user={"username": self.pilotcfg['username']})
      else:
        bugsnag.notify(Exception(e), user={"username": self.pilotcfg['username']})
      return 0, e

  def registernode(self):
    nodeconffile = self.pilot_dir + '/config.yml'
    nodeconf = {}
    nodeid = None
    apikey = None

    address = get_mac()
    h = iter(hex(address)[2:].zfill(12))
    mac = "".join(i + next(h) for i in h)

    try:
      nodeconf = yaml.load(self.sbc.getFileContent(nodeconffile))
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
      ret, obj = self.query_graphql(query)
      if ret == 200 and obj['data'] and obj['data']['nodebyid']:
        if obj['data']['nodebyid']['apikey'] != nodeconf['apikey']:
          print('The API key is wrong, correcting using your credentials.')
          apikey = obj['data']['nodebyid']['apikey']
        print('Your Node was already registered as \'{}\''.format(
            obj['data']['nodebyid']['name']))
      elif ret == 200 and not obj['data']['nodebyid']:
        apikey = None

    if apikey == None:
      ch = input(
          'Do you want to register the Node with mypilot.io? (required for remote access) (y/n)')
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
        ret, obj = self.query_graphql(query)
        if ret == 200 and obj['data'] and obj['data']['upsertNode']:
          nodeid = obj['data']['upsertNode']['id']
          apikey = obj['data']['upsertNode']['apikey']

    if nodeid != None and apikey != None:
      if nodeconf == None:
        nodeconf = {}
      nodeconf['nodeid'] = nodeid
      nodeconf['apikey'] = apikey

      self.sbc.setFileContent(nodeconffile, yaml.dump(nodeconf, default_flow_style=False))


  def load_config(self):
    self.pilotcfg = {}
    #first check if a .pilotrc file exists
    try:
      with open(os.path.expanduser(self.pilotrc), 'r') as rcfile:
        self.pilotcfg = yaml.safe_load(rcfile)
        if self.pilotcfg == None:
          self.pilotcfg = {}
        if not 'username' in self.pilotcfg:
          self.pilotcfg['username'] = ''
        if not 'token' in self.pilotcfg:
          self.pilotcfg['token'] = ''
    except:
      pass

  def save_config(self):
    try:
      with open(os.path.expanduser(self.pilotrc), 'w') as rcfile:
        yaml.dump(self.pilotcfg, rcfile)
    except:
      pass
