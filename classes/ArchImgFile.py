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
import shutil
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
  PNG = 10
  VID = 11
  PDF = 12
  GIF = 13

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
  RawTypes = ['.RAF', '.DNG', '.CRW', '.CR2', '.XMP', '.PP3', '.RAW', '.RW2', '.RWL'] # TODO: others?
  IgnoreTypes = ['.SWP', '.LOG']
  EditorTypes = ['.PSD', '.XCF', '.TIFF', '.TIF']
  PlayTypes = ['.MP3', '.MP4', '.MOV']
  month_folder = {'01': '01-Jan',
                  '02': '02-Feb',
                  '03': '03-Mar',
                  '04': '04-Apr',
                  '05': '05-May',
                  '06': '06-Jun',
                  '07': '07-Jul',
                  '08': '08-Aug',
                  '09': '09-Sep',
                  '10': '10-Oct',
                  '11': '11-Nov',
                  '12': '12-Dec'}
  Platform = HostType.UNKNOWN
  MediaRoot = ''
  _mountedSrcVols = {} # TODO try to avoid pickling this...
  _mountedDestVols = {} # TODO try to avoid pickling this...
  _createdDirs = {} # same
  _copyCount = 0 # again
  _alreadyArchivedCount = 0
  _pretending = False # TODO: when _pretending, all mkdirs and exists and copys pretend to work

  @classmethod
  def pretend(cls, Pretending=True):
    cls._pretending = Pretending

  @classmethod
  def describe_created_dirs(cls):
    print("Created {} folders:".format(len(cls._createdDirs)))
    for f in sorted(cls._createdDirs.keys()):
      print(f)
    print('..while copying {} files'.format(cls._copyCount))

  @classmethod
  def _initialize_platform(cls):
    if cls.Platform is not HostType.UNKNOWN:
      return
    if os.name == 'posix': # mac?
      if platform.uname()[0] == 'Linux':
        cls.Platform = HostType.LINUX
        if os.path.exists('/mnt/chromeos'):
          cls.Platform = HostType.CROSTINI
          cls.MediaRoot = '/mnt/chromeos/removable'
        else:
          ubuRoot = os.path.join('/media/', os.environ['USER'])
          if os.path.exists(ubuRoot):
            cls.Platform = HostType.UBUNTU
            cls.MediaRoot = ubuRoot
          else:
            cls.MediaRoot = '/mnt'
      else: # mac
        cls.Platform = HostType.MAC
        cls.MediaRoot = '/Volumes'
    elif os.name == "nt":     # or self.opt.win32:
      cls.Platform = HostType.WINDOWS
      print("Unsupported: Windows")
      sys.exit()
    else:
      print("Unrecognized OS '{}'".format(os.name))
      sys.exit()

  @classmethod
  def get_media_name(cls, Filename):
    'return the name with MediaRoot or local folder stripped off'
    cls._initialize_platform()
    l = len(cls.MediaRoot)
    if Filename[:l] == cls.MediaRoot:
      return Filename[(l+1):]
    home = os.environ['HOME']
    l = len(home)
    if Filename[:l] == home:
      return Filename[(l+1):]
    print("Error: get_media_name({}):\n    not in {} or {}".format(Filename,
                                                                   cls.MediaRoot, home))
    sys.exit()

  @classmethod
  def create_destination_dir(cls, DestinationDir):
    # print("Need {}".format(DestinationDir))
    dl = DestinationDir.split(os.path.sep)
    for i in range(len(dl)):
      partial_dir = os.path.sep.join(dl[:i+1])
      if partial_dir != '':
        if not os.path.exists(partial_dir):
          if cls._pretending:
            if not cls._createdDirs.get(partial_dir):
              print("pretend to make '{}'".format(partial_dir))
          else:
            try:
              os.mkdir(partial_dir)
            except AttributeError:
              print('mkdir({}) failed: {}'.format(partial_dir, sys.exc_info()))
            except:
              print('mkdir({}) failed: {}'.format(partial_dir, sys.exc_info()[0]))
              return False
            if not os.path.exists(partial_dir):
              print('mkdir({}) failed mysteriously'.format(partial_dir))
              return False
          cls._createdDirs[partial_dir] = 1
        else:
          if not os.path.isdir(partial_dir): # even if pretending, fail on this
            print("ERROR: '{}' exists, but NOT a directory".format(partial_dir))
            return False
    return True

  @classmethod
  def volume_path(cls, VolumeName):
    return os.path.join('/Volumes', VolumeName)

  @classmethod
  def dest_volume_ready(cls, DestinationRoot):
    m = cls._mountedDestVols.get(DestinationRoot)
    if m is not None:
      return m
    volname = cls.volume_path(DestinationRoot)
    cls._mountedDestVols[DestinationRoot] = os.path.exists(volname)
    return cls._mountedDestVols[DestinationRoot]

  @classmethod
  def source_volume_ready(cls, VolumeName):
    m = cls._mountedSrcVols.get(VolumeName)
    if m is not None:
      return m
    volname = cls.volume_path(VolumeName)
    cls._mountedSrcVols[VolumeName] = os.path.exists(volname)
    if not cls._mountedSrcVols[VolumeName]:
      '''
      # okay, what about raw name (e.g., home directory)?
      Check this *after* trying the volume name
      '''
      cls._mountedSrcVols[VolumeName] = os.path.exists(VolumeName)
    if cls._mountedSrcVols[VolumeName]:
      print("Source volume {} ready".format(VolumeName))
    else:
      print("Source volume {} missing".format(VolumeName))
    return cls._mountedSrcVols[VolumeName]

  #
  # INSTANCE METHODS BEGIN ####################################################################
  #

  def __init__(self, Filename=None):
    '''
    basics
    '''
    ArchImgFile._initialize_platform()
    self.filename = Filename
    self.type = ArchFileType.UNKNOWN
    self.relative_name = None
    self.src_volume = None
    self.was_archived = False
    self.is_wip = False
    self._initialize_type() # first
    self._initialize_size() # second
    # others can arrive in arbitrary order
    self._find_src_volume()
    # self._initialize_origin_name() # redundant
    self._initialize_work_state()
    self._initialize_rating()
    # self._determine_archive_location_() redundant

  def get_type(self):
    '''
    simplify file types for this use
    TODO: GIF and PNG
    '''
    if self.type == ArchFileType.MISSING or self.type == ArchFileType.ERROR:
      return self.type
    base = os.path.basename(self.filename)
    ext = os.path.splitext(self.filename)[1].upper()
    if ext == '.PP3':
      return ArchFileType.PP3
    elif ext == '.XMP':
      return ArchFileType.XMP
    elif ext == '.JPG':
      return ArchFileType.JPG
    elif ext == '.PNG':
      return ArchFileType.PNG
    elif ext == '.PDF':
      return ArchFileType.PDF
    elif ext == '.GIF':
      return ArchFileType.GIF
    elif ArchImgFile.PlayTypes.__contains__(ext):
      return ArchFileType.VID
    elif ArchImgFile.RawTypes.__contains__(ext):
      return ArchFileType.RAW
    elif ArchImgFile.EditorTypes.__contains__(ext):
      return ArchFileType.EDITOR
    elif ArchImgFile.IgnoreTypes.__contains__(ext):
      return ArchFileType.IGNORE
    elif base == 'Thumbs':
      return ArchFileType.IGNORE
    return ArchFileType.UNKNOWN

  def _initialize_type(self):
    self.type = self.get_type()

  def _initialize_size(self):
    "calls stat()"
    self.nBytes = 0 # long
    if self.get_type() is ArchFileType.IGNORE:
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
    'Look for editor files, or enclosing "Work" folder'
    t = self.get_type()
    if t is ArchFileType.EDITOR or t is ArchFileType.PDF or t is ArchFileType.GIF:
      #self.is_wip = True
      return True
    for part in self.filename.split(os.path.sep):
      if part[:4] == 'Work':
        #self.is_wip = True
        return True
  def has_been_edited(self):
    return self._initialize_work_state()

  def _find_src_volume(self):
    l = len(ArchImgFile.MediaRoot)
    if self.filename[:l] == ArchImgFile.MediaRoot:
      self.relative_name = ArchImgFile.get_media_name(self.filename)
      paths = self.relative_name.split(os.path.sep, 1)
      self.volume = paths[0]
      return
    h = os.environ['HOME']
    l = len(h)
    if self.filename[:l] == h:
      self.volume = h
      self.relative_name = ArchImgFile.get_media_name(self.filename)
      # print('_find_src_volume({}): home volume'.format(self.relative_name))
      return
    # TODO: this test should also accept local folders, e.g. ~/pix/kbImport/xxx...
    print("Error: _find_src_volume({}) unknown".format(self.filename))
    sys.exit()

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
      return
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
    fn = queries.get(self.get_type())
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
    t = self.get_type()
    if t in [ArchFileType.PDF, ArchFileType.GIF, ArchFileType.UNKNOWN]:
      self.origin_name = b
      return
    # 'try P1090086'
    m = re.search(r'_[mo]$', b)
    if m:
      self.origin_name = b
      return
    m = re.search(r'^\d+', b)
    if m:
      self.origin_name = b
      return
    if b[:2] == 'P_' or b[:3] == 'rps' or b[0] == '_':
      self.origin_name = b
      return
    m = re.search(r'Gear360_.*', b)
    if m:
      self.origin_name = m.group()
      return
    m = re.search(r'Hero\d_.*', b)
    if m:
      self.origin_name = m.group()
      return
    m = re.search(r'[PFR]\d{6}\d*', b)
    if m:
      self.origin_name = m.group()
      return
    m = re.search(r'_([A-Za-z_][A-Za-z0-9_]{3}\d{4})', b)
    if m:
      self.origin_name = m.group(1)
      return
    m = re.search(r'^([A-Za-z_][A-Za-z0-9_]{3}\d{4})$', b)
    if m:
      self.origin_name = m.group(1)
      return
    if t == ArchFileType.PNG:
      self.origin_name = b
      return
    m = re.search(r'[0-9A-Z]{3}_\d{4}', b)
    if m:
      self.origin_name = m.group()
      return
    self.origin_name = b

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
      return os.path.join(yearDir, monthDir, dayDir)
    if len(chain) >= 2:
      look = 2
      while look <= len(chain):
        if re.match(r'\d{4}$', chain[-look]):
          return os.path.sep.join(chain[-look:-1])
        look = look + 1
    # didn't find a year folder, so let's try to be more clever
    m = re.match(r'^(\d{4})[-_](\d{2})[_-](\d{2})', self.folder())
    if m:
      yearDir = m.group(1)
      monthDir = '{}-{}'.format(m.group(1), ArchImgFile.month_folder[m.group(2)])
      return os.path.join(yearDir, monthDir, self.folder())
    m = re.match(r'Work(\d{4})', self.folder())
    if m:
      yearDir = m.group(1)
      return os.path.join(yearDir, self.folder())
    # last chance, look in the filename
    m = re.match(r'^(\d{4})[-_](\d{2})[_-](\d{2})', os.path.basename(self.filename))
    if m:
      yearDir = m.group(1)
      monthDir = m.group(2)
      dayDir = m.group(3)
      return os.path.join(yearDir, monthDir, dayDir)
    # no idea so let's just file it in 'Misc'
    return os.path.join('Misc', self.folder())

  def dest(self):
    'we cannot trust stored destination values, but all they are is string manipulation so...'
    return self._determine_archive_location_()

  def src_drive(self):
    return self.relative_name.split(os.path.sep)[0]

  def origin(self):
    self._initialize_origin_name()
    return self.origin_name

  # END OF INITIALIZERS

  def exists_at(self, DestinationRoot):
    'already stored?'
    if not ArchImgFile.dest_volume_ready(DestinationRoot):
      print("<{}>.exists_at({}): not mounted".format(self.origin(), DestinationRoot))
      return False
    destDir = os.path.join(DestinationRoot, self.dest())
    base = os.path.basename(self.filename)
    destFile = os.path.join(destDir, base)
    return os.path.exists(destFile)

  def archived_unknown(self, DestinationRoot):
    'if unknown, return the path to the archive'
    if self.get_type() != ArchFileType.UNKNOWN:
      return None
    if not ArchImgFile.dest_volume_ready(DestinationRoot):
      print("<{}>.archived_unknown({}): not mounted".format(self.origin(), DestinationRoot))
      return None
    destDir = os.path.join(DestinationRoot, self.dest())
    base = os.path.basename(self.filename)
    destFile = os.path.join(destDir, base)
    if os.path.exists(destFile):
      return destFile
    return None

  def unarchived_raw(self, DestinationRoot, IndexName=None):
    'if unknown, return the path to the archive'
    if self.get_type() != ArchFileType.RAW:
      return None
    if not ArchImgFile.dest_volume_ready(DestinationRoot):
      print("<{}>.unarchived_raw({}): not mounted".format(self.origin(), DestinationRoot))
      return None
    destDir = os.path.join(DestinationRoot, self.dest())
    base = os.path.basename(self.filename)
    destFile = os.path.join(destDir, base)
    if not os.path.exists(destFile):
      if IndexName is None or ( IndexName == self.origin() ):
        return "{} # {} {}".format(os.path.join(self.dest(),base), self.src_drive(), self.origin())
      else:
        return "{} # {} {}:{}".format(os.path.join(self.dest(),base), self.src_drive(), self.origin(), IndexName)
    return None

  def archive_to(self, DestinationRoot):
    'archive stuff'
    if not ArchImgFile.source_volume_ready(self.volume):
      print('Cannot get {} data'.format(self.basename()))
      return 0 # not here
    if not ArchImgFile.dest_volume_ready(DestinationRoot):
      print("<{}>.archive_to({}): not mounted".format(self.origin(), DestinationRoot))
      return 0 # not here
    if self.get_type() == ArchFileType.UNKNOWN:
      # "don't copy what you don't know"
      return 0
    destDir = os.path.join(DestinationRoot, self.dest())
    base = os.path.basename(self.filename)
    destFile = os.path.join(destDir, base)
    if os.path.exists(destFile):
      ArchImgFile._alreadyArchivedCount += 1
      return 0 # already done
    if not os.path.exists(destDir):
      if not ArchImgFile.create_destination_dir(destDir):
        return 0 # no destination
    if ArchImgFile._pretending:
      print('pretend copy {} -> {}'.format(self.filename, destFile))
    else:
      try:
        shutil.copyfile(self.filename, destFile)
      except:
        print("ERR: copy({}, {}) got {}".format(self.filename, destFile, sys.exc_info()))
        return 0
    ArchImgFile._copyCount += 1
    if (ArchImgFile._copyCount % 500) == 0:
      print("{} files copied".format(ArchImgFile._copyCount))
    return 1


  def folder(self):
    chain = self.filename.split(os.path.sep)
    if len(chain) < 2:
      return '.'
    return chain[-2]

  def basename(self):
    return os.path.basename(self.filename)

  def __str__(self):
    return '{}: {:.2f}MB, {}*, {} -> {}'.format(
        os.path.basename(self.filename),
        self.nBytes/(1024*1024),
        self.rating,
        self.src_drive(),
        self.dest())

  def print_stats(self):
    print('{}:\n  {:.2f} MB, rating {}\n  arch to {}\n  volume {}\n  relative name {}'.format(
        self.filename,
        self.nBytes/(1024*1024),
        self.rating,
        self.dest(),
        self.volume,
        self.relative_name))

  def print_arch_status(self, ArchDir='/Volumes/Legacy20/Pix'):
    'what is the state of this file? (called within ArchRec)'
    print("{} -> {}: Archived {}".format(os.path.basename(self.filename), self.dest(), self.exists_at(ArchDir)))


