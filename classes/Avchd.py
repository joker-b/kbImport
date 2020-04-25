#! /usr/bin/python3

import os
import re
import Store

class Avchd(object):
  """
  Methods related to AVCHD's convoluted file arrangement
  """
  regexAvchd = re.compile('AVCHD')
  regexAvchdFiles = re.compile(r'\.(MTS|CPI|TDT|TID|MPL|BDM)')
  def __init__(self, Storage):
    self.storage = Storage
    self.AVCHDTargets = {"MTS": os.path.join("AVCHD", "BDMV", "STREAM"),
                         "CPI": os.path.join("AVCHD", "BDMV", "CLIPINF"),
                         "MPL": os.path.join("AVCHD", "BDMV", "PLAYLIST"),
                         "BDM": os.path.join("AVCHD", "BDMV"),
                         "TDT": os.path.join("AVCHD", "ACVHDTN"),
                         "TID": os.path.join("AVCHD", "ACVHDTN")}
    self.AVCHDTargets["JPG"] = os.path.join("AVCHD", "CANONTHM")
    self.type = 'JPG'

  @classmethod
  def valid_source_dir(cls, Filename):
    if cls.regexAvchd.search(Filename):
      return True
    return False

  @classmethod
  def filetype_search(cls, Filename):
    return cls.regexAvchdFiles.search(Filename)

  def dest_dir_name(self, SrcFile, ArchDir):
    """
    AVCHD has a complex format, let's keep it intact so clips can be archived to blu-ray etc.
    We will say that the dated directory is equivalent to the "PRIVATE" directory in the spec.
    We don't handle the DCIM and MISC sub-dirs.
    """
    privateDir = self.storage.dest_dir_name(SrcFile, ArchDir)
    if privateDir is None:
      print("avchd error")
      return privateDir
    adir = self.storage.safe_mkdir(os.path.join(privateDir, "AVCHD"), "AVCHD")
    for s in ["AVCHDTN", "CANONTHM"]:
      self.storage.safe_mkdir(os.path.join(adir, s), "AVCHD"+os.path.sep+s)
    bdmvDir = self.storage.safe_mkdir(os.path.join(adir, "BDMV"), "BDMV")
    for s in ["STREAM", "CLIPINF", "PLAYLIST", "BACKUP"]:
      self.storage.safe_mkdir(os.path.join(bdmvDir, s), "BDMV"+os.path.sep+s)
    return privateDir

  def destination_path(self, fullKidPath, VidArchDir):
    path = self.dest_dir_name(fullKidPath, VidArchDir)
    if path is None:
      return None
    return os.path.join(path, self.AVCHDTargets[self.type])

if __name__ == '__main__':
  print("Avchd testing time")
  s = Store.Store()
  v = Avchd(s)
  print(Avchd.valid_source_dir('AVCHD'))
