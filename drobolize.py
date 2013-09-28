# /usr/bin/python

"""
# Usage:
#    sudo python drobolize.py
#
# to-do: compare size and data
# to-do: audio and video
# TO-DO: preview mode - which needs to keep a list of directories and file counts
# TO-DO: catch *similar* names/files....
#
# make sure localPix & the backup align
#
# Kevin Bjorke
# http://www.photorant.com/
"""

import sys
import os
import shutil
import time
import re

global active
global totalCopied
global createdDirs
global suffix

active = True
totalCopied = 0
createdDirs = {}
suffix = {}

pixDir = None
pixDisk = None
audioDir = None
audioDisk = None
dcimDir = None
dcimDisk = None

audioPrefix = ""

timeFormat = "%Y_%m_%d"

destdate = time.strftime(timeFormat)

###################

def new_dir(name):
  "if you can, make it. and save the name"
  global active
  global createdDirs
  if not os.path.exists(name):
	if createdDirs.has_key(name):
	  return
	createdDirs[name] = 1
	if (active):
	  print "** Creating dir %s **" % (name)
	  os.mkdir(name)
	else:
	  print "** Need to create dir %s **" % (name)

###################

def send_file(Indent,filename,fullFilename,ArchivePath):
  "safely send (or pretend to send)"
  global active
  global suffix
  m = re.search(r"\.[a-zA-Z0-9_]+$",filename)
  if (m):
	e = m.group(0)
  else:
	print 'file "%s" has no suffix?' % (filename)
	e = "??"
  if suffix.has_key(e):
	suffix[e] += 1
  else:
	suffix[e] = 1
  if active:
	print "%s%s -> %s" % (Indent,filename,ArchivePath) 
	shutil.copy2(fullFilename,ArchivePath)
  else:
	print "%s%s -> (%s)" % (Indent,filename,ArchivePath) 

###################

def year_subdir(s,ArchDir):
  subdir = time.strftime("%Y",time.localtime(s.st_ctime))
  result = os.path.join(ArchDir,subdir)
  new_dir(result)
  return result

###################

def month_subdir(s,ArchDir):
  subdir = time.strftime("%Y-%m-%b",time.localtime(s.st_ctime))
  result = os.path.join(ArchDir,subdir)
  new_dir(result)
  return result

###################

def dir_for_file(ArchDir,filepath):
  "dddd"
  s = os.stat(fullpath)
  subdir = time.strftime(timeFormat,time.localtime(s.st_ctime))
  if len(sys.argv) > 1:
    subdir = "%s_%s" % (subdir,sys.argv[1])
  if len(sys.argv) > 2:
    audioPrefix = "%s_" % (sys.argv[2])
  result = os.path.join(ArchDir,subdir)
  new_dir(result)
  return result

###################

def dest_dir_name(SrcPath,ArchDir):
  "dirname based on origination date"
  s = os.stat(SrcPath)
  rootDir = year_subdir(s,ArchDir)
  rootDir = month_subdir(s,rootDir)
  subdir = time.strftime(timeFormat,time.localtime(s.st_ctime))
  if len(sys.argv) > 1:
    subdir = "%s_%s" % (subdir,sys.argv[1])
  finaldir = os.path.join(rootDir,subdir)
  # should make sure it exists!
  new_dir(finaldir)
  return finaldir

###################

def copy_pix(FromDir,ArchDir,Indent):
  "Copy images"
  global totalCopied
  global active
  new_dir(ArchDir)
  if active:
	if not os.path.isdir(ArchDir):
	  print "Hey, image destination '%s' is not a directory!" % (ArchDir)
	  return 0
  if not os.path.exists(FromDir):
	print "Hey, image source '%s' is vapor!" % (FromDir)
	return 0
  if not os.path.isdir(FromDir):
	print "Hey, image source '%s' is not a directory!" % (FromDir)
	return 0
  okayCt = 0
  copies = 0
  for kid in os.listdir(FromDir):
    fromKidPath = os.path.join(FromDir,kid)
    archKidPath = os.path.join(ArchDir,kid)
    if os.path.isdir(fromKidPath):
      okayCt += copy_pix(fromKidPath,archKidPath,Indent+" ")
    else:
	  if os.path.exists(archKidPath):
		okayCt += 1
	  else:
		send_file(Indent,kid,fromKidPath,archKidPath)
		copies += 1
		totalCopied += 1
  if (active):
	  print "%s%s: %d items okay" % (Indent,FromDir,okayCt)
	  if copies > 0:
		  print "%s  (%d new items copied)" % (Indent,copies)
  else:
	  if copies > 0:
		  print "%s  (%d new items to be copied)" % (Indent,copies)
  return okayCt

###################

def copy_tracks(FromDir,ArchDir):
  "Copy audio tracks"
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
  for kid in os.listdir(FromDir):
    fullpath = os.path.join(FromDir,kid)
    if os.path.isdir(fullpath):
      copy_tracks(fullpath,ArchDir)
    else:
      fp2 = fullpath.upper()
      if fp2.endswith("MP3") or fp2.endswith("WAV"):
	print "%s..." % (kid)
	trackDir = dest_dir_name(fullpath,ArchDir)
	print "%s -> %s" % (kid,trackDir) 
	# INSERT CODE FOR RENAMING HERE
	# shutil.copy2(fullpath,trackDir)
      else:
	print "Skipping %s" % (fullpath)

###########

def dir_report():
  "tell me"
  global createdDirs
  print "\nDirectories ------------------------"
  kk = createdDirs.keys()
  kk.sort()
  print "%d total directories" % (len(kk))
  for g in kk:
	print "%s" % (g)

def file_report():
  "tell me"
  global totalCopied
  global createdDirs
  print "\nFiles ------------------------"
  print "%d total files" % (totalCopied)
  for g in suffix.keys():
	print "   %4d %s" % (suffix[g],g)


###########################################################
## MAIN EXECUTION STARTS HERE #############################
###########################################################

# SEEK SOURCE AND DEST DIRS ##############################################

if os.name != "nt":
  print "Sorry no code for OS '%s' yet!" % (os.name)
  exit()

pixDir = os.path.join("R:","Pix")
audioDir = os.path.join("R:","Audio")
if not os.path.exists(pixDir):
  print "Drobo picture path %s unavailable at the moment..." % (pixDir)
  exit()
if not os.path.exists(audioDir):
  print "Drobo audio path %s unavailable at the moment..." % (audioDir)
  exit()
srcDisk = os.path.join("D:","LocalAudio")
dcimDir = os.path.join("D:","LocalPix")

# AUDIO #########################################
# print "Archiving Audio from '%s'\n\tto '%s'" % (srcDisk,audioDir)
# copy_tracks(srcDisk,audioDir)
# PIX #########################################
print "Archiving Images from '%s'\n\tto '%s'" % (dcimDir,pixDir)
copy_pix(dcimDir,pixDir,"")

dir_report()
file_report()

# /disks/Removable/Flash\ Reader/EOS_DIGITAL/DCIM/100EOS5D/
# /disks/Removable/MK1237GSX/DOORKNOB/Pix/
