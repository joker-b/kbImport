# /usr/bin/python

"""
# My quick "one size fits all" import and archive script.
#       THIS VERSION: 28 MARCH 2012
#       NO WARRANTIES EXPRESSED OR IMPLIED. THIS WORKS FOR ME. I AM JUST SHARING INFO.
#       I CHANGE THIS AROUND ALL THE TIME AS MY PERSONAL HARDWARE CHANGES.
#       OKAY TO REDISTRIBUTE AS LONG AS THIS NOTICE IS RETAINED IN FULL.
#
# Usage:
#       Plug in a card, camera, or audio recorder, and (optinally) an external disk.
#       The External disk should have a directory called "Pix" to archive images.
#       The External disk should have a directory called "Vid" to archive video.
#       The External disk should have a directory called "Audio" to archive sounds.
#       (Under windows, if there is no external they will be on "D:" and called "Pix" etc)
#
#       (windows) python kyImport.py [jobname] [srcDriveLetter] [destDriveLetter]
#       (linux) sudo python kbImport.py [jobname]
#
# Converts some files types (RW2) to DNG if the DNG converter is available
#
# Individual archive folders with names based on the FILE date will 
#    be created within those archive directories. The optional [jobname] maybe be
#       appended to the date, e.g. for jobname "NightSkate":
#           R:\Vid\2009\2009-09-Sep\2009_09_27_NightSkate\AVCHD\BDMV\STREAM\02332.MTS
#
# Types recognized include Canon and Panasonic picture formats, AVCHD and QT and AVI files,
#       MP3 and WAV audio
#
# AVCHD support added -- it gets a bit complex for my Canon flash camcorder, as when it
#       mounts it mounts as MULTIPLE drives -- the internal flash, the internal HD, and
#       possibly an extra SDHC card.... this will tend to just get the G: drive until I
#       can figure out a better way to sort-through these. I also try to handle the Canon
#       thumbnail setup.
#
# Doing some experiments - Canon sets the creation time (which I had been using) on AVCHD files
#       to 1979, while the modification time is correct! So now using modification time. Will
#       tweak this for still cameras and audio as needed.
#
# Kevin Bjorke
# http://www.botzilla.com/
"""

# TO-DO -- ignore list eg ['.dropbox.device']
# TO-DO - itemized manifest @ end ("# of pix to dir xxxx" etc)

versionString = "kbImport - 12nov2019 - (c)2019 K Bjorke"

import sys
if sys.version_info > (3,):
  long = int
import os
import platform
import shutil
import time
import re
import subprocess
import argparse

win32ok = True
try:
  import win32file
except:
  win32ok = False

################################################
##### global variable ##########################
################################################

# if gTest is True, create directories, but don't actually copy files (for testing).....
gTest = False
gVerbose = False

#########################################################################################
## FUNCTIONS START HERE #################################################################
#########################################################################################

def seek_named_dir(LookHere, DesiredName, Level=0, MaxLevels=6):
  """
  Recursively look in 'LookHere' for a directory of the 'DesiredName'.
  Return full path or None.
  Don't dig more than MaxLevels deep.
  """
  if Level >= MaxLevels:
    # print("seek_named_dir('{}','{}',{},{}): too deep".format(LookHere,DesiredName,Level,MaxLevels))
    return None
  if not os.path.exists(LookHere):
    print('seek_named_dir({}) No such path'.format(LookHere))
    return None
  try:
    allSubs = os.listdir(LookHere)
  except:
    if gVerbose:
      print("seek_named_dir('{}','{}'):\n\tno luck, '{}'".format(LookHere,DesiredName,sys.exc_info()[0]))
    return None
  for subdir in allSubs:
    if subdir == DesiredName:
      return os.path.join(LookHere, subdir) # got it
  for subdir in os.listdir(LookHere):
    fullpath = os.path.join(LookHere, subdir)
    if os.path.isdir(fullpath):
      sr = seek_named_dir(fullpath, DesiredName, Level+1, MaxLevels) # recurse
      if sr is not None:
        return sr
  return None

