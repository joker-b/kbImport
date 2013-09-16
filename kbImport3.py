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

versionString = "kbImport - 28oct2012 - (c)2012 K Bjorke"

import sys
import os
import shutil
import time
import re
import subprocess

##############################################################
##### global variables and settings ##########################
##############################################################

# if gTest is True, create directories, but don't actually copy files (for testing).....
gTest = False
#if gForce is True, just copy always. Otherwise, don't overwrite existing archived files.
gForce = False

# my windows archive drives 
RemovableMedia = ['I:', 'H:', 'K:','J:','G:', 'F:']
PrimaryArchiveList = ['R:', 'G:', 'G:']
LocalArchiveList = ['D:']

# temp: disk weirdness
# RemovableMedia = ['K:','J:','I:','H:']

PhotoJobName = None
if len(sys.argv) > 1:
    PhotoJobName = sys.argv[1]
if len(sys.argv) > 2:
    RemoveableMedia = [ '%s:' % (sys.argv[2]) ]
    RemoveableMedia[0] = re.sub('::',':',RemoveableMedia[0])
if len(sys.argv) > 2:
    PrimaryArchiveList = [ sys.argv[3] ]
    PrimaryArchiveList[0] = re.sub('::',':',PrimaryArchiveList[0])

hasDNGConv = False
# DNGscript = None
DNG = ""
global nConversions
nConversions = 0
if os.environ.has_key('PROGRAMFILES'):
  DNG = os.path.join(os.environ['PROGRAMFILES'],"Adobe","Adobe DNG Converter.exe")
  if not os.path.exists(DNG):
          DNG = os.path.join(os.environ['PROGRAMFILES(X86)'],"Adobe","Adobe DNG Converter.exe")
  if os.path.exists(DNG):
        print "%s exists" % (DNG)
        hasDNGConv = True
        # DNGscript = open("DNG.bat","w")

################
global gCreatedDirs
global gDirList
gCreatedDirs = {}
gDirList = []

global gBytes
gBytes = 0L
global gNFiles
gNFiles = 0

# currently I want "" for my Edirol
audioPrefix = ""

# where AVCHD wants various types of files
global gAVCHDTargets
gAVCHDTargets = {}
gAVCHDTargets["MTS"] = os.path.join("AVCHD","BDMV","STREAM")
gAVCHDTargets["CPI"] = os.path.join("AVCHD","BDMV","CLIPINF")
gAVCHDTargets["MPL"] = os.path.join("AVCHD","BDMV","PLAYLIST")
gAVCHDTargets["BDM"] = os.path.join("AVCHD","BDMV")
gAVCHDTargets["TDT"] = os.path.join("AVCHD","ACVHDTN")
gAVCHDTargets["TID"] = os.path.join("AVCHD","ACVHDTN")
gAVCHDTargets["JPG"] = os.path.join("AVCHD","CANONTHM")

#########################################################################################
## FUNCTIONS START HERE #################################################################
#########################################################################################

def mkArchiveDir(Location):
  "possibly create a directory"
  global gCreatedDirs
  global gDirList
  if not gCreatedDirs.has_key(Location):
    if not os.path.exists(Location):
      gCreatedDirs[Location] = 1
      gDirList.append(Location)
      if gTest:
        print "** Need to create dir %s **" % (Location)
      else:
        print "** Creating dir %s **" % (Location)
        os.mkdir(result)

#####################################################
## Find or Create Archive Destination Directories ###
#####################################################

def year_subdir(SrcFileStat,ArchDir):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  if not os.path.exists(result):
    print "** Creating dir %s **" % (result)
    os.mkdir(result)
  return result

def month_subdir(SrcFileStat,ArchDir):
  "Based on the source file's timestamp, seek (or create) an archive directory"
  # subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_ctime))
  subdir = time.strftime("%Y-%m-%b",time.localtime(SrcFileStat.st_mtime))
  result = os.path.join(ArchDir,subdir)
  if not os.path.exists(result):
    print "** Creating dir %s **" % (result)
    os.mkdir(result)
  return result

def dest_dir_name(SrcFile,ArchDir):
  "seek or create an archive directory based on the src file's origination date"
  s = os.stat(SrcFile)
  rootDir = year_subdir(s,ArchDir)
  rootDir = month_subdir(s,rootDir)
  timeFormat = "%Y_%m_%d"
  subdir = time.strftime(timeFormat,time.localtime(s.st_mtime))
  if PhotoJobName is not None:
    subdir = "%s_%s" % (subdir,PhotoJobName)
  finaldir = os.path.join(rootDir,subdir)
  # should make sure it exists!
  if not os.path.exists(finaldir):
    print "** Creating dir %s **" % (finaldir)
    os.mkdir(finaldir)
  if not os.path.isdir(finaldir):
        print "path error: %s is not a directory!" % (finaldir)
        sys.exit(-4)
  return finaldir

############

def safe_mkdir(Dir):
  "check for existence, create as needed"
  if not os.path.exists(Dir):
    print "** Creating dir %s **" % (Dir)
    os.mkdir(Dir)
  if not os.path.isdir(Dir):
    print "path error: %s is not a directory!" % (finaldir)
    sys.exit(-4)
    # return None
  return Dir

