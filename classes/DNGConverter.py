#! /bin/python

import os
import re
from AppOptions import AppOptions

class DNGConverter(object):
  """handle optional DNG conversion"""
  regexDNGsrc = re.compile(r'(.*)\.RW2')

  @classmethod
  def filetype_search(cls, Filename):
    return cls.regexDNGsrc.search(Filename)

  def __init__(self, Options=AppOptions()):
    self.opt = Options
    self.active = Options.use_dng and Options.win32
    self.nConversions = 0
    self.seek_converter()

  def convert(self, srcPath, destPath, destName):
    "TODO: check for testing? - based on old dng_convert()"
    # TODO: get command from Volumes instance
    if not self.opt.win32:
      return False
    cmd = "\"{}\" -c -d \"{}\" -o {} \"{}\"".format(
        self.converter, destPath, destName, srcPath)
    # print(cmd)
    if self.opt.test:
      print(cmd)
      return True # pretend
    p = os.popen(r'cmd /k')
    p[0].write('{}\r\n'%cmd)
    p[0].flush()
    p[0].write('exit\r\n')
    p[0].flush()
    print(''.join(p[1].readlines()))
    self.nConversions += 1    # TODO - Volume data
    return True

  def seek_converter(self):
    """find a DNG converter, if one is available"""
    self.converter = None
    if not self.opt.win32:
      self.active = False
      return
    pf = os.environ.get('PROGRAMFILES')
    if pf: # windows
      self.converter = os.path.join(pf, "Adobe", "Adobe DNG Converter.exe")
      if not os.path.exists(self.converter):
        pfx = os.environ.get('PROGRAMFILES(X86)')
        self.converter = os.path.join(pfx, "Adobe", "Adobe DNG Converter.exe")
      if not os.path.exists(self.converter):
        self.converter = None

if __name__ == '__main__':
  print("testing time")
  d = DNGConverter()
  print("convertor is {}".format(d.converter))
  print("active? {}".format(d.active))
