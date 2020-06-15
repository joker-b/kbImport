#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
"""
import os
import sys
from ArchImgFile import ArchImgFile
from ArchRec import ArchRec
import pickle

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
    self.allFiles = {}

  def add_file(self, Filename):
    '''
    TODO: does this know too much about ArchImgFile/ArchRec internals?
    TODO: avoid adding files we already have
    '''
    trimmed = ArchImgFile.get_relative_name(Filename)
    if self.allFiles.get(trimmed):
      return
    self.allFiles[trimmed] = 1
    img = ArchImgFile(Filename)
    o = img.origin_name
    rec = self.archRecs.get(o)
    if not rec:
      rec = ArchRec()
      self.archRecs[o] = rec
    rec.add_img_file(img)

  def add_folder(self, Folder):
    if not os.path.exists(Folder):
      return
    for item in os.listdir(Folder):
      if item[0] == '.':
        continue
      full = os.path.join(Folder, item)
      if os.path.isdir(full):
        self.add_folder(full)
      else:
        self.add_file(full)

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

def get_test_pic():
  return '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'

def get_test_folder():
  # f2 = '/home/kevinbjorke/pix/kbImport/Pix/'
  # f2 = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun'
  for f2 in [
      '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_06_WoodX/',
      '/Volumes/pix20s/kbImport/Pix/',
      '/Volumes/pix20s/kbImport/Pix/2020/2020-06-Jun/2020_06_06_Wood/']:
    if os.path.exists(f2):
      return f2
  return '.' # less-awkward fail

if __name__ == '__main__':
  test_pic = get_test_pic()
  test_folder = get_test_folder()
  # test_folder = '/home/kevinbjorke/pix/'
  db = ArchDB()
  # d.add_file(f)
  print("let's test {}".format(test_folder))
  db.add_folder(test_folder)
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
  print("Archive Size: {:.6f}MB from {:.8}MB".format(
      db.archive_size()/(1024*1024),
      db.source_size()/(1024*1024)))
  jf = open('pix20s-db.pkl', 'wb')
  pickle.dump(db, jf)
  jf.close()

