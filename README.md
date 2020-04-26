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

Copying vs Renaming
---

As of April 2020 kbImport can also rename and arrange "simple backup" files in disk: e.g., if you have just copied am SD card DCIM to a local drive, kbImport can find those files, relabel and rearrange them _on the same disk._ This requires no real copying and is just very fast. Use the `-r` option for relabelling.

As you'll see below, raw copying followed by relabelling can be the fastest option for some devices.

Some Performance Numbers
---

Testing with about a dozen `JPG`/`RAF` pairs:

_25 April 2020: Discovered that performance numbers from kbImport are wrong - they should be *higher.* They'd been accidentally scaled not by elapsed time `(bytes/time)` but instead by `(bytes/(time*time))` -- new numbers forthcoming._

* On *Chromebook Galaxy* with *Letscom* external: *Revised* based on 11,63GB in 423 files
* To External SSD: 26.5 minutes, 7.471 Mb/s
* To microSD evo256 : 26.7 minutes  7.403 Mb/sec with one error from SD reader - second run fixed in about 5 seconds
* Drag to microSD of the same folder: about 8mins, or 24.8 MB/sec + renaming 36sec = about 24MB/sec
* WD auto-backup: about 5 minutes, or about 40MB/s + renaming pass 28sec ("486MB/sec") or in total about 36MB/s
* `cp -r` to internal drive: 5.5min or about 36MB/s before renaming - flaky SSD reader? one error
* *Macbook Air 2013* with integrated SD reader
* To External SSD: 2.44 minutes, 81.394 Mb/s
* *Win 10 desktop* with IOGear SD reader
* To External SSD: 5.29 minutes, 37.547 Mb/s

Older Performance Numbers
----

* *Macbook Air* with integrated SD reader
* On MBA internal to SSD: about 576 Mb/sec (questionable)
* Drag in MBA finder card->SSD: \~6.5 Mb/sec!
* `cp -r` on MBA card->SSD: \~380 Mb/sec
* *Windows 10 desktop* (older):
* Windows desktop: \~160 Mb/sec (questionable)
* *Macbook Pro 2018*
* On Satechi external reader to SSD: about 410 Mb/sec (questionable)
* On Letscom external reader to SSD: about 444 Mb/sec (questionable)
* Additional *Galaxy Chromebook*
* `cp -r` on GCB card->SSD: \~125 Mb/sec

drobolize - deprecated for 2020
---------

Because kbImport is meant to be useful even on small laptops when travelling (I often have used it on an Asus EE-PC with an
external HD), it will first look for the "master" archive (for me, a drobo disk stack) and if it can't find it, it will
seek a sensible local-system location for media storgage. Then later, when the master archive is available the temporary
local archive can be merged into the master using <b>drobolize.py</b> -- be sure to double-check the expected locations
in this script, because like kbImport it expects *my* drive locations -- yours may vary.

