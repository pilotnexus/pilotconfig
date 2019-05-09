def setup_arguments(parser):
  # parser.add_argument('--terminal', '-t', action='store_true', help='forces the terminal version instead of GUI')
  parser.add_argument('--source', '-c', default=None, dest='source',
                      help='Download Sourcecode only')
  parser.add_argument('--node', '-n', default=None, dest='node',
                      help='Configure node only')
  parser.add_argument('--reset', '-r', default=None, action='store_const', const='reset', dest='reset',
                      help='Resets the Pilot Mainboard')
  parser.add_argument('--yes', '-y', default=None, action='store_const', const='noninteractive', dest='noninteractive',
                      help='Confirms default action (non-interactive mode)')
  parser.add_argument('--driveronly', '-x', default=None, action='store_const', const='driveronly', dest='driveronly',
                      help='Installs driver only')

def program_arguments(parser):
  parser.add_argument('--binary', '-b', default=None, dest='bin',
                      help='Write binary image to the Pilot Microcontroller')
  parser.add_argument('--variables', '-v', default=None, dest='vars',
                      help='Set PLC variables')

def compiler_arguments(parser):
  parser.add_argument('--config', dest='configfile',
                      default=None, help='module config file (.pilotfwconfig.json)')
  parser.add_argument('--iec2c', dest='iec2cdir',
                      default=None, help='directory of iec2c compiler')
  parser.add_argument('--source', dest='source',
                      default=None, help='source directory')
  parser.add_argument('--target', dest='target',
                      default=None, help='target directory')
  parser.add_argument('--verbose', action='store_const',
                      const=True, help='verbose output')
  parser.add_argument('files', nargs='*', default=None,
                      help='IEC Structured Text File')

def project_arguments(parser):
  # parser.add_argument('--terminal', '-t', action='store_true', help='forces the terminal version instead of GUI')
  pass