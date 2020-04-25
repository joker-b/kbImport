#! /bin/python

import os
import sys
import time

from AppOptions import AppOptions
from ImgInfo import ImgInfo

#####################################################
## Find or Create Archive Destination Directories ###
#####################################################

class Store(object):
  """Storeage Operationns"""

  def __init__(self, Options=AppOptions()):
    self.opt = Options
    self.createdDirs = []
    self.encountered = {}
    self.testLog = {}
    self.unifiedDir = None

  def print_report(self, TopDir='.'):
    print("Out of {} directory requests:".format(len(self.encountered)))
    allDirs = self.createdDirs + ImgInfo.createdDirs
    if len(allDirs) > 0:
      print("Created directories within {}:".format(TopDir))
      print(' ' + '\n '.join(allDirs))
    else:
      print("No new directories were created")

  def safe_mkdir(self, Dir, PrettierName=None, Prefix=''):
    """
    check for existence, create _recursively_ as needed.
    'PrettierName' is a print-pretty version.
    Returns Dir or None
    When testing is True, still return name of the (non-existent) directory!
    """
    report = PrettierName or Dir
    if self.encountered.get(Dir): # no need to call stat()
      return Dir
    if os.path.exists(Dir):
      if not os.path.isdir(Dir):
        print("Path error: '{}' exists but not a directory!".format(Dir))
        return None
      self.encountered[Dir] = 1
      return Dir
    if self.opt.testing:
      gr = self.testLog.get(report)
      if not gr:
        print("safe_mkdir('{}') needed **".format(report))
        self.testLog[report] = 1
    else:
      parent = os.path.split(Dir)[0]
      if not os.path.exists(parent):
        p = self.safe_mkdir(parent)
        if p is None:
          return None
      try:
        os.mkdir(Dir)
      except:
        print('mkdir "{}" failed'.format(Dir))
        return None
      if not os.path.exists(Dir):
        print('mkdir result "{}" failed to appear'.format(Dir))
        return None
      self.createdDirs.append(Prefix+os.path.split(Dir)[1])
      print("** Created dir {} **".format(report))
    self.encountered[Dir] = 1
    return Dir

  ######

  def year_subdir(self, SrcFileStat, ArchDir, ReportName=""):
    "Based on the source file's timestamp, seek (or create) an archive directory"
    # subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_ctime))
    subdir = time.strftime("%Y", time.localtime(SrcFileStat.st_mtime))
    result = os.path.join(ArchDir, subdir)
    report = ReportName + os.path.sep + subdir
    self.safe_mkdir(result, report)
    return result

  #########

  def month_subdir(self, SrcFileStat, ArchDir, ReportName=""):
    "Based on the source file's timestamp, seek (or create) an archive directory"
    # subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_ctime))
    subdir = time.strftime("%Y-%m-%b", time.localtime(SrcFileStat.st_mtime))
    result = os.path.join(ArchDir, subdir)
    report = ReportName + os.path.sep + subdir
    self.safe_mkdir(result, report, Prefix='  ')
    return result

  #########

  def unified_dir_name(self, ArchDir, ReportName=""):
    '''
    When the unify option is active, we just make one directory
    '''
    if self.unifiedDir is not None:
      return self.unifiedDir # already have it
    now = time.localtime()
    yearStr = time.strftime("%Y", now)
    yearPath = os.path.join(ArchDir, yearStr)
    archivePath = ReportName+os.path.sep+yearStr
    self.safe_mkdir(yearPath, archivePath)
    monthStr = time.strftime("%Y-%m-%b", now)
    monthPath = os.path.join(yearPath, monthStr)
    archivePath = archivePath+os.path.sep+monthStr
    self.safe_mkdir(monthPath, archivePath, Prefix='  ')
    dateStr = time.strftime("%Y_%m_%d", now)
    if self.opt.jobname is not None:
      dateStr = "{}_{}".format(dateStr, self.opt.jobname)
    unifiedName = os.path.join(monthPath, dateStr)
    archivePath = archivePath+os.path.sep+dateStr
    self.safe_mkdir(unifiedName, archivePath, Prefix='    ')
    if not (os.path.isdir(unifiedName) or self.opt.testing):
      print("path error: {} is not a directory!".format(unifiedName))
      return None
    self.unifiedDir = unifiedName
    return self.unifiedDir

  def dest_dir_name(self, SrcFile, ArchDir, ReportName=""):
    """
    Seek or create an archive directory based on the src file's origination date,
    unless 'unify' is active, in which case base it on today's date.
    """
    if self.opt.unify:
      return self.unified_dir_name(ArchDir, ReportName)
    try:
      s = os.stat(SrcFile)
    except FileNotFoundError:
      print('dest_dir_name("{}") not found'.format(SrcFile))
      return None
    except:
      print('Stat failure: "{}"'.format(sys.exc_info()[0]))
      return None
    yearDir = self.year_subdir(s, ArchDir)
    monthDir = self.month_subdir(s, yearDir)
    timeFormat = "%Y_%m_%d"
    dateDir = time.strftime(timeFormat, time.localtime(s.st_mtime))
    if self.opt.jobname is not None:
      dateDir = "{}_{}".format(dateDir, self.opt.jobname)
    destDir = os.path.join(monthDir, dateDir)
    # reportStr = ReportName + os.path.sep + dateDir
    return destDir

if __name__ == '__main__':
  print("testing time")
  opt = AppOptions()
  opt.testing = True
  #opt.unify = True
  opt.set_jobname('StorageTest')
  s = Store(opt)
  s.safe_mkdir('here/would_be_a/testing_dir')
  s.safe_mkdir('/home/kevinbjorke/pix/kbImport/Pix')
  d = (s.dest_dir_name('../kbImport3.py', '/home/kevinbjorke/pix/kbImport/Pix'))
  print("for '{}':".format(d))
  s.safe_mkdir(d)
  s.print_report()
