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
#       (Under windows, if there is no external they will be on "D:" and called "LocalPix" etc)
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
# http://www.photorant.com/
"""

versionString = "kbImport - 21jan2014 - (c)2014 K Bjorke"

import sys
import os
import shutil
import time
import re
import subprocess
import unittest

##############################################################
##### global variables and settings ##########################
##############################################################

# if gTest is True, create directories, but don't actually copy files (for testing).....
gTest = True
#if gForce is True, just copy always. Otherwise, don't overwrite existing archived files.
gForce = False


################


# where AVCHD wants various types of files

#########################################################################################
## FUNCTIONS START HERE #################################################################
#########################################################################################

def seek_named_dir(LookHere,DesiredName,Level=0,MaxLevels=6):
  "Look for a directory, which should have pix"
  if Level >= MaxLevels:
    print "seek_named_dir('%s','%s',%d,%d): too deep" % (LookHere,DesiredName,Level,MaxLevels)
    return None
  if not os.path.exists(LookHere):
    print 'seek_named_dir(%s) No such path' % (LookHere)
    return None
  try:
    allSubs = os.listdir(LookHere)
  except:
        print "seek_named_dir('%s','%s'): no luck" % (LookHere,DesiredName)
        return None
  for subdir in allSubs:
    fullpath = os.path.join(LookHere,subdir)
    if subdir == DesiredName:
      return fullpath
  for subdir in os.listdir(LookHere):
    fullpath = os.path.join(LookHere,subdir)
    if os.path.isdir(fullpath):
      sr = seek_named_dir(fullpath,DesiredName,Level+1,MaxLevels)
      if sr is not None:
        return sr
  return None

#####


#####################################################
## Find or Create Archive Destination Directories ###
#####################################################


def safe_mkdir(Dir):
  "check for existence, create as needed"
  if not os.path.exists(Dir):
    if gTest:
      print "Need to create dir %s **" % (Dir)
    else:
      print "** Creating dir %s **" % (Dir)
      os.mkdir(Dir)
  elif not os.path.isdir(Dir):
    print "path error: %s is not a directory!" % (finaldir)
    return None
    # return None
  return Dir

def year_subdir(SrcFileStat,ArchDir):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  safe_mkdir(result)
  return result

def month_subdir(SrcFileStat,ArchDir):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  safe_mkdir(result)
  return result

############


#############################################################
## Recurse Throufgh Source Directories, and Archive #########
#############################################################

patAvchd = re.compile('AVCHD')
patDotAvchd = re.compile('(.*).AVCHD')
patAvchdFiles = re.compile('\.(MTS|CPI|TDT|TID|MPL|BDM)')
patVidFiles = re.compile('\.(M4V|MP4|MOV|3GP)')
patJPG = re.compile('(.*)\.JPG')
patDNGsrc = re.compile('(.*)\.RW2') # might be more in the future....

  
#############################################################


def archive_dir_name(ArchDir,BaseName):
  "pick the name of a good dated archive dir"
  if not os.path.exists(ArchDir):
    print "Hey, master '%s' is vapor!" % (ArchDir)
    return None
  if not os.path.isdir(ArchDir):
    print "Hey, '%s' is not a directory!" % (ArchDir)
    return None
  arch = os.path.join(ArchDir,BaseName)
  if not os.path.exists(arch):
    return arch
  counter = 0
  while os.path.exists(arch):
    bn = "%s_%d" % (BaseName,counter)
    counter = counter + 1
    if counter > 20:
      return None
    arch = os.path.join(ArchDir,bn)
  return arch

# #

class Volumes(object):
  'object for import/archive environment'
  AVCHDTargets = {}
  AVCHDTargets["MTS"] = os.path.join("AVCHD","BDMV","STREAM")
  AVCHDTargets["CPI"] = os.path.join("AVCHD","BDMV","CLIPINF")
  AVCHDTargets["MPL"] = os.path.join("AVCHD","BDMV","PLAYLIST")
  AVCHDTargets["BDM"] = os.path.join("AVCHD","BDMV")
  AVCHDTargets["TDT"] = os.path.join("AVCHD","ACVHDTN")
  AVCHDTargets["TID"] = os.path.join("AVCHD","ACVHDTN")
  AVCHDTargets["JPG"] = os.path.join("AVCHD","CANONTHM")
  #
  def __init__(self):
    self.startTime = time.clock()
    if os.name == 'posix': # mac?
      vols = '/Volumes'
      self.RemovableMedia = [os.path.join(vols,a) for a in os.listdir(vols) if os.path.isdir(os.path.join(vols,a)) and a != 'Macintosh HD']
      self.PrimaryArchiveList = [os.path.join(os.environ['HOME'],'Google Drive','kbImport')]
      self.LocalArchiveList = [os.path.join(os.environ['HOME'],'Pictures','kbImport')]
    elif os.name != "nt":
      print "Sorry no code for OS '%s' yet!" % (os.name)
      self.RemovableMedia = []
      self.PrimaryArchiveList = []
      self.LocalArchiveList = []
    else:
      self.RemovableMedia = ['I:', 'H:', 'K:','J:','G:', 'F:']
      self.PrimaryArchiveList = ['R:', 'G:', 'G:']
      self.LocalArchiveList = ['D:']
    self.JobName = None
    self.nBytes = 0L
    self.nFiles = 0L
    self.nConversions = 0
    self.audioPrefix = "" # for edirol
    self.createdDirs = {}
    self.dirList = []
  #
  def archive(self):
    if self.ready():
      print versionString
      self.announce()
      self.archive_images_and_video()
      self.archive_audio()
      self.report()
  #
  def ready(self):
    if not self.find_archive_drive():
      return False
    if not self.verify_archive_dest():
      return False
    self.find_src_media()
    if self.srcMedia is None:
      print "WARNING: No original source media found"
      print "\tPlease connect a card, phone, etc."
      return False
    self.seek_dng_convertor()
    return True
  #
  def find_archive_drive(self):
    # look for Drobo first
    for arch in self.PrimaryArchiveList:
      if os.path.exists(arch):
          self.archiveDrive = arch
          if arch[-1] == ':':       # windows
            arch = arch+os.path.sep
          self.pixDestDir = os.path.join(arch,"Pix")
          self.vidDestDir = os.path.join(arch,"Vid")
          self.audioDestDir = os.path.join(arch,"Audio")
          return True
    # nothing found?
    print "Primary archive disk unavailable"
    for arch in self.LocalArchiveList:
      if os.path.exists(arch):
        self.archiveDrive = arch
        if arch[-1] == ':':
          arch = arch+os.path.sep
        print "Using local drive %s instead" % (arch)
        self.pixDestDir = os.path.join(arch,"LocalPix")
        self.vidDestDir = os.path.join(arch,"LocalVid")
        sef.audioDestDir = os.path.join(arch,"LocalAudio")
        return True
    print "Something is broken? No primary or local archive dirs!"
    return False
  def verify_archive_dest(self):
    for d in [self.pixDestDir, self.vidDestDir, self.audioDestDir]: # delay this test?
      if not os.path.exists(d):
        print "Something is broken? No archive dir %s" % (d)
        return False
    return True
  #
  def find_src_media(self):
    self.srcMedia = None
    self.foundImages = False
    self.isPhone = False
    self.imgDirs = []
    for srcDisk in self.RemovableMedia:
      print srcDisk
      if self.archiveDrive == srcDisk:
        continue
      if os.path.exists(srcDisk):
        self.srcMedia = srcDisk
        avDir = seek_named_dir(srcDisk,"DCIM")
        if avDir is not None:
          self.imgDirs.append(avDir)
          self.foundImages = True
        avDir = seek_named_dir(srcDisk,".android_secure")
        if avDir is not None:
          self.isPhone = True
          print "Android Phone Storage Identified"
        else:
          # not a phone, so look for AVCHD stuff
          avDir = seek_named_dir(srcDisk,"PRIVATE")
          if avDir is not None:
            self.imgDirs.append(avDir)
            self.foundImages = True
          else:
            avDir = seek_named_dir(srcDisk,"AVCHD")
            if avDir is not None:
              self.imgDirs.append(avDir)
              self.foundImages = True
        if self.foundImages or self.isPhone:
            break
    if self.foundImages:
      # PIX and VIDEO #########################################
      # new hack to accomodate android phone that may have multiple dirs....
      print "looking for extra image dirs on drive '%s'" % (self.srcMedia)
      for aTest in ["AndCam3D", "AndroPan", "CamScanner", "ReducePhotoSize", "retroCamera",
              "FxCamera", "PicSay", "magicdoodle", "magicdoodlelite", "penman", 
              "Video", "Vignette", "SketchBookMobile", "sketcher"]:
        nDir = seek_named_dir(self.srcMedia,aTest)
        if nDir is not None:
          self.imgDirs.append(nDir)
          self.isPhone = True
    return self.srcMedia
  def seek_dng_convertor(self):
    self.hasDNGConv = False
    # DNGscript = None
    self.DNG = ""
    if os.environ.has_key('PROGRAMFILES'):
      self.DNG = os.path.join(os.environ['PROGRAMFILES'],"Adobe","Adobe DNG Converter.exe")
      if not os.path.exists(DNG):
              self.DNG = os.path.join(os.environ['PROGRAMFILES(X86)'],"Adobe","Adobe DNG Converter.exe")
      if os.path.exists(DNG):
            print "%s exists" % (DNG)
            self.hasDNGConv = True
          # DNGscript = open("DNG.bat","w")
  def mkArchiveDir(self,Location):
    "possibly create a directory"
    if not self.createdDirs.has_key(Location):
      if not os.path.exists(Location):
        self.createdDirs[Location] = 1
        self.dirList.append(Location)
        safe_mkdir(result)
  def dest_dir_name(self,SrcFile,ArchDir):
    "seek or create an archive directory based on the src file's origination date"
    s = os.stat(SrcFile)
    rootDir = year_subdir(s,ArchDir)
    rootDir = month_subdir(s,rootDir)
    timeFormat = "%Y_%m_%d"
    subdir = time.strftime(timeFormat,time.localtime(s.st_mtime))
    if self.JobName is not None:
      subdir = "%s_%s" % (subdir,self.JobName)
    finaldir = os.path.join(rootDir,subdir)
    # should make sure it exists!
    safe_mkdir(finaldir)
    if not os.path.isdir(finaldir):
      print "path error: %s is not a directory!" % (finaldir)
      return None
    return finaldir
  def announce(self):
    print 'SOURCE MEDIA: "%s"' % (self.srcMedia)
    print 'DESTINATION DRIVE: "%s"' % (self.archiveDrive)
    print 'JOB NAME: "%s"' % (self.JobName)
  def archive_images_and_video(self):
    if not self.foundImages:
      return
    print "Found These valid image source directories:"
    print "  %s" % (", ".join(self.imgDirs))
    for srcDir in self.imgDirs:
      print "Archiving Images from '%s'\n\tto '%s'" % (srcDir,self.pixDestDir)
      self.archive_pix(srcDir,self.pixDestDir,self.vidDestDir)
  def archive_audio(self):
    print "Archiving Audio from '%s'\n\tto '%s'" % (self.srcMedia,self.audioDestDir)
    # self.archive_audio_tracks(srcMedia,audioDestDir) ## HACKKKK
  def archive_audio_tracks(self,FromDir,ArchDir):
    "Archive audio tracks"
    # first validate our inputs
    if self.audioPrefix != "":
      print "NEED     Filenames %sXXXX.MP3 etc" % (self.audioPrefix)
    if not os.path.exists(ArchDir):
      print "Hey, destination archive '%s' is vapor!" % (ArchDir)
      return
    if not os.path.isdir(ArchDir):
      print "Hey, audio destination '%s' is not a directory!" % (ArchDir)
      return
    if not os.path.exists(FromDir):
      print "Hey, track source '%s' is vapor!" % (FromDir)
      return
    if not os.path.isdir(FromDir):
      print "Hey, track source '%s' is not a directory!" % (FromDir)
      return
    # okay to proceed
    for kid in os.listdir(FromDir):
      fullpath = os.path.join(FromDir,kid)
      if os.path.isdir(fullpath):
        self.archive_audio_tracks(fullpath,ArchDir)
      else:
        fp2 = fullpath.upper()
        if fp2.endswith("MP3") or fp2.endswith("WAV"):
          # print "%s..." % (kid)
          trackDir = dest_dir_name(fullpath,ArchDir)
          if trackDir:
            print "%s -> %s" % (kid,trackDir) 
            # INSERT CODE FOR RENAMING HERE
            s = os.stat(fullpath)
            self.nBytes += s.st_size
            self.nFiles += 1
            if not gTest:
                shutil.copy2(fullpath,trackDir)
          else:
            print "Unable to archive audio to %s" % (ArchDir)
        else:
          print "Skipping %s" % (fullpath)
  def verify_image_archive_dir(self,FromDir,PixArchDir,VidArchDir):
    if not os.path.exists(PixArchDir):
      print "Hey, image archive '%s' is vapor!" % (PixArchDir)
      return False
    if not os.path.isdir(PixArchDir):
      print "Hey, image destination '%s' is not a directory!" % (PixArchDir)
      return False
    if VidArchDir is not None and not os.path.exists(VidArchDir):
      print "Caution: Video archive '%s' is vapor, Ignoring it." % (VidArchDir)
      VidArchDir = None
    if not os.path.exists(FromDir):
      print "Hey, image source '%s' is vapor!" % (FromDir)
      return False
    if not os.path.isdir(FromDir):
      print "Hey, image source '%s' is not a directory!" % (FromDir)
      return False
    return True
  def archive_pix(self,FromDir,PixArchDir,VidArchDir):
    "Archive images and video"
    # first make sure all inputs are valid
    if not self.verify_image_archive_dir(FromDir,PixArchDir,VidArchDir):
      return
    # now we can proceed
    isAVCHDsrc = False
    m = patAvchd.search(FromDir)
    if m:
      isAVCHDsrc = True
    files = os.listdir(FromDir)
    files.sort()
    for kid in files:
      fullKidPath = os.path.join(FromDir,kid)
      if os.path.isdir(fullKidPath):
        self.archive_pix(fullKidPath,PixArchDir,VidArchDir)
      else:
        # if .MOV or .M4V or .MP4 or .3GP it's a vid
        # if JPG, check to see if there's a matching vid
        isSimpleVideo = False
        isDNGible = False
        isAVCHD = False
        avchdType = "JPG"
        kUp = kid.upper()
        destName = kid
        m = patAvchdFiles.search(kUp)
        if (m):
          isAVCHD = True
          avchdType = m.group(1)
        m = patVidFiles.search(kUp)
        if (m):
          isSimpleVideo = True
        m = patDNGsrc.search(kUp)
        if m:
          if Vols.hasDNGConv:
            isDNGible = True
            destName = "%s.DNG" % m.groups(0)[0]
        m = patJPG.search(kUp)
        if m:
          # keep an eye open for special thumbnail JPGs....
          if isAVCHDsrc:
            isAVCHD = True
            avchdType = "JPG"
          else:
            root = m.groups(0)[0]
            for suf in ['M4V', 'MOV', 'MP4', '3GP']:
              vidName = "%s.%s" % (root,suf)
              if files.__contains__(vidName):
                # print "List contains both %s and %s" % (kid,vidName)
                isSimpleVideo = True # send the thumbnail to the video directory too
        if isAVCHD:
          avchdPath = self.dest_avchd_dir_name(fullKidPath,VidArchDir)
          if avchdPath is None:
            destinationPath = None
          else:
            destinationPath = os.path.join(avchdPath,Volumes.AVCHDTargets[avchdType])
        elif isSimpleVideo:
          destinationPath = self.dest_dir_name(fullKidPath,VidArchDir)
        else:
          destinationPath = self.dest_dir_name(fullKidPath,PixArchDir)
        if destinationPath:
          self.archive_image(kid,fullKidPath,kidTargetPath,destinationPath,destName)
        else:
          print "Unable to archive media to %s" % (destinationPath)
    return
  def dest_avchd_dir_name(self,SrcFile,ArchDir):
    """
    AVCHD has a complex format, let's keep it intact so clips can be archived to blu-ray etc.
    We will say that the dated directory is equivalent to the "PRIVATE" directory in the spec.
    We don't handle the DCIM and MISC dirs.
    """
    privateDir = self.dest_dir_name(SrcFile,ArchDir)
    if privateDir is None:
      print "avchd error"
      return privateDir
    avchdDir = safe_mkdir(os.path.join(privateDir,"AVCHD"))
    avchdtnDir = safe_mkdir(os.path.join(avchdDir,"AVCHDTN"))
    bdmvDir = safe_mkdir(os.path.join(avchdDir,"BDMV"))
    streamDir = safe_mkdir(os.path.join(bdmvDir,"STREAM"))
    clipinfDir = safe_mkdir(os.path.join(bdmvDir,"CLIPINF"))
    playlistDir = safe_mkdir(os.path.join(bdmvDir,"PLAYLIST"))
    backupDir = safe_mkdir(os.path.join(bdmvDir,"BACKUP"))
    canonthmDir = safe_mkdir(os.path.join(avchdDir,"CANONTHM"))
    # should make sure it exists!
    return privateDir
  def archive_image(self,SrcName,FullSrcPath,DestDir,DestName):
    FullDestPath = os.path.join(DestDir,DestName)
    s = os.stat(FullSrcPath)
    protected = gTest
    destinationPath = DestDir
    #
    # wanted: better checking here
    #
    if os.path.exists(destinationPath):
      if gForce:
        print "overwriting %s" % (FullDestPath) 
        self.nBytes += s.st_size
        self.nFiles += 1
      else:
        protected = True
        m = patDotAvchd.search(destinationPath)
        if m:
          destinationPath = m.group(1)
          destinationPath = os.path.join(destinationPath,"...",SrcName)
        # print "%s already exists" % (destinationPath) 
    else:
      print "%s -> %s" % (SrcName,FullDestPath) 
      self.nBytes += s.st_size
      self.nFiles += 1
    if not protected:
      if isDNGible:
        self.dng_convert(destinationPath,destName,FullSrcPath)
      else:
        self.safe_copy(FullSrcPath,destinationPath)
  #
  def safe_copy(self,FullSrcPath,DestPath):
    if gTest:
      print "Fake Copy %s -> %s" % (FullSrcPath,DestPath)
      return
    shutil.copy2(FullSrcPath,DestPath)
  #
  def dng_convert(self,DestPath,DestName,FullSrcPath):
    cmd = "\"%s\" -c -d \"%s\" -o %s \"%s\"" % (self.DNG,DestPath,DestName,FullSrcPath)
    # print cmd
    if gTest:
      print cmd
      return
    p = os.popen4(r'cmd /k')
    p[0].write('%s\r\n'%cmd)
    p[0].flush()
    p[0].write('exit\r\n')
    p[0].flush()
    print ''.join(p[1].readlines())
    self.nConversions += 1
    # DNGscript.write("%s\n"%(cmd))
    # ret = subprocess.call(cmd)
    # print "ret was %d" % (ret)
  def report(self):
    if len(self.dirList) > 0:
      print "Created %d Directories:" % (len(self.dirList))
      for d in self.dirList:
        print d
    print "%d Files, Total MB: %d" % (self.nFiles,self.nBytes/(1024*1024))
    endTime = time.clock()
    elapsed = endTime-self.startTime
    if elapsed > 100:
      print "%d minutes" % (elapsed/60)
    else:
      print "%d seconds" % (elapsed)
    throughput = self.nBytes/elapsed
    throughput /= (1024*1024)
    print "Estimated performance: %g Mb/sec" % (elapsed)
    if self.nConversions > 0:
      print "Including %d DNG conversions" % (self.nConversions)



class VolTests(unittest.TestCase):
  def setUp(self):
    self.v = Volumes()
  #def test_hasRemoveable(self):
  #  self.assertTrue(len(Vols.RemovableMedia) > 0)
  def test_hasPrimary(self):
    self.assertTrue(len(self.v.PrimaryArchiveList) > 0)
  def test_hasRLocal(self):
    self.assertTrue(len(self.v.LocalArchiveList) > 0)
  #def test_soughtDNG(self):
  #  self.assertTrue(Vols.DNG is not None)

if len(sys.argv) <= 1:
  print "Usage: python kbImport3.py JobName [Removeable] [ArchiveDir]"
  print "No arguments: Running unittests"
  unittest.main()
  sys.exit()

Vols = Volumes()

Vols.JobName = sys.argv[1]
if len(sys.argv) > 2: # TO-DO fix this
  Vols.RemovableMedia = [ '%s:' % (sys.argv[2]) ]
  Vols.RemovableMedia[0] = re.sub('::',':',Vols.RemovableMedia[0])
if len(sys.argv) > 3: # TO-DO fix this
  Vols.PrimaryArchiveList = [ sys.argv[3] ]
  Vols.PrimaryArchiveList[0] = re.sub('::',':',Vols.PrimaryArchiveList[0])

Vols.archive()

# /disks/Removable/Flash\ Reader/EOS_DIGITAL/DCIM/100EOS5D/
# /disks/Removable/MK1237GSX/DOORKNOB/Pix/


