#!/usr/bin/env python3

from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
import os
import tarfile
from pathlib import Path

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
        if directory == 'project': #additionally pack these
            project_dir = os.path.join('pilot', directory)
            compiler_dirs = os.listdir(project_dir)
            for compiler_dir in compiler_dirs:
                project_templ_path = os.path.join(project_dir, compiler_dir)
                project_templates = os.listdir(project_templ_path)
                for proj_templ in project_templates:
                    ptf = os.path.join(project_templ_path, proj_templ)
                    if Path(ptf).is_dir():
                        tar_file = ptf+'.tar.gz'
                        tar_dir(tar_file, ptf)
                        paths.append(os.path.join('..', tar_file))
                print(project_templates)
            pass
        else:
            for (path, _directories, filenames) in os.walk(os.path.join('pilot', directory)):
                for filename in filenames:
                    if not filename.endswith(".pyc"):
                        paths.append(os.path.join('..', path, filename))
    return paths

def tar_dir(name, directory):
    with tarfile.open(name, "w:gz") as tar:
        for (path, _directories, filenames) in os.walk(directory):
            for filename in filenames:
                full_file = os.path.join('.', path, filename)
                arcname=os.path.relpath(full_file, directory)
                tar.add(full_file, arcname=arcname)
        tar.close()

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
                    'pyYAML==6.0.1',
                    'pybars3==0.9.7',
                    'halo==0.0.31',
                    'requests==2.31.0',
                    'requests_http_signature==0.7.1',
                    'configparser==6.0.0',
                    'argparse==1.4.0',
                    'bugsnag==4.6.0',
                    'uuid==1.30',
                    'colorama==0.4.6',
                    'paramiko==3.3.1',
                    'scp==0.14.5',
                    'pyjwt==2.8.0',
                    'qrcode_terminal==0.8',
                    'gql==3.4.1',
                    'rich==13.6.0',
                    'protobuf==4.24.4',
                    'grpcio==1.59.0',
                    'requests_toolbelt==1.0.0'
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
