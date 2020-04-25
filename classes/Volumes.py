#! /usr/bin/python3

import os
import sys
import re
import time
import shutil
from AppOptions import AppOptions
import Store
import Drives
from ImgInfo import ImgInfo
from DNGConverter import DNGConverter

if sys.version_info > (3,):
  long = int

class Avchd(object):
  regexAvchd = re.compile('AVCHD')
  regexAvchdFiles = re.compile(r'\.(MTS|CPI|TDT|TID|MPL|BDM)')
  def __init__(self, Storage):
    self.storage = Storage
    self.AVCHDTargets = {"MTS": os.path.join("AVCHD", "BDMV", "STREAM"),
                         "CPI": os.path.join("AVCHD", "BDMV", "CLIPINF"),
                         "MPL": os.path.join("AVCHD", "BDMV", "PLAYLIST"),
                         "BDM": os.path.join("AVCHD", "BDMV"),
                         "TDT": os.path.join("AVCHD", "ACVHDTN"),
                         "TID": os.path.join("AVCHD", "ACVHDTN")}
    self.AVCHDTargets["JPG"] = os.path.join("AVCHD", "CANONTHM")
    self.type = 'JPG'

  @classmethod
  def valid_source_dir(cls, Filename):
    if cls.regexAvchd.search(Filename):
      return True
    return False

  @classmethod
  def filetype_search(cls, Filename):
    return cls.regexAvchdFiles.search(Filename)

  def dest_dir_name(self, SrcFile, ArchDir):
    """
    AVCHD has a complex format, let's keep it intact so clips can be archived to blu-ray etc.
    We will say that the dated directory is equivalent to the "PRIVATE" directory in the spec.
    We don't handle the DCIM and MISC sub-dirs.
    """
    privateDir = self.storage.dest_dir_name(SrcFile, ArchDir)
    if privateDir is None:
      print("avchd error")
      return privateDir
    adir = self.storage.safe_mkdir(os.path.join(privateDir, "AVCHD"), "AVCHD")
    for s in ["AVCHDTN", "CANONTHM"]:
      self.storage.safe_mkdir(os.path.join(adir, s), "AVCHD"+os.path.sep+s)
    bdmvDir = self.storage.safe_mkdir(os.path.join(adir, "BDMV"), "BDMV")
    for s in ["STREAM", "CLIPINF", "PLAYLIST", "BACKUP"]:
      self.storage.safe_mkdir(os.path.join(bdmvDir, s), "BDMV"+os.path.sep+s)
    return privateDir

  def destination_path(self, fullKidPath, VidArchDir):
    path = self.dest_dir_name(fullKidPath, VidArchDir)
    if path is None:
      return None
    return os.path.join(path, self.AVCHDTargets[self.type])

#######################

class Video(object):
  regexVidFiles = re.compile(r'\.(M4V|MP4|MOV|3GP)')
  def __init__(self):
    pass
  @classmethod
  def has_filetype(cls, Filename):
    return cls.regexVidFiles.search(Filename) is not None


##############################