#
# Test Fixtures
#

def get_test_folder():
  for v in [
      '/home/kevinbjorke/pix/kbImport/Pix/2020',
      '/Volumes/pix20s/kbImport/Pix/2020']:
    if os.path.exists(v):
      return v
  return '.'

def get_test_samples(yDir = '.'):
  files = [W for W in [
      yDir+'/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF',
      yDir+'/2020-06-Jun/2020_06_06_WoodX/bjorke_Wood_DSCF6121.JPG',
      yDir+'/2020-06-Jun/2020_06_06_WoodX/bjorke_Wood_DSCF6121.RAF',
      yDir+'/2020-06-Jun/2020_06_06_WoodX/bjorke_Wood_DSCF6121.xmp',
      yDir+'/2020-06-Jun/2020_06_06_Wood/bjorke_Wood_DSCF6121.JPG',
      yDir+'/2020-06-Jun/2020_06_06_Wood/bjorke_Wood_DSCF6121.RAF',
      yDir+'/2020-06-Jun/2020_06_06_Wood/bjorke_Wood_DSCF6121.xmp',
  ] if os.path.exists(W)]
  return files

#
# Unit Test
#
if __name__ == '__main__':
  v = get_test_folder()
  for sample_f in get_test_samples(v):
    if not os.path.exists(sample_f):
      print('skipping {} no file'.format(sample_f))
      continue
    print('----- {}'.format(sample_f))
    aif = ArchImgFile(sample_f)
    # print("Archive Location {}".format(aif.dest()))
    aif.print_stats()
  print("TODO - add '{}'' to the relative-path calculation".format(v))
  print("TODO - add dates to 'loose' files?")