#####################################################
## Find or Create Archive Destination Directories ###
#####################################################

class StorageHierarchy(object):
  createdDirs = []

  def __init__(self, Testing=False, Unified=False, jobname=None, UniDir=None):
    self.test = Testing
    self.unify = Unified
    self.jobname = jobname
    self.unified_archive_dir = UniDir # TODO: is this ever actually set?
    self.testLog = {}

  def print_report(self, TopDir='.'):
    if len(self.createdDirs) > 0:
      print("Created directories within {}:".format(TopDir))
      print(' ' + '\n '.join(self.createdDirs))

  def safe_mkdir(self, Dir, PrettierName=None, TestMe=False, Prefix=''):
    """
    check for existence, create as needed.
    'PrettierName' is a print-pretty version.
    Return directory name.
    When testing is True, still return name of the (non-existent) directory!
    """
    report = PrettierName or Dir
    testing = TestMe
    if not os.path.exists(Dir):
      if testing:
        gr = self.testLog.get(report)
        if not gr:
          print("Need to create dir {} **".format(report))
          self.testLog[report] = 1
      else:
        print("** Creating dir {} **".format(report))
        os.mkdir(Dir)
        if not os.path.exists(Dir):
          print('mkdir "{}" failed')
          return None
        self.createdDirs.append(Prefix+os.path.split(Dir)[1])
        return Dir
    elif not os.path.isdir(Dir):
      print("Path error: {} is not a directory!".format(finaldir))
      return None
    return Dir

  ######

  def year_subdir(self, SrcFileStat, ArchDir, ReportName="", TestMe=False):
    "Based on the source file's timestamp, seek (or create) an archive directory"
    # subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_ctime))
    subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_mtime))
    result = os.path.join(ArchDir,subdir)
    report = ReportName + os.path.sep + subdir
    self.safe_mkdir(result, report, TestMe=TestMe)
    return result

  #########

  def month_subdir(self, SrcFileStat, ArchDir, ReportName="", TestMe=False):
    "Based on the source file's timestamp, seek (or create) an archive directory"
    # subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_ctime))
    subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_mtime))
    result = os.path.join(ArchDir,subdir)
    report = ReportName + os.path.sep + subdir
    self.safe_mkdir(result, report, TestMe=TestMe, Prefix='  ')
    return result

  def unified_dir_name(self, ArchDir, ReportName=""):
    'TODO: redundant calls to safe_mkdir?'
    if self.unified_archive_dir is not None:
            return self.unified_archive_dir
    now = time.localtime()
    yearStr = time.strftime("%Y",now)
    yearPath = os.path.join(ArchDir,yearStr)
    archivePath = ReportName+os.path.sep+yearStr
    safe_mkdir(yearPath, archivePath, TestMe=self.test)
    monthStr = time.strftime("%Y-%m-%b",now)
    monthPath = os.path.join(yearPath,monthStr)
    archivePath = archivePath+os.path.sep+monthStr
    safe_mkdir(monthPath, archivePath, TestMe=self.test, Prefix='  ')
    dateStr = time.strftime("%Y_%m_%d",now)
    if self.jobname is not None:
      dateStr = "{}_{}".format(dateStr,self.jobname)
    unifiedDir = os.path.join(monthPath,dateStr)
    archivePath = archivePath+os.path.sep+dateStr
    safe_mkdir(unifiedDir, archivePath, TestMe=self.test, Prefix='    ')
    if not ( os.path.isdir(unifiedDir) or self.test ):
      print("path error: {} is not a directory!".format(unifiedDir))
      return None
    return unifiedDir

  def dest_dir_name(self, SrcFile, ArchDir, ReportName=""):
    """
    Seek or create an archive directory based on the src file's origination date,
    unless 'unify' is active, in which case base it on today's date.
    """
    if self.unify:
      return self.unified_dir_name(ArchDir,ReportName)
    try:
      s = os.stat(SrcFile)
    except:
      print('Stat failure: "{}"'.format(sys.exc_info()[0]))
      return None
    yearDir = self.year_subdir(s, ArchDir, TestMe=self.test)
    monthDir = self.month_subdir(s, yearDir, TestMe=self.test)
    timeFormat = "%Y_%m_%d"
    dateDir = time.strftime(timeFormat, time.localtime(s.st_mtime))
    if self.jobname is not None:
      dateDir = "{}_{}".format(dateDir, self.jobname)
    destDir = os.path.join(monthDir, dateDir)
    reportStr = ReportName + os.path.sep + dateDir
    self.safe_mkdir(destDir, reportStr, TestMe=self.test, Prefix='   ')
    if not ( os.path.isdir(destDir) or self.test ):
      print("Destination path error: '{}' is not a directory!".format(destDir))
      return None
    return destDir