class Volumes(object):
  '''object for import/archive environment'''
  regexDotFiles = re.compile(r'^\..*(BridgeCache|dropbox\.device)')
  regexJPG = re.compile(r'(.*)\.JPG')

  @classmethod
  def is_dot_file(cls, Filename):
    return cls.regexDotFiles.match(Filename)


  def __init__(self, Options=AppOptions()):
    self.startTime = time.process_time() if sys.version_info > (3, 3)  else time.clock()
    self.opt = Options
    self.drives = Drives.Drives(Options)
    self.storage = Store.Store(Options)
    self.dng = DNGConverter(Options)
    ImgInfo.set_options(Options)
    ImgInfo.set_dng_converter(self.dng)
    self.avchd = Avchd(self.storage)
    self.nBytes = long(0)
    self.nFiles = long(0)
    self.nSkipped = long(0)
    self.nConversions = 0
    self.audioPrefix = "" # for edirol
    self.createdDirs = {}
    self.newDirList = []
    self.imgDirs = []
    self.srcMedia = []
    self.images = [] # array of ImgInfo
    self.process_options()

  def process_options(self):
    "set state according to options object"
    if self.opt.source is not None:
      self.drives.assign_removable(self.opt.source)

  def seek_named_dir(self, ParentDir, FindDir, Level=0, MaxLevels=6):
    """
    Recursively look in 'ParentDir' for a directory of the 'FindDir'.
    Return full path or None.
    Don't dig more than MaxLevels deep.
    """
    if Level >= MaxLevels or not os.path.exists(ParentDir):
      return None
    try:
      allSubs = os.listdir(ParentDir)
    except FileNotFoundError:
      print('No such path: {}'.format(ParentDir))
      return None
    except:
      print("seek_named_dir(): {}".format(sys.exc_info()[0]))
      return None
    for subdir in allSubs:
      if subdir == FindDir:
        return os.path.join(ParentDir, subdir)
    for subdir in allSubs:
      fullpath = os.path.join(ParentDir, subdir)
      if os.path.isdir(fullpath):
        sr = self.seek_named_dir(fullpath, FindDir, Level+1, MaxLevels) # recurse
        if sr is not None:
          return sr
    return None

  def archive(self):
    "Main dealio right here"
    print(self.opt.version)
    if not self.media_are_ready():
      print("No '{}' media found, please connect it to this {} computer".format(
          self.opt.jobname, self.drives.host))
      if not self.opt.testing:
        sys.exit()
    self.announce()
    self.archive_images_and_video()
    self.archive_audio()
    self.report()

  def media_are_ready(self):
    "Do we have all media in place? Find sources, destination, and optional converter"
    if not self.drives.found_archive_drive():
      if self.opt.verbose:
        print('No archive drive found')
      return False
    if not self.drives.verify_archive_locations(self.storage):
      if self.opt.verbose:
        print('Archive drive failed verification')
      return False
    self.find_src_image_media()
    if len(self.srcMedia) == 0:
      if self.opt.verbose:
        print('Images not found')
      return False
    return True

  #
  # Find Source Material
  #

  def find_src_image_media(self):
    self.srcMedia = []
    if len(self.drives.RemovableMedia) < 1:
      print("Yikes, no source media")
      return
    for srcDevice in self.drives.RemovableMedia:
      if self.opt.verbose:
        print("  Checking {} for source media".format(self.drives.pretty(srcDevice)))
      if ((self.drives.archiveDrive == srcDevice) or
          (not os.path.exists(srcDevice)) or
          os.path.islink(srcDevice)):
        continue
      avDir = self.seek_named_dir(srcDevice, "DCIM", 0, 2)
      if avDir is not None:
        self.imgDirs.append(avDir)
      # we may have images AND video on this device
      avDir = self.seek_named_dir(srcDevice, "PRIVATE")
      if avDir is None:
        avDir = self.seek_named_dir(srcDevice, "AVCHD")
      if avDir is not None:
        self.imgDirs.append(avDir)
      if len(self.imgDirs) > 0:
        self.srcMedia.append(srcDevice)

  #
  # Archiving
  #
  def mkArchiveDir(self, Location):
    "possibly create a directory"
    dh = self.createdDirs.get(Location)
    if not dh:
      if not os.path.exists(Location):
        self.createdDirs[Location] = 1
        self.newDirList.append(Location)
        self.storage.safe_mkdir(Location)

  def archive_images_and_video(self):
    "Top image archive method"
    if len(self.srcMedia) == 0:
      print("No images to archive")
      return
    if self.opt.verbose:
      print("Found These valid image source directories:")
      print("  {}".format(", ".join(self.imgDirs)))
    for srcDir in self.imgDirs:
      print("Archiving Images from '{}'".format(srcDir))
      self.seek_files_in(srcDir)
      self.archive_found_image_data()

  def archive_audio(self):
    'TODO fix this method'
    # print("Archiving Audio from '{}'\n\tto '{}'".format(self.srcMedia, self.audioDestDir))
    # self.archive_audio_tracks(srcMedia,audioDestDir) ## HACKKKK
  def archive_audio_tracks(self, FromDir, ArchDir):
    "Archive audio tracks"
    # first validate our inputs
    if self.audioPrefix != "":
      print("NEED Filenames {}XXXX.MP3 etc".format(self.audioPrefix))
    if not os.path.exists(ArchDir):
      print("Hey, destination archive '{}' is vapor!".format(ArchDir))
      return
    if not os.path.isdir(ArchDir):
      print("Hey, audio destination '{}' is not a directory!".format(ArchDir))
      return
    if not os.path.exists(FromDir):
      print("Hey, track source '{}' is vapor!".format(FromDir))
      return
    if not os.path.isdir(FromDir):
      print("Hey, track source '{}' is not a directory!".format(FromDir))
      return
    # okay to proceed
    for kid in os.listdir(FromDir):
      fullpath = os.path.join(FromDir, kid)
      if os.path.isdir(fullpath):
        self.archive_audio_tracks(fullpath, ArchDir)
      else:
        fp2 = fullpath.upper()
        if fp2.endswith("MP3") or fp2.endswith("WAV"):
          # print("{}...".format(kid))
          trackDir = self.storage.dest_dir_name(fullpath, ArchDir)
          if trackDir:
            print("{} -> {}".format(kid, trackDir))
            # INSERT CODE FOR RENAMING HERE
            try:
              s = os.stat(fullpath)
            except FileNotFoundError:
              print('archive_audio_tracks({}) not found'.format(fullpath))
              s = None
            if s:
              self.nBytes += s.st_size
              self.nFiles += 1
              if not self.opt.testing:
                shutil.copy2(fullpath, trackDir)
          else:
            print("Unable to archive audio to {}".format(ArchDir))
        else:
          print("Skipping {}".format(fullpath))

  def verify_image_archive_dir(self, FromDir, PixArchDir, VidArchDir):
    if not os.path.exists(PixArchDir):
      print("Hey, image archive '{}' is vapor!".format(PixArchDir))
      if not self.opt.testing:
        return False
    if not os.path.isdir(PixArchDir):
      print("Hey, image destination '{}' is not a directory!".format(PixArchDir))
      if not self.opt.testing:
        return False
    if VidArchDir is not None and not os.path.exists(self.drives.vidDestDir):
      print("Caution: Video archive '{}' is vapor, Ignoring it.".format(VidArchDir))
      VidArchDir = None # TODO(kevin): what?
    if not os.path.exists(FromDir):
      print("Hey, image source '{}' is vapor!".format(FromDir))
      if not self.opt.testing:
        return False
    if not os.path.isdir(FromDir):
      print("Hey, image source '{}' is not a directory!".format(FromDir))
      if not self.opt.testing:
        return False
    return True

  def add_prefix(self, OrigName):
    return self.opt.add_prefix(OrigName)

  def build_image_data(self, Filename, FromDir, FullPath, files):
    "found a potential file, let's add it as a data record"
    # if .MOV or .M4V or .MP4 or .3GP it's a vid
    # if JPG, check to see if there's a matching vid
    info = ImgInfo(Filename, FullPath)
    isSimpleVideo = False
    isAVCHD = False
    self.avchd.type = "JPG" # blah
    upcaseName = Filename.upper()
    info.destName = self.add_prefix(Filename)  # renaming allowed here
    m = Avchd.filetype_search(upcaseName)
    if m:
      isAVCHD = True
      self.avchd.type = m.group(1)
    isSimpleVideo = Video.has_filetype(upcaseName)
    info.dng_check(self.dng.active)
    m = Volumes.regexJPG.search(upcaseName)
    if m:
      # keep an eye open for special thumbnail JPGs....
      if Avchd.valid_source_dir(FromDir):
        isAVCHD = True
        self.avchd.type = "JPG"
        info.destName = Filename # renaming NOT allowed for AVCHD thumbnails
      else:
        root = m.groups(0)[0]
        for suf in ['M4V', 'MOV', 'MP4', '3GP']:
          vidName = "{}.{}".format(root, suf) # renaming not allowed here
          if files.__contains__(vidName):
            isSimpleVideo = True # send the thumbnail to the video directory too
    if isAVCHD:
      destinationPath = self.avchd.destination_path(FullPath, self.drives.vidDestDir)
    elif isSimpleVideo:
      destinationPath = self.storage.dest_dir_name(FullPath, self.drives.vidDestDir)
    else:
      destinationPath = self.storage.dest_dir_name(FullPath, self.drives.pixDestDir)
    if destinationPath:
      info.destPath = destinationPath
      self.images.append(info)
      return 1
    else:
      print("Unable to archive media to {}".format(destinationPath))
      return 0

  def seek_files_in(self, FromDir):
    "Archive images and video - recursively if needed"
    # first make sure all inputs are valid
    if not self.verify_image_archive_dir(FromDir, self.drives.pixDestDir, self.drives.vidDestDir):
      print("Cannot verify image archive directory")
      return
    # now we can proceed
    localItemCount = 0
    if self.opt.verbose:
      print("seek_files_in({})".format(FromDir))
    # files = [f for f in os.listdir(FromDir) if not Volumes.is_dot_file(f)].sort()
    files = os.listdir(FromDir)
    files = list(files)
    files.sort()
    if files is None:
      files = []
    nFiles = len([f for f in files if not os.path.isdir(os.path.join(FromDir, f))])
    if self.opt.verbose:
      print("Archiving {} files (from {} entries) from\n    {}".format(nFiles, len(files), FromDir))
    for filename in files:
      if Volumes.is_dot_file(filename):
        if self.opt.verbose:
          print("  skipping dotfile {}".format(filename))
        continue
      fullPath = os.path.join(FromDir, filename)
      if os.path.isdir(fullPath):
        if self.opt.verbose:
          print("  down to {}".format(fullPath))
        self.seek_files_in(fullPath)   # recurse
      else:
        localItemCount += self.build_image_data(filename, FromDir, fullPath, files)
    if self.opt.verbose:
      print("Found {} items in {}".format(localItemCount, FromDir))

  def archive_found_image_data(self):
    if self.opt.testing:
      print("{} files found in testing, none moved".format(len(self.images)))
    else:
      for pic in self.images:
        if pic.archive():
          self.nFiles += 1
          self.nBytes += pic.nBytes
        else:
          self.nSkipped += 1

  #
  # reporting
  #
  def announce(self):
    print('SOURCE MEDIA:      {}'.format('\n\t'.join(
        [self.drives.pretty(d) for d in self.srcMedia])))
    print('DESTINATION DRIVE: {}'.format(self.drives.pretty(self.drives.archiveDrive)))
    print('JOB NAME: "{}"'.format(self.opt.jobname))

  def report(self):
    self.storage.print_report(self.drives.pixDestDir)
    if len(self.newDirList) > 0:
      print("Created {} Extra Directories:".format(len(self.newDirList)))
      print('\n'.join(self.newDirList))
    print("{} Files, Total MB: {}".format(self.nFiles, self.nBytes/(1024*1024)))
    if self.nSkipped:
      print("Skipped {} files".format(self.nSkipped))
      print("  with {} doppelgangs".format(len(ImgInfo.doppelFiles)))
    endTime = time.process_time() if sys.version_info > (3, 3)  else time.clock()
    elapsed = endTime-self.startTime
    if elapsed > 100:
      print("{} minutes".format(elapsed/60))
    else:
      print("{} seconds".format(elapsed))
    if self.nBytes > long(0):
      throughput = self.nBytes/elapsed
      throughput /= (1024*1024)
      print("Estimated performance: {} Mb/sec".format(throughput/elapsed))
      if self.nConversions > 0:
        print("Including {} DNG conversions".format(self.nConversions))

if __name__ == '__main__':
  print("testing time")
  opt = AppOptions()
  opt.testing = True
  opt.verbose = True
  opt.set_jobname('VolumesTest')
  v = Volumes(opt)
  fn = "thing.jpg"
  fd = "/home/kevinbjorke/pix"
  fp = os.path.join(fd, fn)
  v.build_image_data(fn, fd, fp, [fn])
  v.archive()
