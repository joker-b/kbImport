#! /bin/python

import os
import time

from AppOptions import AppOptions
from ImgInfo import ImgInfo

#####################################################
## Find or Create Archive Destination Directories ###
#####################################################

class StorageHierarchy(object):
  """Destination Directory Hierarchy"""

  def __init__(self, Options=AppOptions()):
    self.opt = Options
    self.createdDirs = []
    self.testLog = {}

  def print_report(self, TopDir='.'):
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
    Return directory name.
    When testing is True, still return name of the (non-existent) directory!
    """
    report = PrettierName or Dir
    if not os.path.exists(Dir):
      if self.opt.testing:
        gr = self.testLog.get(report)
        if not gr:
          print("Need to create dir '{}' **".format(report))
          self.testLog[report] = 1
      else:
        print("** Creating dir {} **".format(report))
        parent = os.path.split(Dir)[0]
        if not os.path.exists(parent):
          print("  inside of {}".format(parent))
          self.safe_mkdir(parent)
        try:
          os.mkdir(Dir)
        except:
          print('mkdir "{}" failed'.format(Dir))
          return None
        if not os.path.exists(Dir):
          print('mkdir "{}" failed to appear'.format(Dir))
          return None
        self.createdDirs.append(Prefix+os.path.split(Dir)[1])
        return Dir
    elif not os.path.isdir(Dir):
      print("Path error: '{}' is not a directory!".format(Dir))
      return None
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

  def unified_dir_name(self, ArchDir, ReportName=""):
    'TODO: redundant calls to safe_mkdir?'
    if self.opt.unify is not None:
      return self.opt.unify
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
    unifiedDir = os.path.join(monthPath, dateStr)
    archivePath = archivePath+os.path.sep+dateStr
    self.safe_mkdir(unifiedDir, archivePath, Prefix='    ')
    if not (os.path.isdir(unifiedDir) or self.opt.testing):
      print("path error: {} is not a directory!".format(unifiedDir))
      return None
    return unifiedDir

  def dest_dir_name(self, SrcFile, ArchDir, ReportName=""):
    """
    Seek or create an archive directory based on the src file's origination date,
    unless 'unify' is active, in which case base it on today's date.
    """
    if self.opt.unify:
      return self.unified_dir_name(ArchDir, ReportName)
    try:
      s = os.stat(SrcFile)
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
  opt.set_jobname('StorageTest')
  s = StorageHierarchy(opt)
  s.safe_mkdir('here/would_be_a/testing_dir')
  print(s.dest_dir_name('../kbImport3.py', '/home/kevinbjorke'))
  s.print_report()