def dest_avchd_dir_name(SrcFile,ArchDir):
  """
  AVCHD has a complex format, let's keep it intact so clips can be archived to blu-ray etc.
  We will say that the dated directory is equivalent to the "PRIVATE" directory in the spec.
  We don't handle the DCIM and MISC dirs.
  """
  privateDir = dest_dir_name(SrcFile,ArchDir)
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

#############################################################
## Recurse Throufgh Source Directories, and Archive #########
#############################################################

patAvchd = re.compile('AVCHD')
patDotAvchd = re.compile('(.*).AVCHD')
patAvchdFiles = re.compile('\.(MTS|CPI|TDT|TID|MPL|BDM)')
patVidFiles = re.compile('\.(M4V|MP4|MOV|3GP)')
patJPG = re.compile('(.*)\.JPG')
patDNGsrc = re.compile('(.*)\.RW2') # might be more in the future....

def archive_pix(FromDir,PixArchDir,VidArchDir):
  "Archive images and video"
  global gAVCHDTargets
  global gBytes
  global gNFiles
  global nConversions
  # first make sure all inputs are valid
  if not os.path.exists(PixArchDir):
    print "Hey, image archive '%s' is vapor!" % (PixArchDir)
    return None
  if not os.path.isdir(PixArchDir):
    print "Hey, image destination '%s' is not a directory!" % (PixArchDir)
    return None
  if VidArchDir is not None and not os.path.exists(VidArchDir):
    print "Caution: Video archive '%s' is vapor, Ignoring it." % (VidArchDir)
    VidArchDir = None
  if not os.path.exists(FromDir):
    print "Hey, image source '%s' is vapor!" % (FromDir)
    return None
  if not os.path.isdir(FromDir):
    print "Hey, image source '%s' is not a directory!" % (FromDir)
    return None
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
      archive_pix(fullKidPath,PixArchDir,VidArchDir)
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
        if hasDNGConv:
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
        avchdPath = dest_avchd_dir_name(fullKidPath,VidArchDir)
        destinationPath = os.path.join(avchdPath,gAVCHDTargets[avchdType])
      elif isSimpleVideo:
        destinationPath = dest_dir_name(fullKidPath,VidArchDir)
      else:
        destinationPath = dest_dir_name(fullKidPath,PixArchDir)
      kidTargetPath = os.path.join(destinationPath,destName)
      s = os.stat(fullKidPath)
      protected = gTest
      #
      # wanted: better checking here
      #
      if os.path.exists(kidTargetPath):
        if gForce:
          print "overwriting %s" % (kidTargetPath) 
          gBytes += s.st_size
          gNFiles += 1
        else:
          protected = True
          m = patDotAvchd.search(destinationPath)
          if m:
            destinationPath = m.group(1)
            destinationPath = os.path.join(destinationPath,"...",kid)
          # print "%s already exists" % (destinationPath) 
      else:
        print "%s -> %s" % (kid,kidTargetPath) 
        gBytes += s.st_size
        gNFiles += 1
      if not protected:
        if isDNGible:
          # cmd = "\"%s\" -c -d \"%s\" \"%s\"" % (DNG,destinationPath,fullKidPath)
          cmd = "\"%s\" -c -d \"%s\" -o %s \"%s\"" % (DNG,destinationPath,destName,fullKidPath)
          # print cmd
          p = os.popen4(r'cmd /k')
          p[0].write('%s\r\n'%cmd)
          p[0].flush()
          p[0].write('exit\r\n')
          p[0].flush()
          print ''.join(p[1].readlines())
          nConversions += 1
          # DNGscript.write("%s\n"%(cmd))
          # ret = subprocess.call(cmd)
          # print "ret was %d" % (ret)
        else:
          shutil.copy2(fullKidPath,destinationPath)

#############################################################

def archive_audio_tracks(FromDir,ArchDir):
  "Archive audio tracks"
  global gBytes
  global gNFiles
  # first validate our inputs
  if audioPrefix != "":
    print "NEED     Filenames %sXXXX.MP3 etc" % (audioPrefix)
  if not os.path.exists(ArchDir):
    print "Hey, destination archive '%s' is vapor!" % (ArchDir)
    return None
  if not os.path.isdir(ArchDir):
    print "Hey, audio destination '%s' is not a directory!" % (ArchDir)
    return None
  if not os.path.exists(FromDir):
    print "Hey, track source '%s' is vapor!" % (FromDir)
    return None
  if not os.path.isdir(FromDir):
    print "Hey, track source '%s' is not a directory!" % (FromDir)
    return None
  # okay to proceed
  for kid in os.listdir(FromDir):
    fullpath = os.path.join(FromDir,kid)
    if os.path.isdir(fullpath):
      archive_audio_tracks(fullpath,ArchDir)
    else:
      fp2 = fullpath.upper()
      if fp2.endswith("MP3") or fp2.endswith("WAV"):
        # print "%s..." % (kid)
        trackDir = dest_dir_name(fullpath,ArchDir)
        print "%s -> %s" % (kid,trackDir) 
        # INSERT CODE FOR RENAMING HERE
        s = os.stat(fullpath)
        gBytes += s.st_size
        gNFiles += 1
        if not gTest:
            shutil.copy2(fullpath,trackDir)
      else:
        print "Skipping %s" % (fullpath)

