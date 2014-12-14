kbImport
========

Media-import pictures, audio files, and video from a variety of different cameras and devices, including AVCD and various
RAW formats... even scanners. Just put in the SD card and run kbImport.

Used on varying computers at different times: Mac, Linux, Windows. This is a personal script that I have used and
grown over several years of continuous use.

All files are organized under a uniform filing system so it's easy to find images etc based on when and what,
not which hardware. That said, *You need to edit the file* to indicate the drives you use for archiving. Every
system's drive layout may be slightly different. I wish that weren't so, but it is. My (Windows) archive
is on "G:" -- yours may be on "R:" or who knows. So make sure you check! The expected drive locations are right near the
top of the file.

Usage: insert media, then run:
>   python kbImport3.py [JobName]

The [JobName] is optional but helpful. Imported files will be laid-out onto the archive disk as follows
(YYY MM and DD fields are numbers indicating dates):

<pre>
   Audio
      YYYY
         YYYY-MM-Mon
            YYYY\_MM\_DD\_JobName
               R09_0003.MP3
   Pix
      YYYY
         YYYY-MM-Mon
            YYYY\_MM\_DD\_JobName
               rw2s
                  P2357652.RW2
                  P2357653.RW2
               P2357652.JPG
               P2357652.DNG
               P2357653.JPG
               P2357653.DNG
   Vid
      YYYY
         YYYY-MM-Mon
            YYYY\_MM\_DD\_JobName
               P1090545.JPG
               P1090545.MOV
               AVCHD
</pre>

<b>MetaData:</b> kbImport just moves files around, it doesn't assign metadata. For pictures, I use the 'AllMine' script within Photoshop, which can be found at https://github.com/joker-b/PhotoshopScripts

<b>Variations:</b> In the case of the Pix directory, the "rw2s" subdirectory is optional -- it was created by
kbImport when convrting .RW2 format files to .DNG. If DNG wasn't applied, then the .RW2 files would be in the primary
archive.

In the Vid directory, either the AVCHD directory will be present _or_ the .MOV file with matching .JPG thumbnail (unless
you have archived video from two different cameras using different standards into the same directory). Since AVCHD
data formatting is somewhat... brittle, if you have multiple AVCHD cameras shooting on the same day, archive them
using slightly different JobNames, e.g. "WeddingCam1" and "WeddingCam2".


drobolize
---------

Because kbImport is meant to be useful even on small laptops when travelling (I often have used it on an Asus EE-PC with an
external HD), it will first look for the "master" archive (for me, a drobo disk stack) and if it can't find it, it will
seek a sensible local-system location for media storgage. Then later, when the master archive is available the temporary
local archive can be merged into the master using <b>drobolize.py</b> -- be sure to double-check the expected locations
in this script, because like kbImport it expects *my* drive locations -- yours may vary.

