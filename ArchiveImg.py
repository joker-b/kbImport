#! /bin/python

import re
from DNGConverter import *

class ArchiveImg(object):
  """A Single Image"""
  srcName = ''
  srcPath = '' # full path
  destName = ''
  destPath = ''
  doppelFiles = {}
  doppelPaths = {}
  createdDirs = []
  testLog = {}
  regexDotAvchd = re.compile('(.*).AVCHD')
  regexPic = re.compile(r'([A-Z_][A-Z_][A-Z_][A-Z_]\d\d\d\d)\.(JPG|RAF|RW2|RAW|DNG)')

  def __init__(self, Name, Path):
    self.srcName = Name
    self.srcPath = Path
    self.nBytes = long(0)
    self.dng = DNGConverter(False)

  def doppelganger(self):
    "figure out if there is a copy of this file in a neighboring archive"
    name = ArchiveImg.doppelFiles.get(self.srcName)
    if name:
      return True
    (monthPath, dayFolder) = os.path.split(self.destPath)
    dayStr = dayFolder[:10]
    if VERBOSE:
      print("doppelhunting in {}".format(monthPath))
    for d in os.listdir(monthPath):
      name = ArchiveImg.doppelPaths.get(d)
      if name:
        # already checked
        continue
      if d[:10] != dayStr:
        # only review days we care about
        continue
      ArchiveImg.doppelPaths[d] = 1
      for f in os.listdir(os.path.join(monthPath, d)):
        m = ArchiveImg.regexPic.search(f)
        if m:
          theMatch = m.group(0)
          ArchiveImg.doppelFiles[theMatch] = 1
    return ArchiveImg.doppelFiles.get(self.srcName) is not None

  def dest_mkdir(self, Prefix='   '):
    """
    check for existence, create as needed.
    Return directory name.
    When testing is True, still return name of the (non-existent) directory!
    """
    if not os.path.exists(self.destPath):
      if TESTING:
        dp = ArchiveImg.testLog.get(self.destPath)
        if not dp:
          print("Need to create dir {} **".format(self.destPath))
          ArchiveImg.testLog[self.destPath] = 1
      else:
        print("** Creating dir {} **".format(self.destPath))
        os.mkdir(self.destPath)
        if not os.path.exists(self.destPath):
          print('mkdir "{}" failed')
          return None
        ArchiveImg.createdDirs.append(Prefix+os.path.split(self.destPath)[1])
        return self.destPath
    elif not os.path.isdir(self.destPath):
      print("Path error: {} is not a directory!".format(self.destPath))
      return None
    return self.destPath

  def archive(self, Force=False, PixDestDir='none'):
    "Archive a Single Image File"
    # TODO -- Apply fancier naming to self.destName
    FullDestPath = os.path.join(self.destPath, self.destName)
    protected = False
    opDescription = ''
    if os.path.exists(FullDestPath) or self.doppelganger():
      if Force:
        if VERBOSE:
          opDescription += ("Overwriting {}\n".format(FullDestPath))
        self.incr(self.srcPath)
      else:
        protected = True
        m = ArchiveImg.regexDotAvchd.search(FullDestPath)
        if m:
          FullDestPath = os.path.join(m.group(1), "...", self.srcName)
    else:
      # reportPath = '..' + FullDestPath[len(PixDestDir):]
      reportPath = os.path.join('...', os.path.split(self.destPath)[-1], self.destName)
      opDescription += ("{} -> {}".format(self.srcName, reportPath))
      self.incr(self.srcPath)
    if protected:
      return False
    self.dest_mkdir()
    if len(opDescription) > 0:
      print(opDescription)
    if self.dng.active:
      return self.dng.convert(self.srcPath, self.destPath, self.destName)
    # else:
    return self.safe_copy(FullDestPath)

  def incr(self, FullSrcPath):
    try:
      s = os.stat(FullSrcPath)
    except:
      print("incr() cannot stat source '{}'".format(FullSrcPath))
      print("Err {}".format(sys.exc_info()[0]))
      return False
    self.nBytes += s.st_size
    return True

  def safe_copy(self, DestPath):
    "Copy file, unless we are testing"
    if TESTING:  # TODO - Volume data
      return True # always "work"
    try:
      shutil.copyfile(self.srcPath, DestPath)
    except:
      p = sys.exc_info()[0]
      print("Failed to copy: '{}'!!\n\t{}\n\t{}".format(p, self.srcPath, DestPath))
      print("   Details: errno {} on\n\t'{}'' and\n\t'{}'".format(p.errno, p.filename, p.filename2))
      print("   Detail2: {} chars, '{}'".format(p.characters_written, p.strerror))
      return False
    return True

if __name__ == '__main__':
  print("testing time")
