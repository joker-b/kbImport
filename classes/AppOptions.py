#! /usr/bin/python3

import argparse
import sys

class AppOptions(object):
  "bundle of globally goodness"
  def __init__(self, pargs=None):
    self.verbose = False
    self.win32 = sys.platform.startswith('win32')
    self.testing = False
    self.use_dng = False
    self.force_copies = False
    self.force_local = False
    self.force_cloud = False
    self.rename = False
    self.version = "kbImport Default Options"
    if pargs is None:
      self.user_args(self.default_arguments())
    else:
      self.user_args(pargs)

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
    self.rename = bool(pargs.rename)
    self.force_local = bool(pargs.local)
    self.force_cloud = bool(pargs.cloud)
    self.init_prefix = '' if pargs.prefix is None else "{}_".format(pargs.prefix)
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
    args.source = None
    args.archive = None
    args.unify = False
    args.rename = False
    args.local = False
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
