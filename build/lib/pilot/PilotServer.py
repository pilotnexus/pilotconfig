import lazy_import

sys = lazy_import.lazy_module("sys")
time = lazy_import.lazy_module("time")
requests = lazy_import.lazy_module("requests")
bugsnag = lazy_import.lazy_module("bugsnag")
os = lazy_import.lazy_module("os")
yaml = lazy_import.lazy_module("yaml")
getpass = lazy_import.lazy_module("getpass")
json = lazy_import.lazy_module("json")

get_mac = lazy_import.lazy_callable("uuid.getnode")
#from uuid import getnode as get_mac
Enum = lazy_import.lazy_callable("enum.Enum")
#from enum import Enum

from colorama import Fore
from colorama import Style
from colorama import init

from .Sbc import Sbc

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
  pilotrc = '~/.pilotrc'
  pilotcfg = {'username': '', 'token': ''}
  pilot_dir = '/etc/pilot'
  nodeconfname = '/pilotnode.yml'
  terminal = True

  sbc = None

  def __init__(self, sbc: Sbc):
    self.sbc = sbc

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
      nodeconf = yaml.load(self.sbc.getFileContent(nodeconffile))
    except:
      nodeconf = None
    return nodeconf

  def savenodeconf(self, nodeconf):
    nodeconffile = self.pilot_dir + self.nodeconfname
    nodeconfcontent = yaml.dump(nodeconf, default_flow_style=False)
    return self.sbc.setFileContent(nodeconffile, nodeconfcontent)

  def registernode(self, fwconfig):
    nodeconf = self.loadnodeconf()
    nodeid = None
    apikey = None

    address = get_mac()
    h = iter(hex(address)[2:].zfill(12))
    mac = "".join(i + next(h) for i in h)

    if nodeconf != None and 'nodeid' in nodeconf and 'apikey' in nodeconf:
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
      ret, obj = self.query_graphql(query, apikey)
      if ret == 200 and obj['data'] and obj['data']['nodebyid']:
        print('Node Name: \'{}\''.format(
            obj['data']['nodebyid']['name']))
      elif ret == 200 and not obj['data']['nodebyid']:
        apikey = None

    if apikey == None:
      ch = input(
          'Do you want to register the Node? (required for remote access) (y/n) ').strip().lower()
      # ch = read_single_keypress()
      if ch == 'y' or ch == 'yes':
        #Register unassigned Node
        nodename = input('Enter a name for this Node (Unassigned Node): ')
        if nodename == '':
          nodename = 'Unassigned Node'
        query = u"""
        mutation {{
          getNodeCode(node: {{name: "{}", mac: "{}"}}) {{
            code
            requestid
            registerNodeStatus
          }}
        }}
        """.format(nodename, mac)
        ret, obj = self.query_graphql(query)
        if ret == 200 and obj['data'] and obj['data']['getNodeCode']:
          code = obj['data']['getNodeCode']['code']
          requestid = obj['data']['getNodeCode']['requestid']
          retcode = RegisterNodeStatus(obj['data']['getNodeCode']['registerNodeStatus'])

          if retcode == RegisterNodeStatus.OK:
            print('To register, please go to https://pilotcockpit.io/#/registernode and enter the following code:')
            print(Fore.GREEN + code)

            # We have a node code, lets poll the status
            node = None
            while not node:
              time.sleep(2)
              query = u"""
              {{
                noderequeststatus(requestid: "{}") {{
                  id
                  apikey
                  instanceid
                }}
              }}
              """.format(requestid)
              ret, obj = self.query_graphql(query)

              if ret == 200 and obj['data'] and obj['data']['noderequeststatus']:
                print(Fore.GREEN + 'Node added successfully!')
                nodeid = obj['data']['noderequeststatus']['id']
                apikey = obj['data']['noderequeststatus']['apikey']
                break

          elif retcode == RegisterNodeStatus.MAC_ALREADY_USED:
            print(Fore.RED + 'A node with this MAC address is already registered, cannot register another one')
          else:
            print(Fore.RED + 'Could not register node')

    if nodeid != None and apikey != None:
      if nodeconf == None:
        nodeconf = {}
      nodeconf['nodeid'] = nodeid
      nodeconf['apikey'] = apikey

      #generate default connector entry if no connectors are defined
      #needs a change in the future probably for instance based deepstream servers
      #connectors:
      #  server:
      #    type: deepstream
      #    server: wss://rt.pilotnexus.io
      if not 'connectors' in nodeconf:
        nodeconf['connectors'] = { 'server': { 'type': 'deepstream', 'server': 'wss://rt.pilotnexus.io' } }

      self.savenodeconf(nodeconf)

      if fwconfig and nodeconf and nodeconf['apikey']:
        try:
          print('Saving Node configuration...', end='')
          query = u"""
          mutation {{
            setNodeConfig (nodeId: "{}", fwconfig: "{}")
          }}
          """.format(nodeid, json.dumps(fwconfig).replace('"', '\\"'))
          ret, obj = self.query_graphql(query, nodeconf['apikey'])
          if ret == 200 and obj['data'] and obj['data']['setNodeConfig']:
            if obj['data']['setNodeConfig'] == 1:
              print(Fore.GREEN + 'done')
            else:
              print(Fore.RED + 'failed on server')
          else:
            print(Fore.RED + 'failed')
        except:
          print(Fore.RED + 'failed')
