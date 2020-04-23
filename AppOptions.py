#! /usr/bin/python3

import argparse

class AppOptions(object):
  "bundle of globally goodness"
  def __init__(self, pargs=None):
    self.verbose = False
    self.win32 = False
    self.testing = False
    self.use_dng = False
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
    self.jobname = pargs.jobname
    self.verbose = self.verbose or bool(pargs.verbose)
    self.testing = self.testing or bool(pargs.test)
    self.numerate = bool(pargs.numerate)
    self.source = pargs.source
    self.archive = pargs.archive
    if pargs.prefix is not None:
      self.prefix = "{}_".format(pargs.prefix)
    if pargs.jobpref is not None:
      if self.prefix is None:
        self.prefix = "{}_".format(self.jobname)
      else:
        self.prefix = "{}{}_".format(self.prefix, self.jobname)
    # unique to storage
    self.unify = bool(pargs.unify)

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
