import os
from colorama import Fore
from requests_http_signature import HTTPSignatureAuth
from base64 import b64decode
from configparser import ConfigParser
import requests

class Remoteit():
  config_section = 'default'
  config_file = '~/.remoteit/credentials'
  config = None
  public_ip = None
  connection = None
  service_id = None
  
  def update_public_ip(self):
    res = requests.get('https://ident.me')
    if res.status_code == 200:
      self.public_ip = res.text
    else:
      return None

  def get_devices(self):
    body = {"query":"""query{ login { devices (size: 1000, from: 0) { items { id name state services { id name
	        protocol
	        port
	        } } } } }"""}
    res = self.exec(body)
    if res and res.status_code == 200:
      return res.json()["data"]["login"]["devices"]["items"]
    return None

  def list_devices(self):
    device_list = []
    devices = self.get_devices()
    if devices:
        for device in devices:
            for service in device["services"]:
              if service["protocol"] == "TCP" and service["port"] == 22:
                device_list.append((device["name"], device["state"]))
    if len(device_list) > 0:
        from rich.console import Console
        from rich.table import Table

        table = Table.grid()

        table.add_column("Device Name", justify="left")
        table.add_column("Online?", justify="left")

        for (name, state) in device_list:
            if state == 'active':
              table.add_row("[green]{}  ".format(name), "[green]online")
            else:
              table.add_row("{}  ".format(name), "offline")
        
        console = Console()
        console.print(table)


  def resolve_service_name(self, device_name: str):
    device_name = device_name.strip().lower()
    print('Looking up service...', end='')
    devices = self.get_devices()
    if devices:
      for device in devices:
        if device_name == device["name"].strip().lower():
          for service in device['services']:
            if service["protocol"] == "TCP" and service["port"] == 22:
              print(Fore.GREEN + 'done')
              return service["id"]

    print(Fore.RED + 'failed')
    exit(1)

  def connect(self, service_id):
    print("Getting your external IP to limit proxy access...", end='')
    if self.public_ip == None:
        self.update_public_ip()

    if self.public_ip != None:
      print(Fore.GREEN + "done")
      print("access limited to {} (your external IP)".format(self.public_ip))
      allowed_ip = self.public_ip
    else:
      print(Fore.YELLOW + "failed, no IP filter applied")
      allowed_ip = "255.255.255.255"

    print('Creating proxy...', end='')

    body = {"query": """mutation query($serviceId: String!, $hostIP: String!) {
              connect(serviceId: $serviceId, hostIP: $hostIP) {
            	id
            	created
            	host
            	port
            	reverseProxy
            	timeout
            	}
            }""",
            "variables": {
            "serviceId": service_id,
	        "hostIP": allowed_ip
            } 
            }
    res = self.exec(body)
    if res and res.status_code == 200:
      self.connection = res.json()["data"]["connect"]
      self.service_id = service_id
      print(Fore.GREEN + 'done')
      return (self.connection["host"], self.connection["port"])
    else:
      print(Fore.RED + 'failed')
      exit(1)

  def disconnect(self):
    if self.connection == None or self.service_id == None:
        return

    print('Closing proxy...', end='')

    body = {"query": """mutation query($serviceId: String!, $connectionId: String!){
                        disconnect(serviceId: $serviceId, connectionId: $connectionId)
            }""",
            "variables": {
            "serviceId": self.service_id,
	        "connectionId": self.connection["id"] 
            } 
            }
    res = self.exec(body)
    if res and res.status_code == 200:
      if res.json()["data"]["disconnect"] == True:
        self.connection = None
        print(Fore.GREEN + 'done')
        return

    print(Fore.RED + 'failed')

  def read_keys(self):
    if self.config == None:
      try:
        self.config= ConfigParser()
        self.config.read(os.path.expanduser(self.config_file))
      except:
        print(Fore.RED + "Cannot read '{}'".format(self.config_file))
        print("Look at the section 'Key Management' here: https://docs.remote.it/developer-tools/authentication")
        print("to learn how to setup your access keys")
        exit(1)
    try:
      key_id = self.config.get(self.config_section, 'R3_ACCESS_KEY_ID')
      key_secret_id = self.config.get(self.config_section, 'R3_SECRET_ACCESS_KEY')
      return (key_id, key_secret_id)
    except:
      print("Your configuration file '{}' seems to be incorrect. Cannot find required keys".format(self.config_file))
      exit(1)

  def exec(self, body):
    (key_id, key_secret_id) = self.read_keys()

    host = 'api.remote.it'
    url_path = '/graphql/v1'
    content_type_header = 'application/json'
    content_length_header = str(len(body))
    
    headers = {
        'host': host,
        'path': url_path,
        'content-type': content_type_header,
        'content-length': content_length_header,
    }
    
    try:
      return requests.post('https://' + host + url_path,
                               json=body,
                               auth=HTTPSignatureAuth(algorithm="hmac-sha256",
                                                      key=b64decode(key_secret_id),
                                                      key_id=key_id,
                                                      headers=[
                                                      '(request-target)', 'host',
                                                      'date', 'content-type',
                                                      'content-length'
                                                  ]),
                               headers=headers)
    except:
      return None