#############################################################
#############################################################
#############################################################


#############################################################
#############################################################
#############################################################

class ArchiveImg(object):
  srcName = ''
  srcPath = '' # full path
  destName = ''
  destPath = ''
  makeDNG = False
  regexDotAvchd = re.compile('(.*).AVCHD')
  def __init__(self, Name, Path):
    self.srcName = Name
    self.srcPath = Path
    self.nBytes = long(0)

  def archive(self, Force=False, PixDestDir='none'):
    "Archive a Single Image File"
    # TODO -- Apply fancier naming to self.destName
    FullDestPath = os.path.join(self.destPath, self.destName)
    protected = False
    if os.path.exists(FullDestPath):
      if Force:
        if gVerbose:
          print("Overwriting {}".format(FullDestPath))
        self.incr(self.srcPath)
      else:
        protected = True
        m = ArchiveImg.regexDotAvchd.search(FullDestPath)
        if m:
          FullDestPath = os.path.join(m.group(1), "...", self.srcName)
    else:
      # reportPath = '..' + FullDestPath[len(PixDestDir):]
      reportPath = os.path.join('...',os.path.split(self.destPath)[-1], self.destName)
      print("{} -> {}".format(self.srcName, reportPath))
      self.incr(self.srcPath)
    if not protected:
      if self.makeDNG:
        return self.dng_convert(self.destPath)
      else:
        return self.safe_copy(FullDestPath)
    return False

  def incr(self, FullSrcPath):
    try:
      s = os.stat(FullSrcPath)
    except:
      print("incr() cannot stat source '{}'".format(FullSrcPath))
      print("Err {}".format(sys.exc_info()[0]))
      return False
    self.nBytes += s.st_size
    return True

  def dng_convert(self):
    "TODO: check for testing?"
    # TODO: get command from Volumes instance
    cmd = "\"{}\" -c -d \"{}\" -o {} \"{}\"".format(self.DNG, self.destPath, self.destName, self.srcPath)
    # print(cmd)
    if self.test:
      print(cmd)
      return True # pretend
    p = os.popen4(r'cmd /k')
    p[0].write('{}\r\n'%cmd)
    p[0].flush()
    p[0].write('exit\r\n')
    p[0].flush()
    print(''.join(p[1].readlines()))
    self.nConversions += 1    # TODO - Volume data
    return True

  def safe_copy(self, DestPath):
    "Copy file, unless we are testing"
    if gTest:  # TODO - Volume data
      return True # always "work"
    try:
      shutil.copy2(self.srcPath, DestPath)
    except:
      print("Failed to copy: '{}'!!\n\t{}\n\t{}".format(sys.exc_info()[0], self.srcPath, DestPath))
      return False
    return True

#############################################################
#############################################################
#############################################################

