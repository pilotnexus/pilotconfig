#Pilot PLC and custom code scripts
from pybars import Compiler
#import subprocess
import os
import json
import itertools
import string
import re
from collections import defaultdict
import fnmatch

memregions = ['input', 'output', 'memory']
baseAddress        = 0x20000000
baseBitbandAddress = 0x22000000
alignment = 4

varsizes = {
        'BOOL': 1,
        'SINT': 1,
        'INT': 2,
        'DINT': 4,
        'LINT': 8,
        'USINT': 1,
        'UINT': 2,
        'UDINT': 4,
        'ULINT': 8,
        'BYTE': 1,
        'WORD': 2,
        'DWORD': 4,
        'LWORD': 8,
        'REAL': 4,
        'LREAL': 8,
        'TIME': 8, #??
        'DATE': 8, #??
        'DT': 8,   #??
        'TOD': 8,  #??
        'STRING': 126
        }

def iec2c_compile(iec2c_path, iecfile, temp_path):
  # resultfile=os.path.join(os.path.abspath(temp_path), 'result.txt')
  execute='{} -I {} -T {} {}'.format(os.path.join(iec2c_path, 'iec2c'), os.path.join(iec2c_path,'lib'), os.path.abspath(temp_path), iecfile)
  return os.system(execute)
  #with open(resultfile, 'r') as fin:
  #  print fin.read()

def init(config, model):
  configdef = { 'moduledefinitions': [] }
  for root, _dirnames, filenames in os.walk(os.path.dirname(os.path.realpath(__file__))):
    for filename in fnmatch.filter(filenames, 'configdefs.json'):
      with open(os.path.join(root, filename)) as obj:
        configdef['moduledefinitions'].extend( json.load(obj)['moduledefinitions'] )

  memmodules = config["modules"]
  if 'plugins' in config:
    memmodules = memmodules + config['plugins']

  #generate module config
  modulelist = [dict(n[0], **n[1][0]) for n in map(lambda x: (x, list(filter(lambda y: x["fid"] == y["fid"],configdef["moduledefinitions"]))), memmodules) if n[1] != []]

  misalignedmodules = []
  #check if config and firmware align
  for module in model['Modules']:
    for confmod in modulelist:
      if confmod['slot'] == module['Slot'] + 1:
        if (confmod['fid'] != module['Name']):
          misalignedmodules.append(confmod['slot'])

  # generate start addresses if they are not configured
  for memregion in memregions:
    start = 0
    for module in modulelist:
      if (memregion+'address') not in module and (memregion+'size') in module and module[memregion+'size'] > 0:
        module[memregion+'address'] = start
        start = start + module[memregion+'size']

  #generate memory regions
  for memregion in memregions: map(lambda x: x.update({memregion+'bytes': range(x[memregion+'address'],x[memregion+'address']+x[memregion+'size'])}), filter(lambda x: (memregion+'address') in x and (memregion+'size') in x,modulelist))
  
  #calculate memory overlaps and sizes
  overlaps = []
  for memregion in memregions:
    for a, b in itertools.combinations(modulelist, 2): 
        if (memregion+'bytes') in a and (memregion+'bytes') in b:
            overlap = list(set(a[memregion+'bytes']).intersection(b[memregion+'bytes']))
            if overlap != []:
                overlaps.append({'elementa': a, 'elementb': b, 'memory' : memregion, 'address': overlap})

  mem = dict(map(lambda x: [x, {'region': x, 'size': 0, 'start': 0, 'absolute': 0}], memregions))
  for memregion in memregions:
    for module in modulelist:
      if (memregion+'address') in module and (memregion+'size') in module:
        size = module[memregion+'address'] + module[memregion+'size'] 
        mem[memregion]['size'] = size if size > mem[memregion]['size'] else size

  return (modulelist, overlaps, misalignedmodules, mem)

