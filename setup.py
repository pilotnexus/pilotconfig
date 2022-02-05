#!/usr/bin/env python3

from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))

# Get the version
with open(os.path.join(here, 'pilot', 'VERSION'), encoding='utf-8') as f:
  version = f.read().strip()

# Get the long description from the README file
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
  long_description = f.read()

# extra files
def package_files(directoryarr):
    paths = []
    for directory in directoryarr:
      for (path, _directories, filenames) in os.walk(os.path.join('pilot', directory)):
          for filename in filenames:
              paths.append(os.path.join('..', path, filename))
    return paths


extra_files = package_files(['bin', 'compiler', 'plugins', 'devices', 'project'])
extra_files.append('VERSION')
extra_files.append('configdefs.json')
extra_files.append('targethardware.json')

setup(
  name='pilot-config',
  version=version,
  description='Pilot Automation Command Line Utility',
  long_description=long_description,
  author='Daniel Amesberger',
  author_email='daniel.amesberger@amescon.com',
  url='https://www.amescon.com',
  classifiers=[
      # How mature is this project? Common values are
      #   3 - Alpha
      #   4 - Beta
      #   5 - Production/Stable
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Topic :: Software Development :: Build Tools',
      'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      'Programming Language :: Python :: 3',
  ],
  keywords='pilot development automation plc',
  packages=find_packages(exclude=[]),
  package_data={'': extra_files},
  install_requires=['lazy_import',
                    'pyYAML',
                    'pybars3',
                    'halo',
                    'requests',
                    'argparse',
                    'bugsnag',
                    'uuid',
                    'bugsnag',
                    'colorama',
                    'paramiko',
                    'scp',
                    'pyjwt',
                    'qrcode_terminal',
                    'gql',
                    'graphql-core<3.0.0',
                    'tabulate',
                    'protobuf',
                    'grpcio'
                    ],
  python_requires='>=3',
  entry_points={  # Optional
      'console_scripts': [
          'pilot=pilot.pilot:main',
      ],
  },
  project_urls={  # Optional
    'Bug Reports': 'https://github.com/pypa/sampleproject/issues',
    'Funding': 'https://donate.pypi.org',
    'Say Thanks!': 'http://saythanks.io/to/example',
    'Source': 'https://github.com/pypa/sampleproject/',
  },
)