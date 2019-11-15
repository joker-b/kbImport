# /usr/bin/python

"""
# My quick "one size fits all" import and archive script.
#       THIS VERSION: 28 MARCH 2012
#       NO WARRANTIES EXPRESSED OR IMPLIED. THIS WORKS FOR ME. I AM JUST SHARING INFO.
#       I CHANGE THIS AROUND ALL THE TIME AS MY PERSONAL HARDWARE CHANGES.
#       OKAY TO REDISTRIBUTE AS LONG AS THIS NOTICE IS RETAINED IN FULL.
#
# Usage:
#       Plug in a card, camera, audio recorder, or Android phone, and (optinally) an external disk.
#       The External disk should have a directory called "Pix" to archive images.
#       The External disk should have a directory called "Vid" to archive video.
#       The External disk should have a directory called "Audio" to archive sounds.
#       (Under windows, if there is no external they will be on "D:" and called "Pix" etc)
#
#       (windows) python kyImport.py [JobName] [srcDriveLetter] [destDriveLetter]
#       (linux) sudo python kbImport.py [JobName]
#
# Converts some files types (RW2) to DNG if the DNG converter is available
#
# Individual archive folders with names based on the FILE date will 
#    be created within those archive directories. The optional [JobName] maybe be
#       appended to the date, e.g. for JobName "NightSkate":
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

#########################################################################################
## FUNCTIONS START HERE #################################################################
#########################################################################################

def seek_named_dir(LookHere,DesiredName,Level=0,MaxLevels=6):
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
    print("seek_named_dir('{}','{}'):\n\tno luck, '{}'".format(LookHere,DesiredName,sys.exc_info()[0]))
    return None
  for subdir in allSubs:
    if subdir == DesiredName:
      return os.path.join(LookHere,subdir) # got it
  for subdir in os.listdir(LookHere):
    fullpath = os.path.join(LookHere,subdir)
    if os.path.isdir(fullpath):
      sr = seek_named_dir(fullpath,DesiredName,Level+1,MaxLevels) # recurse
      if sr is not None:
        return sr
  return None

#####################################################
## Find or Create Archive Destination Directories ###
#####################################################

def safe_mkdir(Dir,ReportName=None,TestMe=False):
  """
  check for existence, create as needed.
  'ReportName' is a print-pretty version.
  Return directory name.
  When testing is True, still return name of the (non-existent) directory!
  """
  report = ReportName or Dir
  testing = gTest or TestMe
  if not os.path.exists(Dir):
    if testing:
      print("Need to create dir {} **".format(report))
    else:
      print("** Creating dir {} **".format(report))
      os.mkdir(Dir)
      if not os.path.exists(Dir):
        print('mkdir "{}" failed')
        return None
      return Dir
  elif not os.path.isdir(Dir):
    print("path error: {} is not a directory!".format(finaldir))
    return None
    # return None
  # print('Found exisiting dir "{}"'.format(Dir))
  return Dir

######

def year_subdir(SrcFileStat,ArchDir,ReportName="",TestMe=False):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  report = ReportName+os.path.sep+subdir
  safe_mkdir(result,report,TestMe)
  return result

#########

def month_subdir(SrcFileStat,ArchDir,ReportName="",TestMe=False):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  report = ReportName+os.path.sep+subdir
  safe_mkdir(result,report,TestMe)
  return result

#############################################################
#############################################################
#############################################################

class ImportImage(object):
  srcName = ''
  srcFolder = ''
  srcDate = ''
  destName = ''
  destFolder = ''
  destDate = ''
  def __init__(self,SrcName,SrcFolder=None):
    self.srcName = SrcName
    if SrcFolder is not None:
      self.srcFolder = SrcFolder

  def seek_matching_neighbor(self):
    """
    Check directories who may have the same destination date for files that might be the same file
    so that redundant copies are not made
    """
    # 1 : find dest parent directory
    # 2 : extract date of this directory
    # 3 : identify othe rfolders with the same date (or quit)
    # 4 : exract name of this image
    # 5 : for matching directories, sekk filenames containing that name
    # 6: return any matches (or none)
    print('TODO(kevin): seek_matching_neighbor()')


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
  regexDotAvchd = re.compile('(.*).AVCHD')
  regexAvchdFiles = re.compile('\.(MTS|CPI|TDT|TID|MPL|BDM)')
  regexVidFiles = re.compile('\.(M4V|MP4|MOV|3GP)')
  regexJPG = re.compile('(.*)\.JPG')
  regexDNGsrc = re.compile('(.*)\.RW2') # might be more in the future....
  largestSource = 70 * 1024*1024*1024 # in GB - hack to not scan hard drives as source media
  #
  forceCopies = False

  def init_drives_linux(self):
    """
    TODO: modify for Raspberry
    """
    self.host = 'linux'
    mk = '/media/kevin'
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
    self.PrimaryArchiveList = [os.path.join(os.path.sep+'Volumes',D) for D in
                                ['pix20', 'pix18', 'pix15', os.path.join('BjorkeSSD','kbImport'),
                                  'CameraWork','Liq','Pix17','BJORKEBYTES'] ]
    self.LocalArchiveList = [os.path.join(os.environ['HOME'],'Pictures','kbImport')]
    self.ForbiddenSources = [ '/Volumes/Macintosh HD',
                              '/Volumes/MobileBackups',
                              '/Volumes/Recovery',
                              '/Volumes/My Passport for Mac']
    self.ForbiddenSources = self.ForbiddenSources + self.PrimaryArchiveList + self.LocalArchiveList
    self.RemovableMedia = self.available_source_vols([os.path.join('/Volumes',a) for a in os.listdir('/Volumes')])

  def init_drives_windows(self):
    # Defaults for Windows
    self.host = 'windows'
    self.PrimaryArchiveList = ['R:', 'I:', 'G:']
    self.LocalArchiveList = ['D:']
    self.ForbiddenSources = self.PrimaryArchiveList + self.LocalArchiveList
    self.RemovableMedia = self.available_source_vols(['J:', 'I:', 'H:', 'K:','G:', 'F:'])
    if win32ok:
      self.RemovableMedia = [d for d in self.RemovableMedia if win32file.GetDriveType(d)==win32file.DRIVE_REMOVABLE]

  def __init__(self):
    self.startTime = time.clock()
    pxd = ['pix18', 'pix20', 'pix15', 'BjorkeSSD'+os.path.sep+'kbImport', 'T3', 'Sept2013']
    if os.name == 'posix': # mac?
      if platform.uname()[0] == 'Linux':
        self.init_drives_linux()
      else: # mac
        self.init_drives_mac()
    elif os.name == "nt":
      self.init_drives_windows()
    else:
      print("Sorry no code for OS '{}' yet!".format(os.name))
      sys.exit()
    self.JobName = None
    self.nBytes = 0L
    self.nFiles = 0L
    self.nSkipped = 0L
    self.nConversions = 0
    self.audioPrefix = "" # for edirol
    self.createdDirs = {}
    self.dirList = []
    self.imgDirs = []
    self.srcMedia = None
    self.unify = False
    self.unified_archive_dir = None
    self.prefix = None

  def user_args(self, pargs):
    "set state according to object 'pargs'"
    self.JobName = pargs.jobname
    if pargs.source is not None:
      if self.host == 'windows':
        self.RemovableMedia = [ '{}:'.format(pargs.source) ]
        self.RemovableMedia[0] = re.sub('::',':',self.RemovableMedia[0])
      else:
        self.RemovableMedia = [ pargs.source ]
    if pargs.archive is not None:
      self.PrimaryArchiveList = pargs.archive
      if self.host == 'windows':
        self.PrimaryArchiveList[0] = re.sub('::',self.PrimaryArchiveList[0])
    if pargs.unify is not None:
      self.unify = pargs.unify
    if pargs.prefix is not None:
      self.prefix = "{}_".format(pargs.prefix)
    if pargs.jobpref is not None:
      if self.prefix is None:
        self.prefix = "{}_".format(self.JobName)
      else:
        self.prefix = "{}{}_".format(self.prefix,self.JobName)

  def archive(self):
    "Main dealio right here"
    print(versionString)
    if not self.media_are_ready():
      print("Sorry, no '{}' source media found, please connect to {}".format(self.JobName,self.host))
      sys.exit()
    self.announce()
    self.archive_images_and_video()
    self.archive_audio()
    self.report()

  def media_are_ready(self):
    "Do we have all media in place?"
    if not self.find_archive_drive():
      return False
    if not self.verify_archive_locations():
      return False
    self.srcMedia = self.find_src_media()
    if self.srcMedia is None:
      return False
    self.DNG = self.seek_dng_convertor()
    return True

  #
  # seek needed resources on disk
  #
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
    print("Primary archive disk unavailable ({})".format(len(self.PrimaryArchiveList)))
    print("\t\" + \n\t".join(self.PrimaryArchiveList))
    sys.exit() # TODO(kevin): fix this
    return False

  def find_local_archive_drive(self):
    "find 'backup' destination"
    for arch in self.LocalArchiveList:
      if os.path.exists(arch):
        self.archiveDrive = arch
        if arch[-1] == ':':
          arch = arch+os.path.sep
        print("Using local archive {}".format(arch))
        self.pixDestDir = os.path.join(arch,"Pix")
        self.vidDestDir = os.path.join(arch,"Vid")
        self.audioDestDir = os.path.join(arch,"Audio")
        return True
    print("Unable to find a local archive (out of {} possible)".format((len(self.LocalArchiveList))))
    print("\n".join(self.LocalArchiveList))
    return False

  def find_archive_drive(self):
    "find an archive destination"
    if self.find_primary_archive_drive():
      return True
    return self.find_local_archive_drive()

  def verify_archive_locations(self):
    "double-check existence of the archive directories"
    for d in [self.pixDestDir, self.vidDestDir, self.audioDestDir]:
      if not os.path.exists(d):
        print("Error, cannot verify archive {}".format(d))
        return False
    return True

  #
  # Find Source Material
  #
  def available_source_vols(self,Vols=[]):
      return [a for a in Vols if self.acceptable_source_vol(a)]

  def acceptable_source_vol(self,Path):
    if not os.path.exists(Path):
      return False
    if not os.path.isdir(Path):
      print('Error: Proposed source "{}" is not a directory'.format(Path))
      return False
    if Path in self.ForbiddenSources:
      return False
    s = os.path.getsize(Path) # TO-DO: this is not how you get volume size!
    if os.path.getsize(Path) > Volumes.largestSource:
      print('Oversized source: "{}"'.format(Path))
      return False
    return True

  def find_DCIM(self,srcDisk):
      avDir = seek_named_dir(srcDisk,"DCIM",0,2)
      if avDir is not None:
        self.imgDirs.append(avDir)
        self.foundImages = True
        return True
      return False
  def find_PRIVATE(self,srcDisk):
      avDir = seek_named_dir(srcDisk,"PRIVATE")
      if avDir is not None:
        self.imgDirs.append(avDir)
        self.foundImages = True
        return True
      return False
  def find_AVCHD(self,srcDisk):
      avDir = seek_named_dir(srcDisk,"AVCHD")
      if avDir is not None:
        self.imgDirs.append(avDir)
        self.foundImages = True
        return True
      return False
  def identify_phone(self,srcDisk):
      avDir = seek_named_dir(srcDisk,".android_secure",0,2)
      if avDir is not None:
        print("Android Phone Storage Identified")
        return True
      return False
  def find_extra_android_image_dirs(self,srcMedia):
    found = False
    print("looking for extra Android image dirs on drive '{}'".format(srcMedia))
    for aTest in ["AndCam3D", "AndroPan", "CamScanner", "ReducePhotoSize", "retroCamera",
            "FxCamera", "PicSay", "magicdoodle", "magicdoodlelite", "penman", 
            "Video", "Vignette", "SketchBookMobile", "sketcher"]:
      nDir = seek_named_dir(srcMedia,aTest,0,4)
      if nDir is not None:
        self.imgDirs.append(nDir)
        found = True
    return found
  def find_src_media(self):
    srcMedia = None
    self.foundImages = False
    isPhone = False
    for srcDisk in self.RemovableMedia:
      print(srcDisk)
      if (self.archiveDrive == srcDisk) or (not os.path.exists(srcDisk)) or os.path.islink(srcDisk):
        continue
      srcMedia = srcDisk
      self.find_DCIM(srcDisk)
      isPhone = self.identify_phone(srcDisk)
      if not isPhone:
        p = self.find_PRIVATE(srcDisk)
        if not p:
          self.find_AVCHD(srcDisk)
      if self.foundImages or isPhone:
          break
    if self.foundImages:
      isPhone |= self.find_extra_android_image_dirs(srcMedia)
    return srcMedia

  #
  # Look for external tools
  #
  def seek_dng_convertor(self):
    "find a DNG convertor, if one is available"
    convertor = None
    if os.environ.has_key('PROGRAMFILES'): # windows
      convertor = os.path.join(os.environ['PROGRAMFILES'],"Adobe","Adobe DNG Converter.exe")
      if not os.path.exists(convertor):
        convertor = os.path.join(os.environ['PROGRAMFILES(X86)'],"Adobe","Adobe DNG Converter.exe")
      if not os.path.exists(convertor):
        convertor = None
    return convertor

  #
  # Archiving
  #
  def mkArchiveDir(self,Location):
    "possibly create a directory"
    if not self.createdDirs.has_key(Location):
      if not os.path.exists(Location):
        self.createdDirs[Location] = 1
        self.dirList.append(Location)
        safe_mkdir(result)

  def unified_dir_name(self,ArchDir,ReportName=""):
    if self.unified_archive_dir is not None:
            return self.unified_archive_dir
    now = time.localtime()
    yearStr = time.strftime("%Y",now)
    yearPath = os.path.join(ArchDir,yearStr)
    archivePath = ReportName+os.path.sep+yearStr
    safe_mkdir(yearPath,archivePath)
    monthStr = time.strftime("%Y-%m-%b",now)
    monthPath = os.path.join(yearPath,monthStr)
    archivePath = archivePath+os.path.sep+monthStr
    safe_mkdir(monthPath,archivePath)
    dateStr = time.strftime("%Y_%m_{}",now)
    if self.JobName is not None:
            dateStr = "{}_{}".format(dateStr,self.JobName)
    unifiedDir = os.path.join(monthPath,dateStr)
    archivePath = archivePath+os.path.sep+dateStr
    safe_mkdir(unifiedDir,archivePath)
    if not os.path.isdir(unifiedDir):
            print("path error: {} is not a directory!".format(unifiedDir))
            return None
    return unifiedDir

  def dest_dir_name(self,SrcFile,ArchDir,ReportName=""):
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
    yearDir = year_subdir(s,ArchDir)
    monthDir = month_subdir(s,yearDir)
    timeFormat = "%Y_%m_{}"
    dateDir = time.strftime(timeFormat,time.localtime(s.st_mtime))
    if self.JobName is not None:
      dateDir = "{}_{}".format(dateDir,self.JobName)
    destDir = os.path.join(monthDir,dateDir)
    reportStr = ReportName+os.path.sep+dateDir
    safe_mkdir(destDir,reportStr)
    if not os.path.isdir(destDir):
      print("Destination path error: '{}' is not a directory!".format(destDir))
      return None
    return destDir

  def archive_images_and_video(self):
    "Top image archive method"
    if not self.foundImages:
      print("No images to archive")
      return
    print("Found These valid image source directories:")
    print("  {}".format(", ".join(self.imgDirs)))
    for srcDir in self.imgDirs:
      print("Archiving Images from '{}'\n\tto '{}'".format(srcDir,self.pixDestDir))
      self.archive_pix(srcDir,self.pixDestDir,self.vidDestDir)

  def archive_audio(self):
    print("Archiving Audio from '{}'\n\tto '{}'".format(self.srcMedia,self.audioDestDir))
    # self.archive_audio_tracks(srcMedia,audioDestDir) ## HACKKKK
  def archive_audio_tracks(self,FromDir,ArchDir):
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
          trackDir = dest_dir_name(fullpath,ArchDir)
          if trackDir:
            print("{} -> {}".format(kid,trackDir) )
            # INSERT CODE FOR RENAMING HERE
            s = os.stat(fullpath)
            self.nBytes += s.st_size
            self.nFiles += 1
            if not gTest:
                shutil.copy2(fullpath,trackDir)
          else:
            print("Unable to archive audio to {}".format(ArchDir))
        else:
          print("Skipping {}".format(fullpath))

  def verify_image_archive_dir(self,FromDir,PixArchDir,VidArchDir):
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
    privateDir = self.dest_dir_name(SrcFile,ArchDir)
    if privateDir is None:
      print("avchd error")
      return privateDir
    avchdDir = safe_mkdir(os.path.join(privateDir,"AVCHD"),"AVCHD")
    for s in ["AVCHDTN","CANONTHM"]:
      sd = safe_mkdir(os.path.join(avchdDir,s),"AVCHD{}{}".format(os.path.sep,s))
    bdmvDir = safe_mkdir(os.path.join(avchdDir,"BDMV"),"BDMV")
    for s in ["STREAM","CLIPINF","PLAYLIST","BACKUP"]:
      sd = safe_mkdir(os.path.join(bdmvDir,s),"BDMV{}{}".format(os.path.sep,s))
    return privateDir

  def dest_name(self,OrigName):
    if self.prefix:
      return "{}{}".format(self.prefix,OrigName)
    return OrigName

  def archive_pix(self,FromDir,PixArchDir,VidArchDir):
    "Archive images and video - recursively if needed"
    # first make sure all inputs are valid
    if not self.verify_image_archive_dir(FromDir,PixArchDir,VidArchDir):
      print("Cannot verify image archive directory")
      return
    # now we can proceed
    isAVCHDsrc = self.avchd_src(FromDir)
    files = os.listdir(FromDir)
    files.sort()
    print("Archivng {} files in {}".format(len(files),FromDir))
    for kid in files:
      fullKidPath = os.path.join(FromDir,kid)
      if os.path.isdir(fullKidPath):
        self.archive_pix(fullKidPath,PixArchDir,VidArchDir) # recurse
      else:
        # if .MOV or .M4V or .MP4 or .3GP it's a vid
        # if JPG, check to see if there's a matching vid
        isSimpleVideo = False
        isDNGible = False
        isAVCHD = False
        avchdType = "JPG"
        kUp = kid.upper()
        destName = self.dest_name(kid) # renaming allowed here
        m = Volumes.regexAvchdFiles.search(kUp)
        if (m):
          isAVCHD = True
          avchdType = m.group(1)
        isSimpleVideo = Volumes.regexVidFiles.search(kUp) is not None
        m = Volumes.regexDNGsrc.search(kUp)
        if m:
          if Vols.DNG:
            isDNGible = True
            destName = "{}.DNG".format(self.dest_name(m.groups(0)[0])) # renaming allowed here
        m = Volumes.regexJPG.search(kUp)
        if m:
          # keep an eye open for special thumbnail JPGs....
          if isAVCHDsrc:
            isAVCHD = True
            avchdType = "JPG"
            destName = kid # renaming NOT allowed for AVCHD thumbnails
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
          destinationPath = self.dest_dir_name(fullKidPath,VidArchDir)
        else: # still phot
          destinationPath = self.dest_dir_name(fullKidPath,PixArchDir)
        if destinationPath:
          if not self.archive_image(kid,fullKidPath,destinationPath,destName,isDNGible):
            self.nSkipped += 1
        else:
          print("Unable to archive media to {}".format(destinationPath))

  def incr(self,FullSrcPath):
    try:
      s = os.stat(FullSrcPath)
    except:
      print("incr() cannot stat source '{}'".format(FullSrcPath))
      print("Err {}".format(sys.exc_info()[0]))
      return False
    self.nBytes += s.st_size
    self.nFiles += 1
    return True

  def archive_image(self,SrcName,FullSrcPath,DestDir,DestName,IsDNGible):
    "Archive a Single Image File"
    # TO-DO -- Apply fancier naming to DestName
    if SrcName == '.dropbox.device': # TO-DO -- be more sophisticated here
      return False
    FullDestPath = os.path.join(DestDir,DestName)
    protected = gTest
    destinationPath = DestDir
    if os.path.exists(FullDestPath):
      if self.forceCopies:
        print("overwriting {}".format(FullDestPath))
        self.incr(FullSrcPath)
      else:
        protected = True
        m = Volumes.regexDotAvchd.search(FullDestPath)
        if m:
          destinationPath = m.group(1)
          FullDestPath = os.path.join(destinationPath,"...",SrcName)
    else:
            reportPath = '..' + FullDestPath[len(self.pixDestDir):]
            print("{} -> {}".format(SrcName,reportPath))
            self.incr(FullSrcPath)
    if not protected:
      if IsDNGible:
        return self.dng_convert(destinationPath,DestName,FullSrcPath)
      else:
        return self.safe_copy(FullSrcPath,FullDestPath)
    return False

  def safe_copy(self,FullSrcPath,DestPath):
    "Copy file, unless we are testing"
    if gTest:
      return True # always "work"
    try:
      shutil.copy2(FullSrcPath,DestPath)
    except:
      print("Failed to copy, '{}'!!\n\t{}\n\t{}".format(sys.exc_info()[0],FullSrcPath,DestPath))
      return False
    return True

  def dng_convert(self,DestPath,DestName,FullSrcPath):
    cmd = "\"{}\" -c -d \"{}\" -o {} \"{}\"".format(self.DNG,DestPath,DestName,FullSrcPath)
    # print(cmd)
    if gTest:
      print(cmd)
      return True # pretend
    p = os.popen4(r'cmd /k')
    p[0].write('{}\r\n'%cmd)
    p[0].flush()
    p[0].write('exit\r\n')
    p[0].flush()
    print(''.join(p[1].readlines()))
    self.nConversions += 1
    # DNGscript.write("{}\n".format(cmd))
    # ret = subprocess.call(cmd)
    # print("ret was {}".format(ret))
    return True

  #
  # reporting
  #
  def announce(self):
    print('SOURCE MEDIA: "{}"'.format(self.srcMedia))
    print('DESTINATION DRIVE: "{}"'.format(self.archiveDrive))
    print('JOB NAME: "{}"'.format(self.JobName))

  def report(self):
    if len(self.dirList) > 0:
      print("Created {} Directories:".format(len(self.dirList)))
      for d in self.dirList:
        print(d)
    print("{} Files, Total MB: {}".format(self.nFiles,self.nBytes/(1024*1024)))
    if self.nSkipped:
      print("Skipped {} files".format(self.nSkipped))
    endTime = time.clock()
    elapsed = endTime-self.startTime
    if elapsed > 100:
      print("{} minutes".format(elapsed/60))
    else:
      print("{} seconds".format(elapsed))
    throughput = self.nBytes/elapsed
    throughput /= (1024*1024)
    print("Estimated performance: %g Mb/sec".format(elapsed))
    if self.nConversions > 0:
      print("Including {} DNG conversions".format(self.nConversions))

# MAIN EXECUTION BITS ##############

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Import/Archive Pictures, Video, & Audio from removeable media')
  parser.add_argument('jobname',help='appended to date directory names')
  parser.add_argument('-u','--unify',help='Unify imports to a single directory (indexed TODAY)',action="store_true")
  parser.add_argument('-p','--prefix',help='include string in filename as prefix')
  parser.add_argument('-j','--jobpref',help='toggle to include jobname in prefix',action="store_true")
  parser.add_argument('-s','--source',help='Specify source removeable volume (otherwise will guess)')
  parser.add_argument('-a','--archive',help='specify source archive directory (otherwise will use std names)')
  try:
    pargs = parser.parse_args()
  except:
    # testing
    pargs = argparse.Namespace()
    pargs.jobname = 'test'
    pargs.prefix = 'T_'
    pargs.jobpref = None
    pargs.source = None
    pargs.archive = None
    pargs.unify = False
  #print(pargs)

  #print(pargs.jobname)
  # exit()

  Vols = Volumes()
  Vols.user_args(pargs)
  Vols.archive()

# /disks/Removable/Flash\ Reader/EOS_DIGITAL/DCIM/100EOS5D/
# /disks/Removable/MK1237GSX/DOORKNOB/Pix/

# on linux seek /media/kevin/pix15


