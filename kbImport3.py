# /usr/bin/python

r"""
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
  Store()
  ImgInfo()[]
    DNGConverter() # oops
"""

import sys
import argparse
if sys.version_info < (3,):
  print('Sorry, python3 required')
  exit()
sys.path.append('classes')
# pylint: disable=C0413
from AppOptions import AppOptions
import Volumes

options = AppOptions()
options.verbose = False
options.testing = False
options.version = "kbImport - 17may2023 - (c)2004-2023 K Bjorke"
options.win32 = sys.platform.startswith('win32')

#############################################################
### MAIN ACTION #############################################
#############################################################

if __name__ == '__main__':
  arguments = options.default_arguments()
  if len(sys.argv) > 1:
    parser = argparse.ArgumentParser(
        description='Import/Archive Pictures, Video, & Audio from removeable media')
    parser.add_argument('jobname',
                        help='appended to date directory names')
    parser.add_argument('-u', '--unify',
                        help='Unify imports to a single directory (indexed TODAY)',
                        action="store_true")
    parser.add_argument('-p', '--prefix', default="bjorke",
                        help='out filename prefix (use "none" to disable)')
    parser.add_argument('-P', '--project', action="store_true",
                        help='Project name overrides date')
    parser.add_argument('-j', '--jobpref',
                        help='toggle to include jobname in prefix',
                        action="store_true")
    parser.add_argument('-t', '--test',
                        help='test mode: list but do not copy',
                        action="store_true")
    parser.add_argument('-f', '--filter',
                        help='match regex string for import names')
    parser.add_argument('-d', '--age', type=int, default=0,
                        help='max days old')
    parser.add_argument('-l', '--local',
                        help='local archive only',
                        action="store_true")
    parser.add_argument('-x', '--pix_only',
                        help='pictures only',
                        action="store_true")
    parser.add_argument('-S', '--syn',
                        help='Store to Synology if available (overrides -c)',
                        action="store_true")
    parser.add_argument('-c', '--cloud',
                        help='cloud share archive if available',
                        action="store_true")
    parser.add_argument('-v', '--verbose',
                        help='noisy output', action="store_true")
    parser.add_argument('-s', '--source',
                        help='Specify source removeable volume (otherwise will guess)')
    parser.add_argument('-a', '--archive',
                        help='specify archive directory (otherwise will use std names)')
    parser.add_argument('-r', '--rename',
                        help='rename on the same drive, rather than copy',
                        action="store_true")
    parser.add_argument('-n', '--numerate',
                        help='number images as an animation sequence',
                        action="store_true")
    try:
      arguments = parser.parse_args()
    except:
      print("adios")
      sys.exit()
  else:
    print("Using fake arguments as a test.")

  # TODO(kevin): catch -h with empty args?
  options.user_args(arguments)

  activeVols = Volumes.Volumes(options)
  activeVols.archive()

# eof
