'''
  A record indicating a single picture file
  TODO: add date, size
  TODO: look for selection markers: ratings, colors
         (may be in exif, in XMP or PP3 files)
  TODO: check for archive status
  TODO: determine best archive location as appropriate
'''

import os
import sys
import re
import subprocess
import platform
import json
import xml.etree.ElementTree as ET
from enum import Enum

# never needed?
if sys.version_info > (3,):
  long = int

'''
EXIF Tags we care about
Rating: 0
UserComment: ""

pp3 fields: (grep)
Rank=2
ColorLabel=0

xmp fields:
xmp:Rating="3"

(xmp files can be general or for specific JPG/RAF files... by DarkTable?)
'''

class ArchFileType(Enum):
  "File types that the archiver may handle in special ways"
  JPG = 1
  RAW = 2
  PP3 = 3
  XMP = 4
  EDITOR = 5
  UNKNOWN = 6
  MISSING = 7
  ERROR = 8
  IGNORE = 9

class HostType(Enum):
  "File types that the archiver may handle in special ways"
  MAC = 1
  WINDOWS = 2
  CROSTINI = 3
  UBUNTU = 4
  LINUX = 5
  UNKNOWN = 6

#pylint: disable=too-many-instance-attributes
# Nine is reasonable in this case.

class ArchImgFile(object):
  '''
  info for for ONE file
  TODO: precompile regex's
  add archive() method
  '''
  RawTypes = ['.RAF', '.DNG', '.CRW', '.CR2']
  IgnoreTypes = ['.SWP', '.LOG']
  EditorTypes = ['.PSD', '.XCF', '.TIFF', '.TIF']
  Platform = HostType.UNKNOWN
  MediaRoot = ''


  @classmethod
  def _initialize_platform(cls):
    if ArchImgFile.Platform is not HostType.UNKNOWN:
      return
    if os.name == 'posix': # mac?
      if platform.uname()[0] == 'Linux':
        ArchImgFile.Platform = HostType.LINUX
        if os.path.exists('/mnt/chromeos'):
          ArchImgFile.Platform = HostType.CROSTINI
          ArchImgFile.MediaRoot = '/mnt/chromeos/removable'
        else:
          ubuRoot = os.path.join('/media/', os.environ['USER'])
          if os.path.exists(ubuRoot):
            ArchImgFile.Platform = HostType.UBUNTU
            ArchImgFile.MediaRoot = ubuRoot
          else:
            ArchImgFile.MediaRoot = '/mnt'
      else: # mac
        ArchImgFile.Platform = HostType.MAC
        ArchImgFile.MediaRoot = '/Volumes'
    elif os.name == "nt":     # or self.opt.win32:
        ArchImgFile.Platform = HostType.WINDOWS
        print("Unsupported: Windows")
        sys.exit()
    else:
      print("Unrecognized OS '{}'".format(os.name))
      sys.exit()


  def __init__(self, Filename=None):
    '''
    basics
    '''
    ArchImgFile._initialize_platform()
    self.filename = Filename
    self.src_volume = None
    self.was_archived = False
    self.is_wip = False
    self._initialize_type() # first
    self._initialize_size() # second
    # others can arrive in arbitrary order
    self._initialize_origin_name()
    self._initialize_work_state()
    self._initialize_rating()
    self._determine_archive_location_()

  def _initialize_type(self):
    '''
    simplify file types for this use
    TODO: GIF and PNG
    '''
    ext = os.path.splitext(self.filename)[1].upper()
    if ext == '.PP3':
      self.type = ArchFileType.PP3
    elif ext == '.XMP':
      self.type = ArchFileType.XMP
    elif ext == '.JPG':
      self.type = ArchFileType.JPG
    elif ArchImgFile.RawTypes.__contains__(ext):
      self.type = ArchFileType.RAW
    elif ArchImgFile.EditorTypes.__contains__(ext):
      self.type = ArchFileType.EDITOR
    elif ArchImgFile.IgnoreTypes.__contains__(ext):
      self.type = ArchFileType.IGNORE
    else:
      self.type = ArchFileType.UNKNOWN

  def _initialize_size(self):
    "calls stat()"
    self.nBytes = 0 # long
    if self.type is ArchFileType.IGNORE:
      return
    try:
      s = os.stat(self.filename)
    except FileNotFoundError:
      print("incr('{}') no file".format(self.filename))
      self.type = ArchFileType.MISSING
      return
    except:
      print("incr('{}') cannot stat source".format(self.filename))
      print("Err {}".format(sys.exc_info()[0]))
      self.type = ArchFileType.ERROR
      return
    self.nBytes += s.st_size

  def _initialize_work_state(self):
    if self.type is ArchFileType.EDITOR:
      self.is_wip = True
      return
    for part in self.filename.split(os.path.sep):
      if part[:4] == 'Work':
        self.is_wip = True
        return


