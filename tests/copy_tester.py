# /usr/bin/python

import sys
if sys.version_info > (3,):
  long = int
import os
import platform
import shutil
import time
import re
import subprocess
import argparse

gTest = False

class Tester:
  base = '/mnt/chromeos/removable'
  def __init__(self):
    self.srcPath = os.path.join(self.base,'X100F/DCIM/148_FUJI/KBXF8019.JPG')
    self.destPath = os.path.join(self.base,
        'BjorkeSSD/kbImport/Pix/2020/2020-04-Apr/2020_04_08_YardTest/YardTest_KBXF8019.JPG')

  def safe_copy(self, DestPath):
    "Copy file, unless we are testing"
    if gTest:  # TODO - Volume data
      return True # always "work"
    try:
      shutil.copyfile(self.srcPath, DestPath)
    except:
      ei = sys.exc_info()
      print(ei)
      p = ei[0]
      pe = p.errno
      print("Failed to copy: '{}'!!\n\t{}\n\t{}".format(p, self.srcPath, DestPath))
      print("   Details: errno {} on\n\t'{}'' and\n\t'{}'".format(p.errno, p.filename, p.filename2))
      print("   Detail2: {} chars, '{}'".format(p.characters_written, p.strerror))
      return False
    return True


if __name__ == '__main__':
  t = Tester()
  t.safe_copy(t.destPath)
