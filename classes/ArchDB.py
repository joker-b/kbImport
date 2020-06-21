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
  @classmethod
  def load(cls, Filename):
    try:
      jf = open(Filename, 'rb')
    except:
      print('Sorry, no "{}"'.format(Filename))
      return None
    db = pickle.load(jf)
    jf.close()
    # TODO: verify this is the right object
    return db

  @classmethod
  def save(cls, Bbj, Filename):
    "TODO: verify object"
    jf = open(Filename, 'wb')
    pickle.dump(Bbj, jf)
    jf.close()


  @classmethod
  def describe_created_dirs(cls):
    ArchImgFile.describe_created_dirs()

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
    trimmed = ArchImgFile.get_media_name(Filename)
    if self.allFiles.get(trimmed):
      return 0
    self.allFiles[trimmed] = 1
    img = ArchImgFile(Filename)
    o = img.origin_name
    rec = self.archRecs.get(o)
    if not rec:
      rec = ArchRec()
      self.archRecs[o] = rec
    rec.add_img_file(img)
    return 1

  def add_folder(self, Folder, TotalFiles=0):
    nFiles = 0
    if not os.path.exists(Folder):
      return nFiles
    for item in os.listdir(Folder):
      if item[0] == '.':
        continue
      full = os.path.join(Folder, item)
      if os.path.isdir(full):
        nFiles += self.add_folder(full, nFiles+TotalFiles)
      else:
        nFiles += self.add_file(full)
        if ((nFiles+TotalFiles) % 500) == 0:
          print('Identified {} files soe far'.format(nFiles+TotalFiles))
    return nFiles

  def archive_to(self, DestinationDir):
    total = 0
    i = 0
    for kn in self.archRecs:
      total += self.archRecs[kn].archive_to(DestinationDir)
      i += 1
      # TODO remove this...
      #if i > 10000:
      #  break
    return total

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

  def dop_hunt(self):
    n = 0
    for k in self.archRecs:
      ar = self.archRecs[k]
      if ar.spot_doppels().count(True) > 0:
        n += 1
    print("{} of {} records contained doppelgangers".format(n, len(self.archRecs)))

  def __str__(self):
    return '{} Images ({} files):\n'.format(len(self.archRecs), len(self.allFiles))
    # '\n'.join([self.archRecs[a].__str__() for a in self.archRecs]))

  def describe(self):
    print(self)
    n = 0
    archLocs = {}
    for k in self.archRecs:
      ar = self.archRecs[k]
      if n < 3:
        k = list(self.archRecs.keys())[n]
        ar.print_stats()
      n += 1
      for loc in ar.archive_locations():
        archLocs[loc] = 1
    print("{} Archive Locations:".format(len(archLocs)))
    n = 0
    for dest in list(archLocs.keys()):
      print(dest)
      if n >= 3:
        print('...etc')
        break
      n += 1
    print("Archive Size: {:.6g}GB from {:.8g}GB".format(
        self.archive_size()/(1024*1024*1024),
        self.source_size()/(1024*1024*1024)))


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
      '/Volumes/pix18/kbImport/Pix/',
      '/Volumes/pix18/Pix/',
      '/Volumes/pix17/Pix/',
      '/Volumes/pix15/Pix/',
      '/Volumes/pix20/Pix/',
      '/Volumes/Sept2013/Pix/',
      '/Volumes/CameraWork/Pix/']:
    if os.path.exists(f2):
      return f2
  return '.' # less-awkward fail

def build_test_db(Filename = None):
  test_pic = get_test_pic()
  test_folder = get_test_folder()
  # test_folder = '/home/kevinbjorke/pix/'
  if Filename is None:
    db = ArchDB()
  else:
    db = ArchDB.load(Filename)
  # d.add_file(f)
  print("let's scan {}".format(test_folder))
  nf = db.add_folder(test_folder)
  print('Added {} new files'.format(nf))
  return db

def test_archiving(db, DestDir):
  print("sending to {}".format(DestDir))
  total = db.archive_to(DestDir)
  print("Archived {} files".format(total))

#
# #######################
#

if __name__ == '__main__':
  test_db = build_test_db('pix18-20s-db.pkl')
  # test_db = build_test_db('pix18-20s-db.pkl')
  # test_db = ArchDB.load('pix18-20s-db.pkl')
  # test_db.describe()
  # test_db.dop_hunt()
  # save_test(test_db, 'pix18-20s-db.pkl')
  #test_archiving(test_db, '/Volumes/Legacy20/Pix')
  save_test(test_db, 'pix18-20s-db.pkl')
  #ArchDB.describe_created_dirs()

