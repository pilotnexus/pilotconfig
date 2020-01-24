import lazy_import

import os
import jwt
import time
import datetime
sys = lazy_import.lazy_module("sys")
time = lazy_import.lazy_module("time")
requests = lazy_import.lazy_module("requests")
bugsnag = lazy_import.lazy_module("bugsnag")
os = lazy_import.lazy_module("os")
yaml = lazy_import.lazy_module("yaml")
getpass = lazy_import.lazy_module("getpass")
json = lazy_import.lazy_module("json")
qrcode_terminal = lazy_import.lazy_module("qrcode_terminal")
get_mac = lazy_import.lazy_callable("uuid.getnode")
#from uuid import getnode as get_mac
Enum = lazy_import.lazy_callable("enum.Enum")
#from enum import Enum

from colorama import Fore
from colorama import Style
from colorama import init

from .sbc import Sbc

class RegisterNodeStatus(Enum):
  FAILED = -1
  OK = 0
  CODE_NOT_FOUND = 1
  COULD_NOT_CREATE = 2
  COULD_NOT_UPDATE = 3
  MAC_ALREADY_USED = 4

class PilotServer():
  pilot_server = 'https://api.pilotnexus.io/v1'
  api_path = '/query'
  pilot_home_dir = os.path.expanduser('~/.pilot')
  authfile = os.path.join(pilot_home_dir, 'auth.json')
  pilotcfg = {'username': '', 'token': ''}
  pilot_dir = '/etc/pilot'
  nodeconfname = '/pilotnode.yml'

  client_id = 'hG0Kh6oMY6A2dMUjyjAbTQPTcd8syl58'
  audience = [ "https://api.pilotnexus.io", "https://amescon.eu.auth0.com/userinfo" ]

  keys = None
  tokenset = None

  terminal = True

  sbc = None

  def __init__(self, sbc: Sbc):
    self.sbc = sbc
    if not os.path.exists(self.pilot_home_dir):
      os.makedirs(self.pilot_home_dir)
    
    try:
      with open(self.authfile) as authfile:
        self.tokenset = json.load(authfile)
    except:
      pass
    
    try:
      keys = requests.get("https://amescon.eu.auth0.com/.well-known/jwks.json").json()['keys']
      self.keys = [ key for key in keys if key['alg'] == 'RS256' ][0]
    except:
      pass

  def query_graphql(self, s, apikey=None):
    try:
      headers = {}

      if apikey:
        headers = {
            'Authorization': 'Node-ApiKey ' + apikey
        }

      res = requests.post(self.pilot_server + self.api_path,
                          headers=headers,
                          json={"query": s})

      return res.status_code, res.json()
    except:
      type, value, traceback = sys.exc_info()
      if type is requests.exceptions.ConnectionError:
        print('Cannot connect to server!')
        bugsnag.notify(Exception('Connection Error - cannot connect to server ' +
                                self.pilot_server))
      else:
        bugsnag.notify(Exception(type))
      return 0, value

  def loadnodeconf(self):
    nodeconffile = self.pilot_dir + self.nodeconfname
    nodeconf = None
    try:
      nodeconf = yaml.load(self.sbc.getFileContent(nodeconffile), Loader=yaml.FullLoader)
    except:
      nodeconf = None
    return nodeconf

  def savenodeconf(self, nodeconf):
    nodeconffile = self.pilot_dir + self.nodeconfname
    nodeconfcontent = yaml.dump(nodeconf, default_flow_style=False)
    return self.sbc.setFileContent(nodeconffile, nodeconfcontent)

  def authenticate(self):
    payload = {'client_id': self.client_id, 'scope':'openid email offline_access', 'prompt': 'consent' }
    headers = { 'content-type': "application/x-www-form-urlencoded" }

    try:
      response = requests.post("https://amescon.eu.auth0.com/oauth/device/code", data=payload, headers=headers).json()
    
      print("\n\n")
      print("Open {}{}{} and enter".format(Style.BRIGHT, response['verification_uri'], Style.NORMAL))
      print("\n\n")
      print("""=======>      {}{}{}       <=======""".format(Style.BRIGHT, response['user_code'], Style.NORMAL))
      print("\n\nor scan this code with your Camera app to skip entering the code")
      qrcode_terminal.draw(response['verification_uri_complete'])
      print("note: this code expires in {} minutes".format(response['expires_in'] / 60))

      payload2 = { 'grant_type': "urn:ietf:params:oauth:grant-type:device_code", 
                   'client_id': payload['client_id'], 'device_code': response['device_code'] }

      done = None
      interval = int(response['interval'])

      while (not done):
        response2 = requests.post("https://amescon.eu.auth0.com/oauth/token", data=payload2, headers=headers).json()
        if 'error' in response2:
          if response2['error'] == 'authorization_pending':
            time.sleep(interval)
          elif response2['error'] == 'access_denied':
            print(Fore.RED + 'Flow cancelled')
            done = True
          elif response2['error'] == 'expired_token':
            print(Fore.RED + 'Token is expired')
            done = True
          else:
            print(Fore.RED + 'Error {}; {}'.format(response2['error'], response2['error_description']))
            done = True
        elif 'access_token' in response2:
          print(Fore.GREEN + "\n\nYour device was sucessfully authorized.")
          self.tokenset = response2
          with open(self.authfile, 'w') as authfile:
            json.dump(self.tokenset, authfile)

    except Exception as e: 
      print('Error authenticating the device {}'.format(e))
      print(e)
  
  def decode(self):
    if self.tokenset != None and self.keys != None:
      try:
        pubkey = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(self.keys))
        return  jwt.decode(self.tokenset['access_token'], pubkey, algorithms='RS256', audience = self.audience) #, audience=self.config.CLIENT_ID) 
      except Exception as e:
        print('error decoding')
        print(e)
    return None


  def registernode(self, fwconfig):
    if self.tokenset == None:
      self.authenticate()
    
    decoded = self.decode()
    if decoded != None:
      expires = int(decoded['exp'] - time.time())
      print('expires in {} seconds ({} hours)'.format(expires, str(datetime.timedelta(seconds=expires))))

    
    
    


