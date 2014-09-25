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

# TO-DO -- ignore list eg ['.dropbox.device']
# TO-DO - itemized manifest @ end ("# of pix to dir xxxx" etc)

versionString = "kbImport - 26jul2014 - (c)2014 K Bjorke"

import sys
import os
import shutil
import time
import re
import subprocess
import argparse
import unittest

##############################################################
##### global variables and settings ##########################
##############################################################

# if gTest is True, create directories, but don't actually copy files (for testing).....
gTest = False
#if gForce is True, just copy always. Otherwise, don't overwrite existing archived files.
gForce = False

#########################################################################################
## FUNCTIONS START HERE #################################################################
#########################################################################################

def seek_named_dir(LookHere,DesiredName,Level=0,MaxLevels=6):
  "Look for a directory, which should have pix"
  if Level >= MaxLevels:
    # print "seek_named_dir('%s','%s',%d,%d): too deep" % (LookHere,DesiredName,Level,MaxLevels)
    return None
  if not os.path.exists(LookHere):
    print 'seek_named_dir(%s) No such path' % (LookHere)
    return None
  try:
    allSubs = os.listdir(LookHere)
  except:
    print "seek_named_dir('%s','%s'):\n\tno luck, '%s'" % (LookHere,DesiredName,sys.exc_info()[0])
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

#####################################################
## Find or Create Archive Destination Directories ###
#####################################################


def safe_mkdir(Dir,ReportName=None):
  "check for existence, create as needed"
  report = Dir
  if ReportName:
  	report = ReportName
  if not os.path.exists(Dir):
    if gTest:
      print "Need to create dir %s **" % (report)
    else:
      print "** Creating dir %s **" % (report)
      os.mkdir(Dir)
  elif not os.path.isdir(Dir):
    print "path error: %s is not a directory!" % (finaldir)
    return None
    # return None
  return Dir

######

def year_subdir(SrcFileStat,ArchDir,ReportName=""):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  report = ReportName+"/"+subdir
  safe_mkdir(result,report)
  return result

#########

def month_subdir(SrcFileStat,ArchDir,ReportName=""):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  report = ReportName+"/"+subdir
  safe_mkdir(result,report)
  return result