def parseplcvariables(temp_path, mem):
  global baseBitbandAddress
  varcsvfilepath=os.path.join(os.path.abspath(temp_path), 'VARIABLES.csv')
  with open(varcsvfilepath) as varcsvfile:
    content = [line.strip() for line in varcsvfile]

  mode = ''
  variables = []
  programs = []
  for line in content:
    if line.startswith('//'): 
      mode = line[2:].strip().lower()
    else:
      columns = line.split(';')
      if mode == 'variables' and len(columns) >= 5:
        varname = columns[2].split('.')
        if len(varname) > 2 and varname[0].upper() == "CONFIG":
          var = {'number': int(columns[0]), 'location': columns[1], 'resource': varname[1], 'type': columns[4]}
          if len(varname) == 3:
            var['instance'] = None
            var['name'] = varname[2]
          elif len(varname) >= 4:
            var['instance'] = varname[2]
            var['name'] = '.'.join(varname[3:])

          #add extra variable info
          var['isGlobal'] = True if var['instance'] == None else False
          var['extern'] = '{}__{}'.format(var['resource'], var['name'])
          var['isExternal'] = True if var['location'] == 'EXT' else False
          var['isString'] = True if var['type'] == 'STRING' else False
          var['plcVarName'] = '{}__{}'.format(var['resource'], var['name']) if var['isGlobal'] else '{}.{}'.format(var['instance'], var['name'])
          var['externdeclaration'] = 'extern __IEC_{}_p {};'.format(var['type'], var['extern']) if var['isGlobal'] else ''

          if var['isGlobal']:
            var['get'] = '{}.value'.format(var['plcVarName'])
          elif var['isExternal']:
            var['get'] = '(__GET_EXTERNAL_BY_REF({}))'.format(var['plcVarName'])
          else:
            var['get'] = '&(__GET_VAR({}))'.format(var['plcVarName'])

          if var['location'] == 'FB':
            if  var['isGlobal'] == True:
              programs.append(var)
          else:
            variables.append(var)

  #parse located variables
  regex = re.compile(r'__LOCATED_VAR\((?P<type>\w+),(?P<var>[^,]*),(?P<mem>\w),(?P<size>\w),(?P<byte>\d+)(,(?P<bit>\w))?\)')
  locatedvarfilepath=os.path.join(os.path.abspath(temp_path), 'LOCATED_VARIABLES.h')
  with open(locatedvarfilepath) as locatedvarfile:
    locatedvariables = [regex.match(line).groupdict() for line in locatedvarfile]

  for locvar in locatedvariables:
    locvar['externlocated'] = 'extern {0} * {1}_; extern IEC_BYTE * {2}_flags; extern {0} * {2}_changed;'.format(locvar['type'], locvar['var'].lower(), locvar['var'])
    #locvar['memoryaddress'] = 
    if locvar['mem'] == 'I':
      locvar['location'] = 'input' #from memregions var
    elif locvar['mem'] == 'Q':
      locvar['location'] = 'output' #from memregions var
    else:
      locvar['location'] = 'memory' #from memregions var

    #located memory
    memmax = int(locvar['byte']) + varsizes[locvar['type']]
    if memmax > mem[locvar['location']]['size']:
      mem[locvar['location']]['size'] = memmax

  #calc absolute memory position
  pos = 0
  for _key, value in mem.items():
    value['start'] = pos
    value['absolute'] = '0x{:X}'.format(pos + baseAddress)
    pos += value['size']

  #set variable memory positions
  for locvar in locatedvariables:
    reladdress = mem[locvar['location']]['start'] + int(locvar['byte'])
    absaddress = reladdress + baseAddress
    # print('location: {}, rel.addr. {:X}, abs.addr: {:X}'.format(locvar['var'], reladdress, absaddress))

    if locvar['bit'] != None:
      locvar['locatedaddressdeclaration'] = '{0} * {1}_ = ({0} *) 0x{2:X}; //bitband region\r#define {3} {1}_\r{0} * {3}_changed;\rIEC_BYTE * {3}_flags;\r'.format(locvar['type'], locvar['var'].lower(), baseBitbandAddress + (reladdress*32) + (int(locvar['bit'])*4), locvar['var'])
    else:
      locvar['locatedaddressdeclaration'] = '{0} * {1}_ = ({0} *) 0x{2:X};\r#define {3} {1}_\r{0} * {3}_changed;\rIEC_BYTE * {3}_flags;\r'.format(locvar['type'], locvar['var'].lower(), absaddress, locvar['var']) #TODO replace 0 with memorylocation


  locations = list(set(map(lambda x: x['location'], locatedvariables)))

  return programs, variables, locatedvariables, locations

