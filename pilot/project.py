from .Sbc import Sbc

def arguments(parser):
  # parser.add_argument('--terminal', '-t', action='store_true', help='forces the terminal version instead of GUI')
  pass


def main(args):
  print('This will create a new firmware project for a Node.')
  project_name = input('Project Name: ')
  print('Next we need a hostname or IP and username/password (ssh) of the Node you want to configure.')
  node_host = input('IP of Node to get FW Config: ')
  node_user = input('Username (pi): ')
  node_password = input('Password (raspberry): ')
  get_node_info(node_host, node)
  print("Project generated:")
  print( """{}
            ├─ src/
            │  ├─ program.st /* IEC 61131-3 code */
            │  └─ *.c, *.h   /* custom C code compiled into firmware image */
            ├─ config.json   /* firmware configuration (memory mapping, module configuration, etc.) */
            └─ basefw/       /* firmware base code folder, generated by 'make basefw' */""".format(project_name))