#############################################################
#############################################################
#############################################################

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
  patAvchd = re.compile('AVCHD')
  patDotAvchd = re.compile('(.*).AVCHD')
  patAvchdFiles = re.compile('\.(MTS|CPI|TDT|TID|MPL|BDM)')
  patVidFiles = re.compile('\.(M4V|MP4|MOV|3GP)')
  patJPG = re.compile('(.*)\.JPG')
  patDNGsrc = re.compile('(.*)\.RW2') # might be more in the future....
  largestSource = 100 * 1024*1024*1024 # in GB - hack to not scan hard drives as source media
  #
  def __init__(self):
    self.startTime = time.clock()
    if os.name == 'posix': # mac?
      self.RemovableMedia = self.available_source_vols([os.path.join('/Volumes',a) for a in os.listdir('/Volumes')])
      self.PrimaryArchiveList = [os.path.join(os.environ['HOME'],'Google Drive','kbImport')]
      self.LocalArchiveList = [os.path.join(os.environ['HOME'],'Pictures','kbImport')]
    elif os.name != "nt":
      print "Sorry no code for OS '%s' yet!" % (os.name)
      self.RemovableMedia = []
      self.PrimaryArchiveList = []
      self.LocalArchiveList = []
    else:
      self.RemovableMedia = self.available_source_vols(['J:', 'I:', 'H:', 'K:','G:', 'F:'])
      self.PrimaryArchiveList = ['R:', 'G:', 'G:']
      self.LocalArchiveList = ['D:']
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
    #
  def user_args(self,pargs):
    self.JobName = pargs.jobname
    if pargs.source is not None: # TO-DO fix this windows-centric oddness
      self.RemovableMedia = [ '%s:' % (pargs.source) ]
      self.RemovableMedia[0] = re.sub('::',':',self.RemovableMedia[0])
    if pargs.archive is not None: # TO-DO fix this
      self.PrimaryArchiveList = pargs.archive
      self.PrimaryArchiveList[0] = re.sub('::',self.PrimaryArchiveList[0])
    if pargs.unify is not None:
    	self.unify = True
    if pargs.prefix is not None:
    	print "can't yet add prefix"
    	self.prefix = "%s_"%(pargs.prefix)

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
    if not self.verify_archive_subdirs():
      return False
    self.srcMedia = self.find_src_media()
    if self.srcMedia is None:
      print "WARNING: No original source media found"
      print "\tPlease connect a card, phone, etc."
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
    print "Primary archive disk unavailable"
    return False
  def find_local_archive_drive(self):
    "find 'backup' destination"
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
    print "Unable to find a local archive location"
    return False
  def find_archive_drive(self):
    "find an archive destination"
    if self.find_primary_archive_drive():
      return True
    return self.find_local_archive_drive()
  def verify_archive_subdirs(self):
    "double-check existence of the archive directories"
    for d in [self.pixDestDir, self.vidDestDir, self.audioDestDir]: # TO-DO delay this test?
      if not os.path.exists(d):
        print "Something is broken? No archive dir %s" % (d)
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
      print 'Caution: "%s" is not a directory' %(Path)
      return False
    if Path == '/Volumes/Macintosh HD' or \
      Path == '/Volumes/MobileBackups' or \
      Path == '/Volumes/My Passport for Mac':
      return False
    s = os.path.getsize(Path) # TO-DO: this is not how you get volume size!
    if os.path.getsize(Path) > Volumes.largestSource:
      print 'Oversized source: "%s"' %(Path)
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
        print "Android Phone Storage Identified"
        return True
      return False
  def find_extra_android_image_dirs(self,srcMedia):
    found = False
    print "looking for extra Android image dirs on drive '%s'" % (srcMedia)
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
      print srcDisk
      if (self.archiveDrive == srcDisk) or (not os.path.exists(srcDisk)):
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
  	ysubdir = time.strftime("%Y",now)
  	yresult = os.path.join(ArchDir,ysubdir)
  	report = ReportName+"/"+ysubdir
  	safe_mkdir(yresult,report)
	msubdir = time.strftime("%Y-%m-%b",now)
	mresult = os.path.join(ArchDir,subdir)
	report = report+"/"+msubdir
	safe_mkdir(mresult,report)
	subdir = time.strftime("%Y_%m_%d",now)
	if self.JobName is not None:
		subdir = "%s_%s" % (subdir,self.JobName)
	finaldir = os.path.join(mresult,subdir)
	report = report+"/"+subdir
	safe_mkdir(finaldir,report)
	if not os.path.isdir(finaldir):
		print "path error: %s is not a directory!" % (finaldir)
		return None
	return finaldir

  def dest_dir_name(self,SrcFile,ArchDir,ReportName=""):
    "seek or create an archive directory based on the src file's origination date"
    if self.unify:
    	return self.unified_dir_name(ArchDir,ReportName)
    try:
      s = os.stat(SrcFile)
    except:
      print 'Stat failure: %s' % (sys.exc_info()[0])
      return None
    rootDir = year_subdir(s,ArchDir)
    rootDir = month_subdir(s,rootDir)
    timeFormat = "%Y_%m_%d"
    subdir = time.strftime(timeFormat,time.localtime(s.st_mtime))
    if self.JobName is not None:
      subdir = "%s_%s" % (subdir,self.JobName)
    finaldir = os.path.join(rootDir,subdir)
    # should make sure it exists!
    report = ReportName+"/"+subdir
    safe_mkdir(finaldir,report)
    if not os.path.isdir(finaldir):
      print "path error: %s is not a directory!" % (finaldir)
      return None
    return finaldir
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
  def avchd_src(self,FromDir):
    if Volumes.patAvchd.search(FromDir):
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
      print "avchd error"
      return privateDir
    avchdDir = safe_mkdir(os.path.join(privateDir,"AVCHD"),"AVCHD")
    for s in ["AVCHDTN","CANONTHM"]:
      sd = safe_mkdir(os.path.join(avchdDir,s),"AVCHD/%s"%(s))
    bdmvDir = safe_mkdir(os.path.join(avchdDir,"BDMV"),"BDMV")
    for s in ["STREAM","CLIPINF","PLAYLIST","BACKUP"]:
      sd = safe_mkdir(os.path.join(bdmvDir,s),"BDMV/%s"%(s))
    return privateDir
  def archive_pix(self,FromDir,PixArchDir,VidArchDir):
    "Archive images and video"
    # first make sure all inputs are valid
    if not self.verify_image_archive_dir(FromDir,PixArchDir,VidArchDir):
      return
    # now we can proceed
    isAVCHDsrc = self.avchd_src(FromDir)
    files = os.listdir(FromDir)
    files.sort()
    print "%d files in %s" % (len(files),FromDir)
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
        m = Volumes.patAvchdFiles.search(kUp)
        if (m):
          isAVCHD = True
          avchdType = m.group(1)
        isSimpleVideo = Volumes.patVidFiles.search(kUp) is not None
        m = Volumes.patDNGsrc.search(kUp)
        if m:
          if Vols.DNG:
            isDNGible = True
            destName = "%s.DNG" % m.groups(0)[0]
        m = Volumes.patJPG.search(kUp)
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
          if not self.archive_image(kid,fullKidPath,destinationPath,destName,isDNGible):
            self.nSkipped += 1
        else:
          print "Unable to archive media to %s" % (destinationPath)

  def incr(self,FullSrcPath):
    try:
      s = os.stat(FullSrcPath)
    except:
      print "archive_image() cannot stat source '%s'" % (FullSrcPath)
      print "Err %s" % (sys.exc_info()[0])
      return False
    self.nBytes += s.st_size
    self.nFiles += 1
    return True

  def archive_image(self,SrcName,FullSrcPath,DestDir,DestName,IsDNGible):
    if SrcName == '.dropbox.device': # TO-DO -- be more sophisticated here
      return False
    FullDestPath = os.path.join(DestDir,DestName)
    protected = gTest
    destinationPath = DestDir
    if os.path.exists(FullDestPath):
      if gForce:
        print "overwriting %s" % (FullDestPath)
        self.incr(FullSrcPath)
      else:
        protected = True
        m = Volumes.patDotAvchd.search(FullDestPath)
        if m:
          destinationPath = m.group(1)
          FullDestPath = os.path.join(destinationPath,"...",SrcName)
    else:
	    reportPath = '..' + FullDestPath[len(self.pixDestDir):]
	    print "%s -> %s" % (SrcName,reportPath)
	    self.incr(FullSrcPath)
    if not protected:
      if IsDNGible:
        return self.dng_convert(destinationPath,destName,FullSrcPath)
      else:
        return self.safe_copy(FullSrcPath,FullDestPath)
    return False
  #
  def safe_copy(self,FullSrcPath,DestPath):
    if gTest:
      return True # always "work"
    try:
      shutil.copy2(FullSrcPath,DestPath)
    except:
      print "Failed to copy, '%s'!!\n\t%s\n\t%s" % (sys.exc_info()[0],FullSrcPath,DestPath)
      return False
    return True
  #
  def dng_convert(self,DestPath,DestName,FullSrcPath):
    cmd = "\"%s\" -c -d \"%s\" -o %s \"%s\"" % (self.DNG,DestPath,DestName,FullSrcPath)
    # print cmd
    if gTest:
      print cmd
      return True # pretend
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
    return True
  #
  # reporting
  #
  def announce(self):
    print 'SOURCE MEDIA: "%s"' % (self.srcMedia)
    print 'DESTINATION DRIVE: "%s"' % (self.archiveDrive)
    print 'JOB NAME: "%s"' % (self.JobName)
  def report(self):
    if len(self.dirList) > 0:
      print "Created %d Directories:" % (len(self.dirList))
      for d in self.dirList:
        print d
    print "%d Files, Total MB: %d" % (self.nFiles,self.nBytes/(1024*1024))
    if self.nSkipped:
      print "Skipped %d files" % (self.nSkipped)
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

