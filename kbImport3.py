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

# TODO items:
# TODO -- ignore list eg ['.dropbox.device']
# TODO - itemized manifest @ end ("# of pix to dir xxxx" etc)

# TODO - handle new device: WD WiFi Hard rive archiving onto different hard drive
# TODO - frames for animaition: renumber (RAF/JPG will require a map), then also write a
      # text file showing the map
# TODO handle inter-HD uploads in general? (this used to the be domain of "drobolize")

Class Hierarchy:
Volumes()
  Drives()
  StorageHierarchy()
  ArchiveImg()[]
    DNGConverter() # oops
"""

import sys
import os
import shutil
#import subprocess
import argparse
import Volumes

WIN32_OK = True
try:
# pylint: disable=E0401
# this error is more informatiove than "platform"
  import win32api
  # import win32file
except ModuleNotFoundError:
  WIN32_OK = False



################################################
##### global variable ##########################
################################################

VERSION_STRING = "kbImport - 21apr2020 - (c)2004-2020 K Bjorke"
# if TESTING is True, don't actually copy files (for testing).....
TESTING = False
VERBOSE = False

#########################################################################################
## FUNCTIONS START HERE #################################################################
#########################################################################################



#############################################################
### MAIN ACTION #############################################
#############################################################


# MAIN EXECUTION BITS ##############
# MAIN EXECUTION BITS ##############
# MAIN EXECUTION BITS ##############

def fake_arguments():
  args = argparse.Namespace()
  args.jobname = 'test'
  args.prefix = None
  args.jobpref = None
  args.source = None
  args.archive = None
  args.unify = False
  args.test = True
  args.verbose = False
  args.numerate = False
  return args


if __name__ == '__main__':
  arguments = fake_arguments()
  if len(sys.argv) > 1:
    parser = argparse.ArgumentParser(
        description='Import/Archive Pictures, Video, & Audio from removeable media')
    parser.add_argument('jobname',
                        help='appended to date directory names')
    parser.add_argument('-u', '--unify',
                        help='Unify imports to a single directory (indexed TODAY)',
                        action="store_true")
    parser.add_argument('-p', '--prefix',
                        help='include string in filename as prefix')
    parser.add_argument('-j', '--jobpref',
                        help='toggle to include jobname in prefix',
                        action="store_true")
    parser.add_argument('-t', '--test',
                        help='test mode: list but do not copy',
                        action="store_true")
    parser.add_argument('-v', '--verbose',
                        help='noisy output', action="store_true")
    parser.add_argument('-s', '--source',
                        help='Specify source removeable volume (otherwise will guess)')
    parser.add_argument('-a', '--archive',
                        help='specify source archive directory (otherwise will use std names)')
    parser.add_argument('-n', '--numerate',
                        help='number images as an animation sequence',
                        action="store_true")
    try:
      arguments = parser.parse_args()
    except:
      print("adios")
      sys.exit()
  else:
    print("using fake arguments")

  # TODO(kevin): catch -h with empty args?
  ActiveVolumes = Volumes.Volumes(arguments, VERBOSE, WIN32_OK, TESTING, VERSION_STRING)
  ActiveVolumes.archive()

# /disks/Removable/Flash\ Reader/EOS_DIGITAL/DCIM/100EOS5D/
# /disks/Removable/MK1237GSX/DOORKNOB/Pix/

# on linux seek /media/kevin/pix15