def checkIfReplacementExists(key, module):
  if key in module:
    #TODO check if module is an array
    regex = re.compile(r"\{\{(.*?)+\}\}")
    m = regex.match(module[key])
    print(m)
    # TODO check that all replacements can be made, otherwise it cannot compile
    # that happens with wrong config file e.g.

def io16_init_gen(nibble, direction, module):
  return 'rpc_io16_{}_set_direction({}, {}); '.format(
    module['index'],
    module['codegen']['nibbles'][nibble]['selector'],
    module['codegen']['direction'][direction])

def io16_read_gen(calls, module):
  if module['fid'] == 'io16' and module['config']:
    gen = defaultdict(lambda : {})
    for k,v in module['config']['direction'].items():
      if not module['codegen']['nibbles'][k][v]['offset'] in gen[v]:
        gen[v][module['codegen']['nibbles'][k][v]['offset']] = []
      gen[v][module['codegen']['nibbles'][k][v]['offset']].append({ 'selector': module['codegen']['nibbles'][k]['selector'],  
        'data': module['codegen']['nibbles'][k][v] })

    #generate inputs
    if 'in' in gen:
      for offset in gen['in']:
        nibbleCalls = []
        for nibble in gen['in'][offset]:
          nibbleCalls.append("(rpc_io16_{}_get_byte({}) >> {})".format(
          module['index'],
          nibble['data']['register'],
          nibble['data']['shift']))
        calls['read'].append("*((unsigned char *)({} + {})) = {}; ".format(
                              module['input'+'absoluteaddress'], offset,
                              ' | '.join(nibbleCalls)))

    #generate outputs
    if 'out' in gen:
      for offset in gen['out']:
        nibbleCalls = []
        registerlist = []
        for nibble in gen['out'][offset]:
          if nibble['data']['register'] not in registerlist:
            calls['write'].append("rpc_io16_{}_set_byte({}, (*((unsigned char *)({} + {}))) >> {}); ".format(
                  module['index'],
                  nibble['data']['register'],
                  module['output'+'absoluteaddress'], offset, nibble['data']['shift']))
            registerlist.append(nibble['data']['register'])
                              
  return calls

def helper_markdown(this, options):
  md = options['fn'](this)
  # md - is a raw markdown string. You could handle it with MD-compiler
  # or just forward it to the result "as is"
  return md

def parsemodules(mem, modules):
  global baseAddress

  for module in modules:
    module['index'] = module['slot']-1

  calls = {'read': [], 'write': [], 'init': [], 'include': []}
  compiler = Compiler()

  for key, value in mem.items():
    for module in modules:
        if (key+'address') in module:
          module[key+'absoluteaddress'] = '0x{:X}'.format(module[key+'address'] + value['start'] + baseAddress)

  for key, value in calls.items():
    for module in modules:
      if key in module and module[key] != '':
        checkIfReplacementExists(key, module)
        template = compiler.compile(module[key])
        calls[key].append(template(module))


  # module config specific calls
  for module in modules:
    if module['fid'] == 'io16' and module['config']['direction']:
      directions = module['config']['direction']
      calls['init'].extend(list(map((lambda x: io16_init_gen(x, directions[x], module)), directions.keys())))
    calls = io16_read_gen(calls, module)

  return calls

def parsesubscriptions(subscriptions):
  subs = []
  for sub in subscriptions:
    subs.append(sub.replace('.', '__').upper() + '.flags = __IEC_SUBSCRIBE_FLAG; ')
  return subs

def parsetemplate(out_path, templatedata):
  #printable = set(string.printable)
  #filecontent = filter(lambda x: x in printable, templatefile.read())
  template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'template')

  for _root, _dirs, files in os.walk(template_path):
    templfiles = map(lambda x: os.path.join(template_path, x) ,filter(lambda x: x.endswith('.templ'), files))

    for templfile in templfiles:
      with open(templfile) as f:
        compiler = Compiler()
        template = compiler.compile(f.read())

        output = template(templatedata)

        with open(os.path.join(out_path, os.path.splitext(os.path.basename(templfile))[0]), 'w') as f:
          f.write(output)          