# UNIT TESTS ##############################

class VolTests(unittest.TestCase):
  def setUp(self):
    gTest = True # good idea?
    self.v = Volumes()
  def test_hasPrimary(self):
    self.assertTrue(len(self.v.PrimaryArchiveList) > 0)
  def test_hasRLocal(self):
    self.assertTrue(len(self.v.LocalArchiveList) > 0)
  def test_archive_loc(self):
    "obviously this test needs to be run on a machine with such a drive..."
    self.assertTrue(self.v.find_archive_drive())

# MAIN EXECUTION BITS ##############

if len(sys.argv)>1 and sys.argv[1]=='test': # this is hokey placement but argparse trashes unittest
	print "Running unit tests..."
	unittest.main()
	sys.exit()

parser = argparse.ArgumentParser(description='Import/Archive Pictures, Video, & Audio from removeable media')
parser.add_argument('jobname',help='appended to date directory names: jobname "test" to run unit tests')
# parser.add_argument('-t','--test',help='Run unit tests',nargs='?',const=1)
parser.add_argument('-u','--unify',help='Unify imports to a single directory (indexed TODAY)')
parser.add_argument('-p','--prefix',help='set imported file prefix, e.g. "bjorke"')
parser.add_argument('-s','--source',help='Specify source removeable volume (otherwise will guess)')
parser.add_argument('-a','--archive',help='specify source archive directory (otherwise will use std names)')
pargs = parser.parse_args()
print pargs

#print pargs.jobname
# exit()

Vols = Volumes()
Vols.user_args(pargs)
Vols.archive()

# /disks/Removable/Flash\ Reader/EOS_DIGITAL/DCIM/100EOS5D/
# /disks/Removable/MK1237GSX/DOORKNOB/Pix/


