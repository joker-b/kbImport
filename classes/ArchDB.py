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
    nItems = 0
    fname = Folder.split(os.path.sep)[-1]
    for item in os.listdir(Folder):
      if item[0] == '.':
        continue
      full = os.path.join(Folder, item)
      if os.path.isdir(full):
        nFiles += self.add_folder(full, nFiles+TotalFiles)
      else:
        nFiles += self.add_file(full)
        nAll = nFiles + TotalFiles
        if nAll % 500 == 0 and nAll > 0:
          print('Identified {} files of {} from {} so far'.format(
                nAll, nItems, fname))
      nItems += 1
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

  def find_archived_unknowns(self, listfile='unknowns.log', ArchDir=None):
    dest = ArchImgFile.dest(ArchDir)
    total = 0
    f = open(listfile, 'w')
    for k in self.archRecs:
      ul = self.archRecs[k].find_archived_unknowns(dest)
      total += len(ul)
      for u in ul:
        f.write(u)
        f.write('\n')
    f.close()
    return total

  def find_unarchived_raw(self, listfile='unarchived-raw.log', ArchDir=None):
    dest = ArchImgFile.dest(ArchDir)
    total = 0
    f = open(listfile, 'w')
    for k in self.archRecs:
      ul = self.archRecs[k].unarchived_raw(dest, k)
      total += len(ul)
      for u in ul:
        f.write(u)
        f.write('\n')
    f.close()
    return total

  def reconcile_misfiled(self):
    checked = 0
    found = 0
    empties = []
    added = {}
    addList = []
    for arch_key in self.archRecs:
      ar = self.archRecs[arch_key]
      for i in range(len(ar.versions)):
        v = ar.versions[i]
        vo = v.origin()
        #if vo[0] == '_':
        #  print("hmm, '{}' from {}".format(vo, v.filename))
        if arch_key != vo:
          # print("TODO refile {} as {}".format(arch_key, v.origin()))
          found += 1
          destRec = self.archRecs.get(vo, added.get(vo))
          if destRec is None:
            added[vo] = ArchRec()
            destRec = added[vo]
            addList.append("{}\t{}".format(vo, v.basename()))
          destRec.versions.append(v)
          ar.versions[i] = None
        checked += 1
      ar.versions = [a for a in ar.versions if a is not None]
      if len(ar.versions) < 1:
        empties.append(arch_key)
    print("checked {} images, {} mislabelled".format(checked, found))
    print("emptied {} records,added {}".format(len(empties), len(added)))
    logname = "additions.log"
    f = open(logname, 'w')
    for k in added:
      if self.archRecs.get(k):
        print("error, already had a '{}'".format(k))
        f.write("error, already had a '{}'\n".format(k))
        continue
      self.archRecs[k] = added[k]
      # f.write(k)
      # f.write('\n')
    f.write('----- ADDS -----\n')
    f.write('\n'.join(addList))
    f.write('\n\n----- EMPTIES -----\n')
    f.write('\n'.join(empties))
    f.write('\n')
    f.close()
    print("Added! see log at {}".format(logname))

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

def show_a_complex_record(DBFile='L3.pkl', RecName='DSCF4743'):
  '''
  find a record that has multiple shots with the same origin name from multple dates
  '''
  ar = None
  test_db = ArchDB.load(DBFile)
  if test_db:
    ar = test_db.archRecs[RecName]
    ar.print_stats()
  return ar

#
# ############# TESTS
#

if __name__ == '__main__':
  ar = show_a_complex_record('pix18-20s-db-L4.pkl')
