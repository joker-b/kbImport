#! /usr/bin/python3

import argparse

class AppOptions(object):
  "bundle of globally goodness"
  def __init__(self, pargs=None):
    self.verbose = False
    self.win32 = False
    self.testing = False
    self.use_dng = False
    self.force_copies = False
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

  def default_arguments(self):
    args = argparse.Namespace()
    args.jobname = 'test'
    args.prefix = None
    args.jobpref = None
    args.source = None
    args.archive = None
    args.unify = False
    args.test = True
    args.verbose = False
    args.numerate = False
    return args

if __name__ == '__main__':
  print("testing time")
  a = AppOptions()
  print(a)
  print(a.prefix)
