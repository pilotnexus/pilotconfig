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

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

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
  pilot_server = 'https://gql-testing.pilotnexus.io/v1/graphql'
  oauth_token_url = "https://amescon.eu.auth0.com/oauth/token"
  oauth_device_code_url = "https://amescon.eu.auth0.com/oauth/device/code"

  pilot_home_dir = os.path.expanduser('~/.pilot')
  authfile = os.path.join(pilot_home_dir, 'auth.json')

  pilot_dir = '/etc/pilot'
  nodeconfname = '/pilotnode.yml'

  client_id = 'hG0Kh6oMY6A2dMUjyjAbTQPTcd8syl58'
  audience = [ "https://api.pilotnexus.io", "https://amescon.eu.auth0.com/userinfo" ]

  keys = None
  tokenset = None
  decoded = None

  terminal = True
  sbc = None

  open_transport = None

  def __init__(self, sbc: Sbc):
    self.sbc = sbc
    if not os.path.exists(self.pilot_home_dir):
      os.makedirs(self.pilot_home_dir)
    
    try:
      with open(self.authfile) as authfile:
        self.tokenset = json.load(authfile)
        self.decode()
    except:
      pass
    
    try:
      keys = requests.get("https://amescon.eu.auth0.com/.well-known/jwks.json").json()['keys']
      self.keys = [ key for key in keys if key['alg'] == 'RS256' ][0]
    except:
      pass

  #def loadnodeconf(self):
  #  nodeconffile = self.pilot_dir + self.nodeconfname
  #  nodeconf = None
  #  try:
  #    nodeconf = yaml.load(self.sbc.getFileContent(nodeconffile), Loader=yaml.FullLoader)
  #  except:
  #    nodeconf = None
  #  return nodeconf

  #def savenodeconf(self, nodeconf):
  #  nodeconffile = self.pilot_dir + self.nodeconfname
  #  nodeconfcontent = yaml.dump(nodeconf, default_flow_style=False)
  #  return self.sbc.setFileContent(nodeconffile, nodeconfcontent)

  def authenticate(self):
    payload = {'client_id': self.client_id, 'scope':'openid email offline_access', 'prompt': 'consent' }
    headers = { 'content-type': "application/x-www-form-urlencoded" }

    try:
      response = requests.post(self.oauth_device_code_url, data=payload, headers=headers).json()
    
      print("\n\n")
      print("Open {}{}{} and enter".format(Style.BRIGHT, response['verification_uri'], Style.NORMAL))
      print("\n\n")
      print("""=======>      {}{}{}       <=======""".format(Style.BRIGHT, response['user_code'], Style.NORMAL))
      print("\n\nor scan this code with your Camera app to skip entering the code")
      qrcode_terminal.draw(response['verification_uri_complete'])
      print("note: this code expires in {} minutes".format(response['expires_in'] / 60))

      payload2 = { 'grant_type': "urn:ietf:params:oauth:grant-type:device_code", 
                   'client_id': self.client_id, 'device_code': response['device_code'] }

      done = None
      interval = int(response['interval'])

      while (not done):
        response2 = requests.post(self.oauth_token_url, data=payload2, headers=headers).json()
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
          self.decode()
          with open(self.authfile, 'w') as authfile:
            json.dump(self.tokenset, authfile)

    except Exception as e: 
      print(Fore.RED + 'Error authenticating the device {}'.format(e))
      print(e)

  def refresh(self):
    try:
      if self.tokenset != None and 'refresh_token' in self.tokenset
        headers = { 'content-type': "application/x-www-form-urlencoded" }
        payload = { 'grant_type': "refresh_token", 
                    'client_id': self.client_id,
                    'refresh_token': self.tokenset['refresh_token']
                  }
        response = requests.post(self.oauth_token_url, data=payload, headers=headers).json()

        console.log(response)
        if 'access_token' in response:
          response['refresh_token'] = self.tokenset['refresh_token']
          self.tokenset = response
          self.decode()
          return True
    except:
      print(Fore.RED + 'Error getting refresh token {}'.format(e))
      print(e)

    return False
  
  def decode(self):
    self.decoded = None
    if self.tokenset != None and self.keys != None:
      try:
        pubkey = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(self.keys))
        self.decode = jwt.decode(self.tokenset['access_token'], pubkey, algorithms='RS256', audience = self.audience) #, audience=self.config.CLIENT_ID) 
      except Exception as e:
        print(Fore.RED + 'error decoding token')
        print(e)
  
  def get_token():
    if self.decoded == None:
      self.authenticate()
    
    if self.decoded == None:
      print(Fore.RED + 'Error, cannot authenticate')
      exit(1)
    
    expires = int(decoded['exp'] - time.time())
    
    #print('expires in {} seconds ({} hours)'.format(expires, str(datetime.timedelta(seconds=expires))))

    if expires < 60: # expires in less than 60 seconds
      if not self.refresh():
        print(Fore.RED + 'Cannot refresh authentication token, please authenticate again')
        self.authenticate()
          if self.decoded == None:
            print(Fore.RED + 'Error, cannot authenticate')
            exit(1)

    # here we should have a valid access token
    return 'Bearer {}'.format(self.tokenset['access_token'])

  def query(self, query, isPublic=False):
    try:
      transport = None
      if isPublic:
        transport = RequestsHTTPTransport( url=self.pilot_server, use_json=True )
      else:
        transport = RequestsHTTPTransport( url=self.pilot_server, use_json=True, headers={ 'Authorization': self.get_token() } )

      client = Client( transport=open_transport, fetch_schema_from_transport=True )
      return True, client.execute(query)
    except:
      print(Fore.RED + 'Could not query server')
    
    return False, {}


  def registernode(self, fwconfig):

    query = gql("""
    {
      pilot_node
      {
        name
      }
    }
    """)
    print(prot_client.execute(query))