class Drives(object):
  PrimaryArchiveList = []
  LocalArchiveList = []
  ForbiddenSources = []
  RemovableMedia = []

  def __init__(self):
    if os.name == 'posix': # mac?
      if platform.uname()[0] == 'Linux':
        self.init_drives_linux()
      else: # mac
        self.init_drives_mac()
    elif os.name == "nt":
      self.init_drives_windows()
    else:
      print("Sorry no initialization for OS '{}' yet!".format(os.name))
      sys.exit()

  def init_drives_linux(self):
    """
    TODO: modify for Raspberry
    """
    # mk = '/media/kevin'
    mk = '/mnt'
    self.host = 'linux'
    # pxd = 'pix18'
    # pxd = 'BjorkeSSD'   # TODO(kevin): this is so bad
    pxd = 'pix20'
    self.PrimaryArchiveList = [os.path.join(mk,pxd)]
    self.LocalArchiveList = [os.path.join(os.environ['HOME'],'Pictures','kbImport')]
    self.ForbiddenSources = self.PrimaryArchiveList + self.LocalArchiveList
    self.RemovableMedia = self.available_source_vols([os.path.join(mk,a) for a in os.listdir(mk) if a != pxd and (len(a)<=8)])

  def init_drives_mac(self):
    self.host = 'mac'
    #self.PrimaryArchiveList = [os.path.join(os.environ['HOME'],'Google Drive','kbImport')]
    Vols = os.path.sep+'Volumes'
    self.PrimaryArchiveList = [os.path.join(Vols,D) for D in
                                ['pix20', 'pix18', 'pix15',
                                  os.path.join('BjorkeSSD','kbImport'),
                                  'CameraWork','Liq','Pix17','BJORKEBYTES',
                                  'T3', 'Sept2013'] ]
    self.LocalArchiveList = [os.path.join(os.environ['HOME'],'Pictures','kbImport')]
    self.ForbiddenSources = [os.path.join(Vols,D) for D in
                                [ 'Macintosh HD',
                                  'MobileBackups',
                                  'Recovery',
                                  'My Passport for Mac'] ]
    self.ForbiddenSources = self.ForbiddenSources + self.PrimaryArchiveList + self.LocalArchiveList
    self.RemovableMedia = self.available_source_vols([os.path.join('/Volumes',a) for a in os.listdir('/Volumes')])

  def init_drives_windows(self):
    # Defaults for Windows
    self.host = 'windows'
    self.PrimaryArchiveList = ['F:', 'R:', 'I:']
    self.LocalArchiveList = ['D:']
    self.ForbiddenSources = self.PrimaryArchiveList + self.LocalArchiveList
    self.RemovableMedia = self.available_source_vols(['J:', 'I:', 'H:', 'K:','G:'])
    if win32ok:
      self.RemovableMedia = [d for d in self.RemovableMedia if win32file.GetDriveType(d)==win32file.DRIVE_REMOVABLE]

  def available_source_vols(self,Vols=[]):
      return [a for a in Vols if self.acceptable_source_vol(a)]

  def acceptable_source_vol(self,Path):
    if not os.path.exists(Path):
      if gVerbose:
        print("{} doesn't exist"%(Path))
      return False
    if not os.path.isdir(Path):
      print('Error: Proposed source "{}" is not a directory'.format(Path))
      return False
    if Path in self.ForbiddenSources:
      if gVerbose:
        print("{} forbidden as a source"%(Path))
      return False
    s = os.path.getsize(Path) # TO-DO: this is not how you get volume size!
    if os.path.getsize(Path) > Volumes.largestSource:
      print('Oversized source: "{}"'.format(Path))
      return False
    return True

  def assign_removable(self, SourceName):
      if self.host == 'windows':
        self.RemovableMedia = [ '{}:'.format(SourceName) ]
        self.RemovableMedia[0] = re.sub('::',':',self.RemovableMedia[0])
      else:
        self.RemovableMedia = [ SourceName ]

  def find_archive_drive(self):
    "find an archive destination"
    if self.find_primary_archive_drive():
      return True
    return self.find_local_archive_drive()

  def find_primary_archive_drive(self):
    "find prefered destination"
    for arch in self.PrimaryArchiveList:
      if os.path.exists(arch):
          self.archiveDrive = arch
          if arch[-1] == ':':       # windows
            arch = arch+os.path.sep
          self.pixDestDir = os.path.join(arch,"Pix")
          self.vidDestDir = os.path.join(arch,"Vid")
          self.audioDestDir = os.path.join(arch,"Audio")
          return True
    if gVerbose:
      print("Primary archive disk unavailable, from these {} options:".format(len(self.PrimaryArchiveList)))
      print("  " + "\n  ".join(self.PrimaryArchiveList))
    return False

  def find_local_archive_drive(self):
    "find 'backup' destination"
    for arch in self.LocalArchiveList:
      if os.path.exists(arch):
        self.archiveDrive = arch
        if arch[-1] == ':':
          arch = arch+os.path.sep
        if gVerbose:
          print("Using local archive {}".format(arch))
        self.pixDestDir = os.path.join(arch,"Pix")
        self.vidDestDir = os.path.join(arch,"Vid")
        self.audioDestDir = os.path.join(arch,"Audio")
        return True
    print("Unable to find a local archive, out of these {} possibilities:".format((len(self.LocalArchiveList))))
    print("  " + "\n  ".join(self.LocalArchiveList))
    return False

  def verify_archive_locations(self):
    "double-check existence of the archive directories"
    for d in [self.pixDestDir, self.vidDestDir, self.audioDestDir]:
      if not os.path.exists(d):
        print("Error, cannot verify archive {}".format(d))
        return False
    return True

