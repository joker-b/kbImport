#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
TODO: Identify doppelgangers - based on size rather than date?
TODO: how to best handle images like DCSF4940 - 9 editions, probably
     at least three different photos from 2014/2019/2020?
"""
import os
import sys
from ArchImgFile import ArchImgFile, ArchFileType

if sys.version_info > (3,):
  long = int

# todo complications: files of varying types
# xfc, png, tiff, etc....
class ArchRec(object):
  '''
  Data for one image.
  An image may have multiple representations, of varying formats and sizes.

  '''
  def __init__(self):
    "the versions array is a list of ArchImagFiles all with matching origin_name"
    self.versions = []

  def add_img_file(self, ArchImg):
    'Add ArchImageFile'
    if ArchImg.get_type() is ArchFileType.IGNORE:
      return
    if len(self.versions) > 0 and ArchImg.origin() != self.origin_name():
      print("ERROR: Can't add '{}'' image to '{}' record".format(
          ArchImg.origin(), self.origin()()))
      return
    self.versions.append(ArchImg)

  def add_file(self, Filename):
    '''
    returns origin()
    '''
    img = ArchImgFile(Filename)
    self.add_img_file(img)
    return self.origin_name()

  def origin_name(self):
    'e.g. KBXF8163'
    if len(self.versions) < 1:
      return None
    return self.versions[0].origin()

  def archive_locations(self):
    archLocs = {}
    for v in self.versions:
      archLocs[v.dest()] = 1
    return list(archLocs.keys())

  def has_been_edited(self):
    for v in self.versions:
      if v.get_type() is ArchFileType.EDITOR:
        return True
      if v.is_wip:
        return True
    # TODO: multiple outputs, varying sizes? Also true
    return False

  def has_no_jpg(self):
    for v in self.versions:
      if v.get_type() is ArchFileType.JPG:
        return False
    return True

  def max_rank(self):
    rank = 0
    for v in self.versions:
      if v.rating is not None:
        try:
          rank = max(rank, v.rating)
        except TypeError:
          print('hmmm, {} vs {} in {}'.format(rank, v.rating, v.filename))
    return rank

  def should_archive_raw(self):
    'the real optimizer - ignore unused raw files'
    if self.has_been_edited():
      return True
    if self.max_rank() > 0:
      return True
    if self.has_no_jpg():
      return True
    return False

  def exists_at(self, DestinationRoot):
    include_raw = self.should_archive_raw()
    dops = self.spot_doppels()
    n = 0
    for i in range(len(self.versions)):
      if not dops[i]:
        v = self.versions[i]
        if v.get_type() is ArchFileType.RAW and not include_raw:
          continue
        if not v.exists_at(DestinationRoot):
          return False
        n += 1
    return n > 0

  def archive_to(self, DestinationRoot):
    include_raw = self.should_archive_raw()
    dops = self.spot_doppels()
    nArchived = 0
    for i in range(len(self.versions)):
      if not dops[i]:
        v = self.versions[i]
        if v.get_type() is ArchFileType.RAW and not include_raw:
          continue
        nArchived += v.archive_to(DestinationRoot)
    return nArchived

  def archive_size(self):
    include_raw = self.should_archive_raw()
    total = 0
    dops = self.spot_doppels()
    for i in range(len(self.versions)):
      if not dops[i]:
        v = self.versions[i]
        if v.get_type() is ArchFileType.RAW and not include_raw:
          continue
        total += v.nBytes
    return total

  def source_size(self):
    "includes all files, regardless"
    total = 0
    for v in self.versions:
      total += v.nBytes
    return total

  def count_unknowns(self):
    d = [v for v in self.versions if v.get_type() == ArchFileType.UNKNOWN]
    return len(d)

  def find_archived_unknowns(self, ArchDir='/Volumes/Legacy20/Pix'):
    u = [v.archived_unknown(ArchDir) for v in self.versions]
    return [b for b in u if b is not None]

  def spot_doppels(self):
    nver = len(self.versions)
    dop = [False] * nver
    base = [os.path.basename(self.versions[i].filename) for i in range(nver)]
    for i in range(nver-1):
      isize = self.versions[i].nBytes
      for j in range(i+1, nver):
        if dop[j]:
          continue
        if base[i] == base[j]:
          jsize = self.versions[j].nBytes
          if isize == jsize:
            dop[j] = True
    # TODO now what? how to report this usefully, and act on the results when
    #    archiving
    '''
    if dop.count(True) > 1 and self.source_size() > 10000: # size guess to avoid tiny files 0:
      print("doppel {} in {} bytes".format(self.origin_name(), self.source_size()))
      self.print_versions()
      print(dop)
      sys.exit()
    '''
    return dop # TODO: review


  def __str__(self):
    return '{}: {} edition(s)'.format(self.origin_name(), len(self.versions))

  def print_versions(self):
    print(self)
    for v in self.versions:
      print(v)

  def print_stats(self):
    self.print_versions()
    print("Archived size: {:.2f}MB of {:.4}MB".format(
        self.archive_size() / (1024*1024), self.source_size() / (1024*1024)))

  def print_arch_status(self, ArchDir='/Volumes/Legacy20/Pix'):
    for v in self.versions:
      v.print_arch_status(ArchDir)

  def print_arch_status2(self, ArchDir='/Volumes/Legacy20/Pix'):
    include_raw = self.should_archive_raw()
    d = self.spot_doppels()
    i = 0
    for v in self.versions:
      if d[i]:
        print('Doppel: {}'.format(v.filename))
      else:
        if v.get_type() is ArchFileType.RAW and not include_raw:
          print('Skipped RAW: {}'.format(os.path.basename(v.filename)))
        else:
          v.print_arch_status()
      i = i + 1

#
# Test fixtures
#
def get_test_folder():
  for f in [
      '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM',
      '/Volumes/pix20s/kbImport/Pix/2020/2020-05-May/2020_05_31_PetaBLM']:
    if os.path.exists(f):
      return f
  return '.'

def get_test_pair(Folder):
  raf = os.path.join(Folder, 'bjorke_BLM_KBXF8642.RAF')
  jpg = os.path.join(Folder, 'bjorke_BLM_KBXF8642.JPG')
  if os.path.exists(raf) and os.path.exists(jpg):
    return (jpg, raf)
  for some_file in os.listdir(Folder):
    sp = os.path.splitext(some_file)
    if sp[-1] == '.RAF':
      jpg = os.path.join(Folder, sp[0]+'.JPG')
      if os.path.exists(jpg):
        raf = os.path.join(Folder, some_file)
        return (jpg, raf)
  return('bad.JPG', 'bad.RAF')



#
# Unit Tests, itegration w/ArchImgFile
#
if __name__ == '__main__':
  print("testing time")
  test_dir = get_test_folder()
  (jpg, raf) = get_test_pair(test_dir)
  ar = ArchRec()
  o = ar.add_file(raf)
  o = ar.add_file(jpg)
  ar.print_stats()
  print("Archive Locations from {}".format(o))
  print(ar.archive_locations())
  print(ar.spot_doppels())
