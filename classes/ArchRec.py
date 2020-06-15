#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
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
    if ArchImg.type is ArchFileType.IGNORE:
      return
    if len(self.versions) > 0 and ArchImg.origin_name != self.origin_name():
      print("ERROR: Can't add '{}'' image to '{}' record".format(
          ArchImg.origin_name, self.origin_name()))
      return
    self.versions.append(ArchImg)

  def add_file(self, Filename):
    '''
    returns origin_name
    '''
    img = ArchImgFile(Filename)
    self.add_img_file(img)
    return self.origin_name()

  def origin_name(self):
    if len(self.versions) < 1:
      return None
    return self.versions[0].origin_name

  def archive_locations(self):
    archLocs = {}
    for v in self.versions:
      archLocs[v.destination_dir] = 1
    return list(archLocs.keys())

  def has_been_edited(self):
    for v in self.versions:
      if v.type is ArchFileType.EDITOR:
        return True
      if v.is_wip:
        return True
    # TODO: multiple outputs, varying sizes? Also true
    return False

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
    return False

  def archive_size(self):
    include_raw = self.should_archive_raw()
    total = 0
    # TODO: watch for duplications
    for v in self.versions:
      if v.type is ArchFileType.RAW and not include_raw:
        continue
      total += v.nBytes
    return total

  def source_size(self):
    "includes all files, regardless"
    total = 0
    for v in self.versions:
      total += v.nBytes
    return total

  def __str__(self):
    return '{}: {} edition(s)'.format(self.origin_name(), len(self.versions))

  def print_stats(self):
    print(self)
    for v in self.versions:
      print(v)
    print("Archived size: {:.2f}MB of {:.4}MB".format(
        self.archive_size() / (1024*1024), self.source_size() / (1024*1024)))

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