#############################################################
#############################################################
#############################################################

class Volumes(object):
  'object for import/archive environment'
  AVCHDTargets = {"MTS": os.path.join("AVCHD","BDMV","STREAM"),
                  "CPI": os.path.join("AVCHD","BDMV","CLIPINF"),
                  "MPL": os.path.join("AVCHD","BDMV","PLAYLIST"),
                  "BDM": os.path.join("AVCHD","BDMV"),
                  "TDT": os.path.join("AVCHD","ACVHDTN"),
                  "TID": os.path.join("AVCHD","ACVHDTN")}
  AVCHDTargets["JPG"] = os.path.join("AVCHD","CANONTHM")
  regexAvchd = re.compile('AVCHD')
  regexAvchdFiles = re.compile('\.(MTS|CPI|TDT|TID|MPL|BDM)')
  regexVidFiles = re.compile('\.(M4V|MP4|MOV|3GP)')
  regexDotFiles = re.compile('^\..*(BridgeCache|dropbox\.device)')
  regexJPG = re.compile('(.*)\.JPG')
  regexDNGsrc = re.compile('(.*)\.RW2') # might be more in the future....
  largestSource = 130 * 1024*1024*1024 # in GB - hack to not scan hard drives as source media
  #
  forceCopies = False
  images = [] # array of ArchiveImg

  def __init__(self, pargs=None):
    self.startTime =  time.process_time() if sys.version_info > (3,3)  else time.clock()
    self.drives = Drives()
    self.jobname = None
    self.nBytes = long(0)
    self.nFiles = long(0)
    self.nSkipped = long(0)
    self.nConversions = 0
    self.audioPrefix = "" # for edirol
    self.createdDirs = {}
    self.storage = StorageHierarchy()
    self.dirList = []
    self.imgDirs = []
    self.srcMedia = None
    self.test = False
    self.verbose = False
    self.prefix = None
    if pargs is not None:
      self.user_args(pargs)

  def user_args(self, pargs):
    "set state according to object 'pargs'"
    global gTest
    global gVerbose
    self.jobname = pargs.jobname
    if pargs.source is not None:
      self.drive.assign_removable(pargs.source)
    if pargs.archive is not None:
      self.PrimaryArchiveList = pargs.archive
      if self.host == 'windows':
        self.PrimaryArchiveList[0] = re.sub('::',self.PrimaryArchiveList[0])
    if pargs.test is not None:
      self.test = pargs.test
    if pargs.verbose is not None:
      self.verbose = pargs.verbose
    if pargs.prefix is not None:
      self.prefix = "{}_".format(pargs.prefix)
    if pargs.jobpref is not None:
      if self.prefix is None:
        self.prefix = "{}_".format(self.jobname)
      else:
        self.prefix = "{}{}_".format(self.prefix,self.jobname)
    # unique to storage
    if pargs.unify is not None:
      self.storage.unify = pargs.unify
    # wrapup
    self.storage.jobname = self.jobname
    self.storage.prefix = self.prefix
    self.storage.test = self.test
    gTest = self.test
    gVerbose = self.verbose
    if gVerbose:
      print("verbose mode")

  def archive(self):
    "Main dealio right here"
    print(versionString)
    if not self.media_are_ready():
      print("No '{}' media found, please connect it to this {} computer".format(self.jobname, self.drives.host))
      sys.exit()
    self.announce()
    self.archive_images_and_video()
    self.archive_audio()
    self.report()

  def media_are_ready(self):
    "Do we have all media in place? Find sources, destination, and optional converter"
    if not self.drives.find_archive_drive():
      if gVerbose:
        print('No archive drive found')
      return False
    if not self.drives.verify_archive_locations():
      if gVerbose:
        print('Archive drive failed verification')
      return False
    self.srcMedia = self.find_src_image_media()
    self.foundImages = self.srcMedia is not None
    if not self.foundImages:
      if gVerbose:
        print('Images not found')
      return False
    self.DNG = self.seek_dng_converter()
    return True

  #
  # Find Source Material
  #

  def find_src_image_media(self):
    if len(self.drives.RemovableMedia) < 1:
      print("Yikes, no source media")
      return None
    for srcDevice in self.drives.RemovableMedia:
      if gVerbose:
        print("  Checking {} for source media".format(srcDevice))
      if (self.drives.archiveDrive == srcDevice) or (not os.path.exists(srcDevice)) or os.path.islink(srcDevice):
        continue
      avDir = seek_named_dir(srcDevice, "DCIM", 0, 2)
      if avDir is not None:
        self.imgDirs.append(avDir)
      # we may have images AND video on the device
      avDir = seek_named_dir(srcDevice, "PRIVATE")
      if avDir is None:
        avDir = seek_named_dir(srcDevice, "AVCHD")
      if avDir is not None:
        self.imgDirs.append(avDir)
      if len(self.imgDirs) > 0:
          return srcDevice
    if gVerbose:
      print("nope")
    return None

  #
  # Look for external tools
  #
  def seek_dng_converter(self):
    "find a DNG converter, if one is available"
    converter = None
    pf =  os.environ.get('PROGRAMFILES')
    if pf: # windows
      converter = os.path.join(pf,"Adobe","Adobe DNG Converter.exe")
      if not os.path.exists(converter):
        pfx = os.environ.get('PROGRAMFILES(X86)')
        converter = os.path.join(pfx,"Adobe","Adobe DNG Converter.exe")
      if not os.path.exists(converter):
        converter = None
    return converter

  #
  # Archiving
  #
  def mkArchiveDir(self, Location):
    "possibly create a directory"
    dh = self.createdDirs.get(Location)
    if not dh:
      if not os.path.exists(Location):
        self.createdDirs[Location] = 1
        self.dirList.append(Location)
        safe_mkdir(result, TestMe=self.test)

  def archive_images_and_video(self):
    "Top image archive method"
    if not self.foundImages:
      print("No images to archive")
      return
    if gVerbose:
      print("Found These valid image source directories:")
      print("  {}".format(", ".join(self.imgDirs)))
    for srcDir in self.imgDirs:
      print("Archiving Images from '{}'\n\tto '{}'".format(srcDir, self.drives.pixDestDir))
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
      fullpath = os.path.join(FromDir,kid)
      if os.path.isdir(fullpath):
        self.archive_audio_tracks(fullpath,ArchDir)
      else:
        fp2 = fullpath.upper()
        if fp2.endswith("MP3") or fp2.endswith("WAV"):
          # print("{}...".format(kid))
          trackDir = self.storage.dest_dir_name(fullpath, ArchDir)
          if trackDir:
            print("{} -> {}".format(kid, trackDir) )
            # INSERT CODE FOR RENAMING HERE
            s = os.stat(fullpath)
            self.nBytes += s.st_size
            self.nFiles += 1
            if not self.test:
                shutil.copy2(fullpath,trackDir)
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

  def avchd_src(self,FromDir):
    if Volumes.regexAvchd.search(FromDir):
      return True
    return False

  def dest_avchd_dir_name(self,SrcFile,ArchDir):
    """
    AVCHD has a complex format, let's keep it intact so clips can be archived to blu-ray etc.
    We will say that the dated directory is equivalent to the "PRIVATE" directory in the spec.
    We don't handle the DCIM and MISC sub-dirs.
    """
    privateDir = self.storage.dest_dir_name(SrcFile,ArchDir)
    if privateDir is None:
      print("avchd error")
      return privateDir
    avchdDir = safe_mkdir(os.path.join(privateDir,"AVCHD"), "AVCHD", TestMe=self.test)
    for s in ["AVCHDTN","CANONTHM"]:
      sd = safe_mkdir(os.path.join(avchdDir,s), "AVCHD"+os.path.sep+s, TestMe=self.test)
    bdmvDir = safe_mkdir(os.path.join(avchdDir,"BDMV"), "BDMV", TestMe=self.test)
    for s in ["STREAM","CLIPINF","PLAYLIST","BACKUP"]:
      sd = safe_mkdir(os.path.join(bdmvDir,s), "BDMV"+os.path.sep+s, TestMe=self.test)
    return privateDir

  def dest_name(self, OrigName):
    if self.prefix:
      return "{}{}".format(self.prefix, OrigName)
    return OrigName

  def identify_archive_pix(self, FromDir, PixArchDir, VidArchDir):
    "Archive images and video - recursively if needed"
    # first make sure all inputs are valid
    if not self.verify_image_archive_dir(FromDir, PixArchDir, VidArchDir):
      print("Cannot verify image archive directory")
      return
    # now we can proceed
    localItemCount = 0
    isAVCHDsrc = self.avchd_src(FromDir)
    #files = os.listdir(FromDir)
    files = [f for f in os.listdir(FromDir) if not Volumes.regexDotFiles.match(f) ]
    files.sort()
    filesOnly = [f for f in files if not os.path.isdir(os.path.join(FromDir,f)) ]
    if len(filesOnly) > 0:
      print("Archiving {} files in {}".format(len(filesOnly),FromDir))
    for kid in files:
      if Volumes.regexDotFiles.match(kid):
        continue
      fullKidPath = os.path.join(FromDir,kid)
      if os.path.isdir(fullKidPath):
        self.identify_archive_pix(fullKidPath, PixArchDir, VidArchDir)   # recurse
      else:
        # if .MOV or .M4V or .MP4 or .3GP it's a vid
        # if JPG, check to see if there's a matching vid
        kidData = ArchiveImg(kid, fullKidPath)
        isSimpleVideo = False
        isAVCHD = False
        avchdType = "JPG"
        upcaseKid = kid.upper()
        kidData.destName = self.dest_name(kid)  # renaming allowed here
        m = Volumes.regexAvchdFiles.search(upcaseKid)
        if (m):
          isAVCHD = True
          avchdType = m.group(1)
        isSimpleVideo = Volumes.regexVidFiles.search(upcaseKid) is not None
        m = Volumes.regexDNGsrc.search(upcaseKid)
        if m:
          if Vols.DNG:
            kidData.makeDNG = True
            kidData.destName = "{}.DNG".format(self.dest_name(m.groups(0)[0])) # renaming allowed here
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
              vidName = "{}.{}".format(root,suf) # renaming not allowed here
              if files.__contains__(vidName):
                # print("List contains both {} and {}".format(kid,vidName))
                isSimpleVideo = True # send the thumbnail to the video directory too
        if isAVCHD:
          avchdPath = self.dest_avchd_dir_name(fullKidPath,VidArchDir)
          if avchdPath is None:
            destinationPath = None
          else:
            destinationPath = os.path.join(avchdPath,Volumes.AVCHDTargets[avchdType])
        elif isSimpleVideo:
          destinationPath = self.storage.dest_dir_name(fullKidPath, VidArchDir)
        else:                                                            # a still photo
          destinationPath = self.storage.dest_dir_name(fullKidPath, PixArchDir)
        if destinationPath:
          kidData.destPath = destinationPath
          self.images.append(kidData)
          localItemCount += 1
          #if not self.archive_image(kid, fullKidPath, destinationPath, destName, isDNGible):
          #  self.nSkipped += 1
        else:
          print("Unable to archive media to {}".format(destinationPath))
    if localItemCount > 0:
      print("Found {} items in {}".format(localItemCount, FromDir))

  def archive_found_image_data(self):
    if not self.test:
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
    print('SOURCE MEDIA: "{}"'.format(self.srcMedia))
    print('DESTINATION DRIVE: "{}"'.format(self.drives.archiveDrive))
    print('JOB NAME: "{}"'.format(self.jobname))

  def report(self):
    self.storage.print_report(self.drives.pixDestDir)
    if len(self.dirList) > 0:
      print("Created {} Extra Directories:".format(len(self.dirList)))
      print('\n'.join(self.dirList))
    print("{} Files, Total MB: {}".format(self.nFiles, self.nBytes/(1024*1024)))
    if self.nSkipped:
      print("Skipped {} files".format(self.nSkipped))
    endTime = time.process_time() if sys.version_info > (3,3)  else time.clock()

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