#pylint: disable=attribute-defined-outside-init
#   linter is just confused by the function indirection
  def _query_xmp(self):
    '''
    only if the file is xmp... could also use exiftool!
    '''
    try:
      tree = ET.parse(self.filename)
    except ET.ParseError:
      print("ParseError for '{}'".format(self.filename))
      return
    except:
      print("_query_xmp({}) error: {}".format(self.filename, sys.exc_info()[0]))
      return None
    root = tree.getroot()
    desc = root[0][0] # risky?
    ratingI = '{http://ns.adobe.com/xap/1.0/}Rating'
    labelI = '{http://ns.adobe.com/xap/1.0/}Label'
    self.rating = desc.get(ratingI)
    if self.rating is not None:
      self.rating = int(self.rating)
    self.label = desc.get(labelI)
  def _query_exif(self):
    j = subprocess.run(["exiftool", "-json", "-Rating", "-Label", "-UserComment", self.filename],
          capture_output=True)
    exif = json.loads(j.stdout)[0]
    # print(exif)
    self.rating = exif.get('Rating')
    self.label = exif.get('Label')
  def _query_pp3(self):
    rank_exp = re.compile(r'Rank=(\d+)')
    label_exp = re.compile(r'ColorLabel=(\d+)')
    found = 0
    for line in open(self.filename, 'r'):
      try:
        m = rank_exp.match(r'Rank=(\d+)', line)
      except TypeError:
        m = None
      except:
        print('fail on "{}" from {}'.format(line, self.filename))
        m = None
      if m:
        self.rating = int(m.group(1))
        found += 1
      try:
        m = label_exp.match(line)
      except TypeError:
        m = None
      except:
        print('fail on "{}" from {}'.format(line, self.filename))
        m = None
      if m:
        self.label = int(m.group(1))
        found += 1
      if found >= 2:
        break
  def _initialize_rating(self):
    self.rating = None
    self.label = None
    queries = {
        ArchFileType.PP3: self._query_pp3,
        ArchFileType.XMP: self._query_xmp,
        ArchFileType.JPG: self._query_exif,
        ArchFileType.RAW: self._query_exif
    }
    fn = queries.get(self.type)
    if fn is not None:
      fn()
    return self.rating

  def _initialize_origin_name(self):
    "try to match camera standard naming patterns"
    self.origin_name = None
    if self.filename is None:
      return
    b = os.path.basename(self.filename)
    b = os.path.splitext(b)[0]
    m = re.search(r'[A-Za-z_][A-Za-z_]{3}\d{4}', b)
    if not m:
      self.origin_name = b
    else:
      self.origin_name = m.group()

  def _determine_archive_location_(self):
    '''
    Determines the location where the archive WOULD be, relative to the
      archive directory. Does not actually archive, that determination is
      made elsewhere
    '''
    chain = self.filename.split(os.path.sep)
    if re.match(r'\d{4}$', chain[-4]):
      yearDir = chain[-4]
      monthDir = chain[-3]
      dayDir = chain[-2]
      self.destination_dir = os.path.join(yearDir, monthDir, dayDir)
      return
    if len(chain) >= 2:
      look = 2
      while look <= len(chain):
        if re.match(r'\d{4}$', chain[-look]):
          self.destination_dir = os.path.sep.join(chain[-look:-1])
          return
        look = look + 1
    self.destination_dir = self.folder()

  # END OF INITIALIZERS

  def folder(self):
    chain = self.filename.split(os.path.sep)
    if len(chain) < 2:
      return '.'
    return chain[-2]

  def __str__(self):
    return '.../{}: {:.2f} MB, rating {}, arch to {}'.format(
        os.path.basename(self.filename),
        self.nBytes/(1024*1024),
        self.rating, self.destination_dir)

#
# Test Fixtures
#

def get_test_samples():
  #H = os.environ['HOME']
  #f = H+'/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_13_XE/bjorke_XE_ESCF4060.JPG'
  yDir = '.'
  for v in [
    '/home/kevinbjorke/pix/kbImport/Pix/2020',
    '/Volumes/pix20s/kbImport/Pix/2020']:
    if os.path.exists(v):
      yDir = v
  files = [W for W in [
      yDir+'/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF',
      yDir+'/2020-06-Jun/2020_06_06_WoodX/bjorke_Wood_DSCF6121.JPG',
      yDir+'/2020-06-Jun/2020_06_06_WoodX/bjorke_Wood_DSCF6121.RAF',
      yDir+'/2020-06-Jun/2020_06_06_WoodX/bjorke_Wood_DSCF6121.xmp',
      yDir+'/2020-06-Jun/2020_06_06_Wood/bjorke_Wood_DSCF6121.JPG',
      yDir+'/2020-06-Jun/2020_06_06_Wood/bjorke_Wood_DSCF6121.RAF',
      yDir+'/2020-06-Jun/2020_06_06_Wood/bjorke_Wood_DSCF6121.xmp',
  ] if os.path.exists(W) ]
  return files

#
# Unit Test
#
if __name__ == '__main__':
  for sample_f in get_test_samples():
    if not os.path.exists(sample_f):
      print('skipping {} no file'.format(sample_f))
      continue
    print('----- {}'.format(sample_f))
    aif = ArchImgFile(sample_f)
    # print("Archive Location {}".format(aif._determine_archive_location_()))
    print(aif)
