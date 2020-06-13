#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
"""
import os
import sys
from ArchImgFile import ArchImgFile
from ArchRec import ArchRec

if sys.version_info > (3,):
  long = int

class ArchDB(object):
  '''
  Collection of ArchRecs
  TODO: pickle
  TODO: debug messages, sizes, etc
  TODO: archive
  '''
  def __init__(self, dbFile=None):
    if dbFile is not None:
      # TODO load that file
      # if it fails, print an error and continue empty
      print("get db from storage")
    self.archRecs = {}
  def add_file(self, Filename):
    '''
    TODO: does this know too much about ArchImgFile/ArchRec internals?
    '''
    img = ArchImgFile(Filename)
    o = img.origin_name()
    rec = self.archRecs.get(o)
    if not rec:
      rec = ArchRec()
      self.archRecs[o] = rec
    rec.add_img_file(img)
  def add_folder(self, Folder):
    for d in os.listdir(Folder):
      full = os.path.join(Folder,d)
      if os.path.isdir(full):
        self.add_folder(full)
      else:
        self.add_file(full) # TODO: only images
  def __str__(self):
    return '{} Images:\n'.format(len(self.archRecs))  
    # '\n'.join([self.archRecs[a].__str__() for a in self.archRecs]))


def archive_folder(source_path):
  'go through folder adding ArchRecs and add to ArchDB'
  print("blah")

#
# Basic tests
#
if __name__ == '__main__':
  f = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'
  f2 = '/home/kevinbjorke/pix/kbImport/Pix/'
  # f2 = '/home/kevinbjorke/pix/'
  d = ArchDB()
  # d.add_file(f)
  d.add_folder(f2)
  # d.add_folder(os.path.split(f)[0])
  print(d)
  n = 0
  archLocs = {}
  for k in d.archRecs:
    ar = d.archRecs[k]
    if n < 3:
      k = list(d.archRecs.keys())[n]
      ar.print_stats()
    n += 1
    for loc in ar.archive_locations():
      archLocs[loc] = 1
  print("Archive Locations")
  for d in list(archLocs.keys()):
    print(d)