# MAIN EXECUTION BITS ##############

def fake_arguments():
    args = argparse.Namespace()
    args.jobname = 'test'
    args.prefix = 'T_'
    args.jobpref = None
    args.source = None
    args.archive = None
    args.unify = False
    args.test = True
    args.verbose = False
    return args


if __name__ == '__main__':
  if len(sys.argv) > 1:
    parser = argparse.ArgumentParser(description='Import/Archive Pictures, Video, & Audio from removeable media')
    parser.add_argument('jobname',help='appended to date directory names')
    parser.add_argument('-u','--unify',help='Unify imports to a single directory (indexed TODAY)',action="store_true")
    parser.add_argument('-p','--prefix',help='include string in filename as prefix')
    parser.add_argument('-j','--jobpref',help='toggle to include jobname in prefix',action="store_true")
    parser.add_argument('-t','--test',help='test mode: list but do not copy',action="store_true")
    parser.add_argument('-v','--verbose',help='noisy output',action="store_true")
    parser.add_argument('-s','--source',help='Specify source removeable volume (otherwise will guess)')
    parser.add_argument('-a','--archive',help='specify source archive directory (otherwise will use std names)')
    try:
      pargs = parser.parse_args()
    except:
      pargs = fake_arguments()
  else:
    pargs = fake_arguments()

  Vols = Volumes(pargs)
  Vols.archive()

# /disks/Removable/Flash\ Reader/EOS_DIGITAL/DCIM/100EOS5D/
# /disks/Removable/MK1237GSX/DOORKNOB/Pix/

# on linux seek /media/kevin/pix15


