#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
"""
import os
import sys
import re
import shutil
from ArchImgFile import ArchImgFile

if sys.version_info > (3,):
  long = int

# todo complications: files of varying types
# xfc, png, tiff, etc....
class ArchRec(object):
  '''
  Data for one image.
  An image may have multiple representations, of varying formats and sizes.

  '''
  def __init__(self ):
    self.versions = [ ]
  def add_img_file(self, ArchImg):
    self.versions.append(ArchImg)
  def add_file(self, Filename):
    '''
    returns origin_name
    '''
    img = ArchImgFile(Filename)
    o = img.origin_name()
    self.add_img_file(img)
    return o

  def archive_locations(self):
    archLocs = {}
    for v in self.versions:
      archLocs[v.archive_location()] = 1
    return list(archLocs.keys())

  def __str__(self):
    n = self.versions[0].origin_name()
    return '{}: {} edition(s)'.format(n, len(self.versions))
  def print_stats(self):
    print(self)
    for v in self.versions:
      print(v)

#
# Unit Tests, itegration w/ArchImgFile
#
if __name__ == '__main__':
  print("testing time")
  f = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'
  ar = ArchRec()
  o = ar.add_file(f)
  ar.print_stats()
  print("Archive Locations from {}".format(o))
  print(ar.archive_locations())