# #

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

#########################################################################################
## MAIN EXECUTION BEGINS HERE ###########################################################
#########################################################################################

# SEEK SOURCE AND DEST DIRS ##

startTime = time.clock()

print versionString

if os.name != "nt":
  print "Sorry no code for OS '%s' yet!" % (os.name)
  exit()

# select archive destination locations ###############

archiveDrive = None
# look for Drobo first
for PrimaryArchive in PrimaryArchiveList:
    if os.path.exists(PrimaryArchive):
        break

archiveDrive = PrimaryArchive+os.path.sep
pixDestDir = os.path.join(archiveDrive,"Pix")
vidDestDir = os.path.join(archiveDrive,"Vid")
audioDestDir = os.path.join(archiveDrive,"Audio")

if not os.path.exists(archiveDrive):
    print "Primary archive disk unavailable"
    for LocalArchive in LocalArchiveList:
        if os.path.exists(LocalArchive):
            break
    if not os.path.exists(LocalArchive):
          print "Something is broken? No primary or local archive dirs!"
          exit()
    archiveDrive = LocalArchive+os.path.sep
    print "Using local drive %s instead" % (LocalArchive)
    pixDestDir = os.path.join(archiveDrive,"LocalPix")
    vidDestDir = os.path.join(archiveDrive,"LocalVid")
    audioDestDir = os.path.join(archiveDrive,"LocalAudio")

if not os.path.exists(pixDestDir):
  print "Something is broken? No archive dir %s" % (pixDestDir)
  exit()

# check for valid source media ###############

imgDirs = []
foundImages = False
isPhone = False
srcMedia = None
for srcDisk in RemovableMedia:
  if archiveDrive == srcDisk+os.path.sep:
    continue
  if os.path.exists(srcDisk):
    srcMedia = srcDisk
    avDir = seek_named_dir(srcDisk,"DCIM")
    if avDir is not None:
      imgDirs.append(avDir)
      foundImages = True
    avDir = seek_named_dir(srcDisk,".android_secure")
    if avDir is not None:
      isPhone = True
      print "Android Phone Storage Identified"
    else:
      # not a phone, so look for AVCHD stuff
      avDir = seek_named_dir(srcDisk,"PRIVATE")
      if avDir is not None:
        imgDirs.append(avDir)
        foundImages = True
      else:
        avDir = seek_named_dir(srcDisk,"AVCHD")
        if avDir is not None:
          imgDirs.append(avDir)
          foundImages = True
    if foundImages or isPhone:
        break

if srcMedia is None:
  print "WARNING: No original source media found"
  print "\tPlease connect a card, phone, etc."
  sys.exit(-3)

print 'SOURCE MEDIA: "%s"' % (srcMedia)

print 'DESTINATION DRIVE: "%s"' % (archiveDrive)
if PhotoJobName is not None:
  print 'PHOTO JOB NAME: "%s"' % (PhotoJobName)

if foundImages:
  # PIX and VIDEO #########################################
  # new hack to accomodate android phone that may have multiple dirs....
  print "looking for extra image dirs on drive '%s'" % (srcMedia)
  for aTest in ["AndCam3D","AndroPan","CamScanner","ReducePhotoSize","retroCamera",\
          "FxCamera","PicSay","magicdoodle","magicdoodlelite","penman", \
          "Video", "Vignette", "SketchBookMobile","sketcher"]:
    nDir = seek_named_dir(srcMedia,aTest)
    if nDir is not None:
      imgDirs.append(nDir)
      isPhone = True
  print "Found These valid source directories:"
  print "  %s" % (", ".join(imgDirs))
  for srcDir in imgDirs:
    print "Archiving Images from '%s'\n\tto '%s'" % (srcDir,pixDestDir)
    archive_pix(srcDir,pixDestDir,vidDestDir)

print "Archiving Audio from '%s'\n\tto '%s'" % (srcMedia,audioDestDir)
# archive_audio_tracks(srcMedia,audioDestDir) ## HACKKKK

######## end report ######################

if len(gDirList) > 0:
  print "Created %d Directories:" % (len(gDirList))
  for d in gDirList:
    print d

print "%d Files, Total MB: %d" % (gNFiles,gBytes/(1024*1024))

endTime = time.clock()
elapsed = endTime-startTime
if elapsed > 100:
  print "%d minutes" % (elapsed/60)
else:
  print "%d seconds" % (elapsed)

throughput = gBytes/elapsed
throughput /= (1024*1024)
print "Estimated performance: %g Mb/sec" % (elapsed)
if nConversions > 0:
  print "Including %d DNG conversions" % (nConversions)

# if hasDNGConv:
#   DNGscript.close()

# /disks/Removable/Flash\ Reader/EOS_DIGITAL/DCIM/100EOS5D/
# /disks/Removable/MK1237GSX/DOORKNOB/Pix/
