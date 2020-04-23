#! /bin/python

import os
import sys
import re
import time
import StorageHierarchy
import Drives
import ArchiveImg

if sys.version_info > (3,):
  long = int

class Volumes(object):
  'object for import/archive environment'
  AVCHDTargets = {"MTS": os.path.join("AVCHD", "BDMV", "STREAM"),
                  "CPI": os.path.join("AVCHD", "BDMV", "CLIPINF"),
                  "MPL": os.path.join("AVCHD", "BDMV", "PLAYLIST"),
                  "BDM": os.path.join("AVCHD", "BDMV"),
                  "TDT": os.path.join("AVCHD", "ACVHDTN"),
                  "TID": os.path.join("AVCHD", "ACVHDTN")}
  AVCHDTargets["JPG"] = os.path.join("AVCHD", "CANONTHM")
  regexAvchd = re.compile('AVCHD')
  regexAvchdFiles = re.compile(r'\.(MTS|CPI|TDT|TID|MPL|BDM)')
  regexVidFiles = re.compile(r'\.(M4V|MP4|MOV|3GP)')
  regexDotFiles = re.compile(r'^\..*(BridgeCache|dropbox\.device)')
  regexJPG = re.compile(r'(.*)\.JPG')
  regexDNGsrc = re.compile(r'(.*)\.RW2') # might be more in the future....
  largestSource = 130 * 1024*1024*1024 # in GB - hack to not scan hard drives as source media
  #
  forceCopies = False
  images = [] # array of ArchiveImg

  def __init__(self, pargs=None, Verbose=False, Win32=False, Testing=False, Version="2020"):
    self.startTime = time.process_time() if sys.version_info > (3, 3)  else time.clock()
    self.verbose = Verbose
    self.win32 = Win32
    self.testing = Testing
    self.version = Version
    self.drives = Drives.Drives(self.verbose, self.win32)
    self.storage = StorageHierarchy.StorageHierarchy(self.testing)
    self.jobname = None
    self.nBytes = long(0)
    self.nFiles = long(0)
    self.nSkipped = long(0)
    self.nConversions = 0
    self.audioPrefix = "" # for edirol
    self.createdDirs = {}
    self.newDirList = []
    self.imgDirs = []
    self.srcMedia = []
    self.prefix = ''
    self.foundImages = False
    if pargs is not None:
      self.user_args(pargs)

  def user_args(self, pargs):
    "set state according to object 'pargs'"
    self.jobname = pargs.jobname
    if pargs.source is not None:
      self.drives.assign_removable(pargs.source)
    if pargs.archive is not None:
      self.PrimaryArchiveList = pargs.archive
      if self.drives.host == 'windows':
        # TODO(kevin): what is wanted here? and why isn't it in the Drives object?
        self.drives.PrimaryArchiveList[0] = re.sub('::', self.drives.PrimaryArchiveList[0])
    self.numerate = bool(pargs.numerate)
    self.verbose = bool(pargs.verbose)
    self.testing = bool(pargs.test)
    if pargs.prefix is not None:
      self.prefix = "{}_".format(pargs.prefix)
    if pargs.jobpref is not None:
      if self.prefix is None:
        self.prefix = "{}_".format(self.jobname)
      else:
        self.prefix = "{}{}_".format(self.prefix, self.jobname)
    # unique to storage
    self.storage.unify = bool(pargs.unify)
    # wrapup
    self.storage.jobname = self.jobname #TODO: messy
    self.storage.prefix = self.prefix # TODO: messy
    self.storage.test = self.testing # self.test
    # self.testing = self.test
    # self.verbose = self.verbose
    if self.verbose:
      print("verbose mode")

