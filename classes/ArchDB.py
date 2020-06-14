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
    o = img.origin_name
    rec = self.archRecs.get(o)
    if not rec:
      rec = ArchRec()
      self.archRecs[o] = rec
    rec.add_img_file(img)

  def add_folder(self, Folder):
    for item in os.listdir(Folder):
      # TODO: ignore dotfiles
      full = os.path.join(Folder, item)
      if os.path.isdir(full):
        self.add_folder(full)
      else:
        self.add_file(full) # TODO: only images

  def archive_size(self):
    total = 0
    for kn in self.archRecs:
      total += self.archRecs[kn].archive_size()
    return total

  def source_size(self):
    total = 0
    for kn in self.archRecs:
      total += self.archRecs[kn].source_size()
    return total

  def __str__(self):
    return '{} Images:\n'.format(len(self.archRecs))
    # '\n'.join([self.archRecs[a].__str__() for a in self.archRecs]))

#
# Basic tests
#
if __name__ == '__main__':
  f = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'
  f2 = '/home/kevinbjorke/pix/kbImport/Pix/'
  f2 = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun'
  f2 = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_06_WoodX/'
  # f2 = '/home/kevinbjorke/pix/'
  db = ArchDB()
  # d.add_file(f)
  db.add_folder(f2)
  # d.add_folder(os.path.split(f)[0])
  print(db)
  n = 0
  archLocs = {}
  for k in db.archRecs:
    ar = db.archRecs[k]
    if n < 3:
      k = list(db.archRecs.keys())[n]
      ar.print_stats()
    n += 1
    for loc in ar.archive_locations():
      archLocs[loc] = 1
  print("{} Archive Locations".format(len(archLocs)))
  for dest in list(archLocs.keys()):
    print(dest)
  print("Archive Size: {:.4f}MB from {:.6}MB".format(
      db.archive_size()/(1024*1024),
      db.source_size()/(1024*1024)))
