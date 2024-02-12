#! /usr/bin/python3

"""
Could have been caleld "config.py" but it's not
"""

import argparse
import sys
import os
import platform
import re
import time
from enum import Enum

class Platform(Enum):
  MAC = 1
  WINDOWS = 2
  LINUX = 3
  CROSTINI = 4 # variants of linux, ya ya
  WSL = 5
  UBUNTU = 6

def identify_platform():
  if os.name == 'posix': # mac?
    if platform.uname()[0] == 'Linux':
      if os.path.exists('/mnt/chromeos'):
        return Platform.CROSTINI
      if os.path.exists(os.path.join('/media/', os.environ['USER'])):
        return Platform.UBUNTU
      if os.path.exists('/mnt/c'): # TODO: is there a better test than this?
        return Platform.WSL
      return Platform.LINUX
  elif os.name == "nt" or self.opt.win32:
    return Platform.WINDOWS
  return Platform.MAC # TODO: catch unknowns?

class AppOptions(object):
  "bundle of globally goodness"
  def __init__(self, pargs=None):
    self.verbose = False
    self.win32 = sys.platform.startswith('win32')
    self.testing = False
    self.use_dng = False
    self.pix_only = False
    self.force_copies = False
    self.force_local = False
    self.force_synology = False
    self.force_cloud = False
    self.rename = False
    self.version = "kbImport Default Options"
    self.now = time.time()
    if pargs is None:
      self.user_args(self.default_arguments())
    else:
      self.user_args(pargs)
    self.platform = identify_platform()

  def __str__(self):
    if self.verbose:
      return dir(self).__str__()
    return self.version

  def user_args(self, pargs):
    "set state according to object 'pargs' created by argparse"
    self.verbose = self.verbose or bool(pargs.verbose)
    self.testing = self.testing or bool(pargs.test)
    self.numerate = bool(pargs.numerate)
    self.source = pargs.source
    self.archive = pargs.archive
    self.project = pargs.project
    if pargs.filter is not None:
      self.filter = re.compile(pargs.filter)
    else:
      self.filter = None
    self.age = max(0, int(pargs.age))
    if self.age > 0:
      if self.verbose:
        print("Max Age is {} days ago".format(self.age+0.5))
      self.age = self.now - (self.age + 0.5) * (24 * 60 * 60)
    self.rename = bool(pargs.rename)
    self.pix_only = bool(pargs.pix_only)
    self.force_local = bool(pargs.local)
    self.force_synology = bool(pargs.syn)
    if self.force_synology:
      if self.archive is not None:
        print(f"WARNING: --archive '{self.archive}' overrides --syn")
      else:
        self.archive = os.path.join(os.environ['HOME'],'SynologyDrive', 'kbImport')
    self.force_cloud = False if self.force_synology else bool(pargs.cloud)
    self.init_prefix = '' if pargs.prefix is None or pargs.prefix == 'None' or pargs.prefix == 'none' \
                                else "{}_".format(pargs.prefix)
    self.use_job_prefix = bool(pargs.jobpref)
    self.unify = bool(pargs.unify)
    self.set_jobname(pargs.jobname)
    # unique to storage

  def set_jobname(self, Job=None):
    self.jobname = '' if Job is None else Job
    if self.use_job_prefix:
      if self.init_prefix is None:
        self.prefix = "{}_".format(self.jobname)
      else:
        self.prefix = "{}{}_".format(self.init_prefix, self.jobname)
    else:
      self.prefix = ''

  def add_prefix(self, OrigName):
    "add appropriate prefix(es) to a name"
    if self.numerate:
      # TODO extract file extension, format number output, store a number, make sure we are *sorted*
      return "{}{}".format(self.prefix, OrigName)
    return "{}{}".format(self.prefix, OrigName)

  def default_arguments(self):
    args = argparse.Namespace()
    args.jobname = 'test'
    args.prefix = None
    args.jobpref = None
    args.project = False
    args.source = None
    args.archive = None
    args.unify = False
    args.filter = None
    args.age = True
    args.rename = False
    args.pix_only = False
    args.local = False
    args.syn = False
    args.cloud = False
    args.test = True
    args.verbose = False
    args.numerate = False
    return args

if __name__ == '__main__':
  print("testing time")
  a = AppOptions()
  a.use_job_prefix = True
  a.set_jobname('tester')
  print(a)
  print(a.prefix)
  print(a.add_prefix('DSCF7544.JPG'))