def seek_named_dir(self, LookHere, DesiredName, Level=0, MaxLevels=6):
  """
  Recursively look in 'LookHere' for a directory of the 'DesiredName'.
  Return full path or None.
  Don't dig more than MaxLevels deep.
  """
  if Level >= MaxLevels:
    # print("self.seek_named_dir('{}','{}',{},{}): too deep".format(
    #        LookHere,DesiredName,Level,MaxLevels))
    return None
  if not os.path.exists(LookHere):
    print('self.seek_named_dir({}) No such path'.format(LookHere))
    return None
  try:
    allSubs = os.listdir(LookHere)
  except:
    if self.verbose:
      print("self.seek_named_dir('{}','{}'):\n\tno luck, '{}'".format(
          LookHere, DesiredName, sys.exc_info()[0]))
    return None
  for subdir in allSubs:
    if subdir == DesiredName:
      return os.path.join(LookHere, subdir) # got it
  for subdir in allSubs:
    fullpath = os.path.join(LookHere, subdir)
    if os.path.isdir(fullpath):
      sr = self.seek_named_dir(fullpath, DesiredName, Level+1, MaxLevels) # recurse
      if sr is not None:
        return sr
  return None

  def archive(self):
    "Main dealio right here"
    print(self.version)
    if not self.media_are_ready():
      print("No '{}' media found, please connect it to this {} computer".format(
          self.jobname, self.drives.host))
      sys.exit()
    self.announce()
    self.archive_images_and_video()
    self.archive_audio()
    self.report()

  def media_are_ready(self):
    "Do we have all media in place? Find sources, destination, and optional converter"
    if not self.drives.find_archive_drive():
      if self.verbose:
        print('No archive drive found')
      return False
    if not self.drives.verify_archive_locations():
      if self.verbose:
        print('Archive drive failed verification')
      return False
    self.srcMedia = self.find_src_image_media()
    self.foundImages = self.srcMedia and len(self.srcMedia) > 0
    if not self.foundImages:
      if self.verbose:
        print('Images not found')
      return False
    return True

  #
  # Find Source Material
  #

  def find_src_image_media(self):
    foundMedia = []
    if len(self.drives.RemovableMedia) < 1:
      print("Yikes, no source media")
      return None
    for srcDevice in self.drives.RemovableMedia:
      if self.verbose:
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
        foundMedia.append(srcDevice)
    return foundMedia


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
    if not self.foundImages:
      print("No images to archive")
      return
    if self.verbose:
      print("Found These valid image source directories:")
      print("  {}".format(", ".join(self.imgDirs)))
    for srcDir in self.imgDirs:
      print("Archiving Images from '{}'".format(srcDir))
      self.identify_archive_pix(srcDir, self.drives.pixDestDir, self.drives.vidDestDir)
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
            s = os.stat(fullpath)
            self.nBytes += s.st_size
            self.nFiles += 1
            if not self.testing:
              shutil.copy2(fullpath, trackDir)
          else:
            print("Unable to archive audio to {}".format(ArchDir))
        else:
          print("Skipping {}".format(fullpath))

  def verify_image_archive_dir(self, FromDir, PixArchDir, VidArchDir):
    if not os.path.exists(PixArchDir):
      print("Hey, image archive '{}' is vapor!".format(PixArchDir))
      return False
    if not os.path.isdir(PixArchDir):
      print("Hey, image destination '{}' is not a directory!".format(PixArchDir))
      return False
    if VidArchDir is not None and not os.path.exists(VidArchDir):
      print("Caution: Video archive '{}' is vapor, Ignoring it.".format(VidArchDir))
      VidArchDir = None
    if not os.path.exists(FromDir):
      print("Hey, image source '{}' is vapor!".format(FromDir))
      return False
    if not os.path.isdir(FromDir):
      print("Hey, image source '{}' is not a directory!".format(FromDir))
      return False
    return True

  def avchd_src(self, FromDir):
    if Volumes.regexAvchd.search(FromDir):
      return True
    return False

  def dest_avchd_dir_name(self, SrcFile, ArchDir):
    """
    AVCHD has a complex format, let's keep it intact so clips can be archived to blu-ray etc.
    We will say that the dated directory is equivalent to the "PRIVATE" directory in the spec.
    We don't handle the DCIM and MISC sub-dirs.
    """
    privateDir = self.storage.dest_dir_name(SrcFile, ArchDir)
    if privateDir is None:
      print("avchd error")
      return privateDir
    avchdDir = self.storage.safe_mkdir(os.path.join(privateDir, "AVCHD"), "AVCHD")
    for s in ["AVCHDTN", "CANONTHM"]:
      sd = self.storage.safe_mkdir(os.path.join(avchdDir, s), "AVCHD"+os.path.sep+s)
    bdmvDir = self.storage.safe_mkdir(os.path.join(avchdDir, "BDMV"), "BDMV")
    for s in ["STREAM", "CLIPINF", "PLAYLIST", "BACKUP"]:
      sd = self.storage.safe_mkdir(os.path.join(bdmvDir, s), "BDMV"+os.path.sep+s)
    return privateDir

  def dest_name(self, OrigName):
    if self.numerate:
      # TODO extract file extension, format number output, store a number, make sure we are *sorted*
      return "{}{}".format(self.prefix, OrigName)
    return "{}{}".format(self.prefix, OrigName)

  def identify_archive_pix(self, FromDir, PixArchDir, VidArchDir):
    "Archive images and video - recursively if needed"
    # first make sure all inputs are valid
    if not self.verify_image_archive_dir(FromDir, PixArchDir, VidArchDir):
      print("Cannot verify image archive directory")
      return
    # now we can proceed
    localItemCount = 0
    isAVCHDsrc = self.avchd_src(FromDir)
    files = [f for f in os.listdir(FromDir) if not Volumes.regexDotFiles.match(f)]
    files.sort()
    filesOnly = [f for f in files if not os.path.isdir(os.path.join(FromDir, f))]
    if self.verbose and len(filesOnly) > 0:
      print("Archiving {} files from\n    {}".format(len(filesOnly), FromDir))
    for kid in files:
      if Volumes.regexDotFiles.match(kid):
        continue
      fullKidPath = os.path.join(FromDir, kid)
      if os.path.isdir(fullKidPath):
        self.identify_archive_pix(fullKidPath, PixArchDir, VidArchDir)   # recurse
      else:
        # if .MOV or .M4V or .MP4 or .3GP it's a vid
        # if JPG, check to see if there's a matching vid
        kidData = ArchiveImg.ArchiveImg(kid, fullKidPath)
        isSimpleVideo = False
        isAVCHD = False
        avchdType = "JPG"
        upcaseKid = kid.upper()
        kidData.destName = self.dest_name(kid)  # renaming allowed here
        m = Volumes.regexAvchdFiles.search(upcaseKid)
        if m:
          isAVCHD = True
          avchdType = m.group(1)
        isSimpleVideo = Volumes.regexVidFiles.search(upcaseKid) is not None
        m = Volumes.regexDNGsrc.search(upcaseKid)
        if m:
          if Vols.dng.active:
            kidData.dng.active = bool(True and self.win32)
            # renaming allowed here
            kidData.destName = "{}.DNG".format(self.dest_name(m.groups(0)[0]))
        m = Volumes.regexJPG.search(upcaseKid)
        if m:
          # keep an eye open for special thumbnail JPGs....
          if isAVCHDsrc:
            isAVCHD = True
            avchdType = "JPG"
            kidData.destName = kid # renaming NOT allowed for AVCHD thumbnails
          else:
            root = m.groups(0)[0]
            for suf in ['M4V', 'MOV', 'MP4', '3GP']:
              vidName = "{}.{}".format(root, suf) # renaming not allowed here
              if files.__contains__(vidName):
                # print("List contains both {} and {}".format(kid,vidName))
                isSimpleVideo = True # send the thumbnail to the video directory too
        if isAVCHD:
          avchdPath = self.dest_avchd_dir_name(fullKidPath, VidArchDir)
          if avchdPath is None:
            destinationPath = None
          else:
            destinationPath = os.path.join(avchdPath, Volumes.AVCHDTargets[avchdType])
        elif isSimpleVideo:
          destinationPath = self.storage.dest_dir_name(fullKidPath, VidArchDir)
        else:                                                            # a still photo
          destinationPath = self.storage.dest_dir_name(fullKidPath, PixArchDir)
        if destinationPath:
          kidData.destPath = destinationPath
          self.images.append(kidData)
          localItemCount += 1
        else:
          print("Unable to archive media to {}".format(destinationPath))
    if self.verbose and localItemCount > 0:
      print("Found {} items in {}".format(localItemCount, FromDir))

  def archive_found_image_data(self):
    if not self.testing:
      for pic in self.images:
        if pic.archive(Force=self.forceCopies, PixDestDir=self.drives.pixDestDir):
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
    print('JOB NAME: "{}"'.format(self.jobname))

  def report(self):
    self.storage.print_report(self.drives.pixDestDir)
    if len(self.newDirList) > 0:
      print("Created {} Extra Directories:".format(len(self.newDirList)))
      print('\n'.join(self.newDirList))
    print("{} Files, Total MB: {}".format(self.nFiles, self.nBytes/(1024*1024)))
    if self.nSkipped:
      print("Skipped {} files".format(self.nSkipped))
      print("  with {} doppelgangs".format(len(ArchiveImg.ArchiveImg.doppelFiles)))
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
