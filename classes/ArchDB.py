#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
"""
import os
import sys
import pickle
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
  @classmethod
  def load(cls, Filename):
    try:
      jf = open(Filename, 'rb')
    except:
      print('Sorry, no "{}"'.format(Filename))
      return None
    try:
      db = pickle.load(jf)
    except:
      print("oops {}".format(jf))
      sys.exit()
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
    o = img.origin()
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
          print('Identified {} files so far'.format(nFiles+TotalFiles))
    return nFiles

  def exists_at(self, DestinationDir):
    missing = []
    for kn in self.archRecs:
      ar = self.archRecs[kn]
      if not ar.exists_at(DestinationDir):
        missing.append("{} {}\n".format(ar.archive_locations(), ar.origin_name()))
    return missing

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

  def count_unknowns(self):
    total = 0
    for kn in self.archRecs:
      total += self.archRecs[kn].count_unknowns()
    return total

  def find_archived_unknowns(self, listfile='unknowns.log', ArchDir='/Volumes/Legacy20/Pix'):
    total = 0
    f = open(listfile, 'w')
    for k in self.archRecs:
      ul = self.archRecs[k].find_archived_unknowns(ArchDir)
      total += len(ul)
      for u in ul:
        f.write(u)
        f.write('\n')
    f.close()
    return total

  def find_unarchived_raw(self, listfile='unarchived-raw.log', ArchDir='/Volumes/Legacy20/Pix'):
    total = 0
    f = open(listfile, 'w')
    for k in self.archRecs:
      ul = self.archRecs[k].unarchived_raw(ArchDir)
      total += len(ul)
      for u in ul:
        f.write(u)
        f.write('\n')
    f.close()
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
      '/home/kevinbjorke/pix/kbImport/Pix',
      # '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_06_WoodX/',
      '/Volumes/pix20s/kbImport/Pix/',
      '/Volumes/pix18/kbImport/Pix/',
      '/Volumes/pix18/Pix/',
      '/Volumes/pix17/Pix/',
      '/Volumes/pix15/Pix/',
      '/Volumes/pix20/Pix/',
      '/Volumes/Sept2013/Pix/',
      # '/Users/kevinbjorke/Pictures/kbImport/Pix/2020/2020-01-Jan/2020_01_02_Putnam/',
      # '/Users/kevinbjorke/Pictures/kbImport/Pix/',
      #'/Users/kevinbjorke/Google Drive/kbImport/Pix/',
      '/Volumes/CameraWork/Pix/']:
    if os.path.exists(f2):
      return f2
  return '.' # less-awkward fail

#
# ############# TESTS
#

def validate(DBFile='pix18-20s-db-L3.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  'remember to assign when testing interactively!'
  # test_db = ArchDB()
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  test_db.describe()
  print('\nVerifying archive at {}:'.format(ArchDir))
  missing = test_db.exists_at(ArchDir)
  print("Identified {} unarchived records, such as:".format(len((missing))))
  print(missing[:3])
  f = open('missing_files.log', 'w')
  for m in missing:
    f.write(m)
  f.close()
  print('logged names')
  return test_db

def update_from_available_drives(SrcDBFile='pix18-20s-db-L3.pkl', SrcFolder=None,
                                 ArchDir='/Volumes/Legacy20/Pix', DestDBFile=None):
  # test_db = ArchDB()
  test_db = ArchDB.load(SrcDBFile)
  # test_pic = get_test_pic()
  if SrcFolder is None:
    test_folder = get_test_folder()
  else:
    test_folder = SrcFolder
  ArchImgFile.pretend(False)
  print("Add test folder: {}".format(test_folder))
  nf = test_db.add_folder(test_folder)
  print('Added {} new files'.format(nf))
  test_db.describe()
  test_db.dop_hunt()
  test_db.archive_to(ArchDir)
  if DestDBFile is None:
    updated_db = SrcDBFile
  else:
    updated_db = DestDBFile
  ArchDB.save(test_db, updated_db)
  ArchDB.describe_created_dirs()

def mini_validate(DBFile='pix18-20s-db-L3.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  # test_db.describe()
  for iid in ['DSCF5603', 'P1090125', 'KBXP1022', 'KBXP1023', 'bjorke_Cuba_XT1A5922', 'KEVT2922']:
    print('-------- {} ---------'.format(iid))
    ar = test_db.archRecs[iid]
    ar.print_arch_status2(ArchDir)
  return test_db

def find_unknowns(DBFile='pix18-20s-db-L3.pkl'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  print('found {} unknown files'.format(test_db.count_unknowns()))
  return test_db

def find_archived_unknowns(DBFile='pix18-20s-db-L3.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  print('found {} archived unknown files'.format(test_db.find_archived_unknowns('unknowns.log', ArchDir)))
  return test_db

def find_unarchived_raws(DBFile='pix18-20s-db-L3.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  print('found {} archived unknown files'.format(test_db.find_unarchived_raw('unarchived-raw.log', ArchDir)))
  return test_db

def complex_record(DBFile='L3.pkl', RecName='DSCF4743'):
  ''''
  others: KEVT2897 DSCF5754
  /Volumes/Legacy20/Pix/2004/300D/2004-04-April/2004_04_24/175_7515.CRW
  /Volumes/Legacy20/Pix/2003/300D/2003-11-Nov/2003_11_16-London/VSMD0052.CRW
  /Volumes/Legacy20/Pix/2006/Digi/2006_08/2006_08_07-Negs/534_3470.DNG
  /Volumes/Legacy20/Pix/2007/Reb/2007_07_29/647CANON/CRW_4704.CRW
  /Volumes/Legacy20/Pix/2007/Reb/2007_07_29/647CANON/CRW_4744.CRW
/Volumes/Legacy20/Pix/2011/2011-03-Mar/2011_03_09/P1000016_1.dng
/Volumes/Legacy20/Pix/2011/2011-03-Mar/2011_03_09_LX5/test.dng
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_24_City/JOKR9972.RAF
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_26_CityIsaac/f10590080.raf
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_26_CityIsaac/f11696064.raf
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_26_CityIsaac/f8935744.raf
/Volumes/Legacy20/Pix/2014/2014-10-Oct/2014_10_08_Pizza/PICS0750.RAF
/Volumes/Legacy20/Pix/2015/2015-09-Sep/2015_09_06_FineArts/bjorke_FineArts_P1080536.DNG
/Volumes/Legacy20/Pix/2006/Digi/2006_06/2006_06_24-hockey/502_0282.DNG
/Volumes/Legacy20/Pix/2006/Digi/2006_06/2006_06_26_slapPractice/502_0298.DNG
  '''
  test_db = ArchDB.load(DBFile)
  ar = test_db.archRecs[RecName]
  ar.print_stats()
  return ar
# problem archive: DSCF4743.RAF - multiple camera versions!

if __name__ == '__main__':
  # mini_validate()
  # find_unknowns()
  # find_archived_unknowns('pix18-20s-db-L4.pkl')
  find_unarchived_raws('pix18-20s-db-L4.pkl')
  #update_from_available_drives('pix18-20s-db-L3.pkl', '/Volumes/Drobo/Pix',
  #            '/Volumes/Legacy20/Pix', 'pix18-20s-db-L4.pkl')
  # sys.exit()
  # update_from_available_drives()
