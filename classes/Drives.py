#! /bin/python

"""
The various config and OS-specific handling data/methods for Drives

It's hoped that all OS-specific stuff goes in here as a clean abstraction

TODO: blah, worry less about "clean abstraction" and more about clear code and data

TODO: watch out for any Cloud Drive, ensure it's never a source

TODO: split build_primary_archive_list (side effect: forbidden sources)
"""

import sys
import os
import re
import glob
import subprocess 
from AppOptions import AppOptions, Platform

#pylint: disable=too-many-instance-attributes
# Nine is reasonable in this case.

# TODO: allow DIFFERENT targets for pix and videos,
# so that 'kbPix' etc can work on the NAS

class Drives(object):
  """
  Determine which archive and source drive locations are appropriate and available for the current device.
  """
  ExternalArchives = []
  LocalArchiveLocations = []
  ForbiddenSources = []
  PossibleSources = []
  # results: destinations for data to be archived
  archiveDrive = ""
  # under "archiveDrive"
  pixDestDir = ""
  vidDestDir = ""
  audioDestDir = ""
  # in GB - hack to not scan hard drives as source media
  # TODO: if we encounter SD Cards > 128GB, this will need revision
  largestSource = 130 * 1024*1024*1024

  def __init__(self, Options):
    """
    "Options" is an "AppOptions" object
    """
    self.opt = Options

  def cloud_archive(self):
    print("cloud_archive(): no platform handler for {}".format(self.opt.platform))
    # do nothing else to ExternalArchives

  def identify_external_archives(self, MountPoint, MoreDrives=[]):
    print("identify_external_archives({}): no platform handler for {}".format(MountPoint, self.opt.platform))
    # do nothing else to ExternalArchives
    return MountPoint
  
  def identify_local_archives(self, Extra=None):
    self.LocalArchiveLocations += [os.path.join(os.environ['HOME'], 'pix', 'kbImport')]
    if Extra is not None:
      self.LocalArchiveLocations += Extra
    self.ForbiddenSources += self.LocalArchiveLocations


  def available_archives(self, MountPoint, MoreDrives=[]):
    '''
    Primary Archives: that is, archives on external disks or the network
    Initialize the Primary Archives list, and 
      also make sure those drives (labelled appropriately) are in the ForbiddenSources list
    '''
    if not self.opt.force_local:
      if self.opt.force_cloud:
        self.cloud_archive()
      else:
        self.identify_external_archives(MountPoint, MoreDrives)
    self.ForbiddenSources += self.ExternalArchives # always true? TODO - maybe wrong for cloud...
    return MountPoint

  def init_drives(self):
    self.available_archives()
    print("init_drives(): no platform handler for {}".format(self.opt.platform))

  def process_options(self):
    '''
    TODO: this is messy and order-dependent
    '''
    if self.opt.force_local:
      self.ExternalArchives = []
      return
    if self.opt.archive is not None:
      self.ExternalArchives = [self.opt.archive]

  def show_drives(self):
    print('Primary: ', self.ExternalArchives)
    print('Local: ', self.LocalArchiveLocations)
    print('Forbidden: ', self.ForbiddenSources)
    print('Removable: ', self.PossibleSources)

  def available_source_vols(self, Vols=[]):
    if self.opt.verbose:
      print("Searching {} for source data".format(Vols))
    return [a for a in Vols if self.acceptable_source_vol(a)]

  def seekWDBackups(self):
    '''
    Look for backup volumes on a WD Wireless Drive (which are arranged according to WD's rules)
    '''
    backupLocations = []
    for srcDevice in self.PossibleSources:
      wdBackup = os.path.join(srcDevice, "SD Card Imports")
      if not os.path.exists(wdBackup):
        continue
      for day in os.listdir(wdBackup):
        dd = os.path.join(wdBackup, day)
        if os.path.isdir(dd):
          for tag in os.listdir(dd):
            td = os.path.join(dd, tag)
            if os.path.isdir(td):
              for card in os.listdir(td):
                cardDir = os.path.join(td, card)
                if os.path.isdir(cardDir):
                  backupLocations.append(cardDir)
    if len(backupLocations) < 1:
      return
    self.PossibleSources = backupLocations + self.PossibleSources

  def pretty(self, Path):
    return Path

  def acceptable_source_vol(self, Path):
    printable = self.pretty(Path)
    if not os.path.exists(Path):
      if self.opt.verbose:
        print("{} doesn't exist".format(printable))
      return False
    if not os.path.isdir(Path):
      print('Error: Proposed source "{}" is not a directory'.format(printable))
      return False
    if Path in self.ForbiddenSources:
      if self.opt.verbose:
        print("{} forbidden as a source".format(printable))
      return False
    s = os.path.getsize(Path) # TODO: this is not how you get volume size!
    if s > Drives.largestSource:
      print('Oversized source: "{}"'.format(printable))
      return False
    if self.opt.verbose:
      print("Found source {}".format(printable))
    return True

  def assign_removable(self, SourceName):
    self.PossibleSources = [SourceName]

  def found_archive_drive(self):
    "find an archive destination"
    if self.found_primary_archive_drive():
      return True
    if self.opt.force_cloud:
      print("Unable to find cloud archive")
      return
    return self.found_local_archive_drive()

  def found_primary_archive_drive(self):
    "find prefered destination"
    if self.opt.force_local:
      if self.opt.verbose:
        print("No need to find archive if we've forced a local destination")
      return False
    if self.opt.verbose:
      print("Primary Archive Candidates:\n\t{}".format('\n\t'.join(self.ExternalArchives)))
    for arch in self.ExternalArchives:
      if os.path.exists(arch):
        self.archiveDrive = arch
        if arch[-3:] == 'Pix':
          if not self.opt.pix_only:
            print('archiving photos only')
          self.opt.pix_only = True
          self.pixDestDir = arch
          self.vidDestDir = self.audioDestDir = None
        if arch[-1] == ':':       # windows
          arch = arch+os.path.sep
        self.pixDestDir = os.path.join(arch, "Pix")
        self.vidDestDir = os.path.join(arch, "Vid")
        self.audioDestDir = os.path.join(arch, "Audio")
        return True
      elif self.opt.verbose:
        print("Primary candidate {} not present".format(arch))
    if self.opt.verbose:
      print("Primary archive disk unavailable, from these {} options:".format(
          len(self.ExternalArchives)))
      print("  " + "\n  ".join(self.ExternalArchives))
    return False

  def found_local_archive_drive(self):
    "find 'backup' destination"
    for arch in self.LocalArchiveLocations:
      if os.path.exists(arch):
        self.archiveDrive = arch
        if arch[-1] == ':':
          arch = arch+os.path.sep
        if self.opt.verbose:
          print("Using local archive {}".format(arch))
        self.pixDestDir = os.path.join(arch, "Pix")
        self.vidDestDir = os.path.join(arch, "Vid")
        self.audioDestDir = os.path.join(arch, "Audio")
        return True
    print("Unable to find a local archive, out of these {} possibilities:".format(
        (len(self.LocalArchiveLocations))))
    print("  " + "\n  ".join(self.LocalArchiveLocations))
    return False

  def verify_archive_locations(self, store):
    "double-check existence of the archive sub_directories"
    for d in [self.pixDestDir, self.vidDestDir, self.audioDestDir]:
      if store.safe_mkdir(d) is None:
        print("Error, cannot verify archive {}".format(d))
        return False
    return True

###########################################################
###########################################################
###########################################################

class LinuxDrives(Drives):
  def identify_external_archives(self, MountPoint, MoreDrives=[]):
    # mk = '/media/kevin'
    knownDrives = ['pix20','KBWIFI','pix20s'] + MoreDrives
    archDrives = [d for d in knownDrives if os.path.exists(os.path.join(MountPoint, d))]
    if not self.opt.force_local:
      for d in [os.path.join(MountPoint, d, 'kbImport') for d in archDrives]:
        if os.path.exists(d):
          self.ExternalArchives.append(d)
    self.ForbiddenSources += self.ExternalArchives
    return MountPoint

  def init_drives(self):
    """
    TODO: modify for Raspberry (done?)
    """
    mk = self.available_archives('/mnt')
    self.identify_local_archives()
    # TODO(kevin): choose a better local default?
    self.ForbiddenSources.append(os.path.join(mk, 'Legacy20'))
    self.ForbiddenSources.append(os.path.join(mk, 'KBWIFI', 'kbImport'))
    self.ForbiddenSources.append("Storage")
    knownDrives = ['pix20','KBWIFI','pix20s']
    self.PossibleSources = self.available_source_vols(
        [os.path.join(mk, a) for a in os.listdir(mk) if not knownDrives.__contains__(a) and (len(a) <= 8)]) if \
            os.path.exists(mk) else []
    if self.opt.rename:
      # look for some known locations of unformatted backups
      wdBkp = os.path.join(mk,'KBWIFI','SD Card Imports/')
      bkpDirs = glob.glob(wdBkp+'*/*/*')
      bkpDirs.append(os.path.join(mk,'evo256','pix'))
      bkpDirs.append("/home/kevinbjorke/pix/Drag_SD_Data_Here")
      self.PossibleSources = bkpDirs + self.PossibleSources
    else:
      self.ForbiddenSources.append(os.path.join("Storage", "SD Card Imports"))
    # self.show_drives()

#################################################################

class ChromebookDrives(LinuxDrives):
  def init_drives(self):
    mk = self.available_archives(os.path.join('/mnt/chromeos', "removable"), ['evo256'])
    # TODO(kevin): choose a better local default?
    self.identify_local_archives()
    self.ForbiddenSources.append(os.path.join(mk, 'Legacy20'))
    self.ForbiddenSources.append(os.path.join(mk, 'KBWIFI', 'kbImport'))
    self.ForbiddenSources.append("Storage")
    knownDrives = ['pix20','KBWIFI','pix20s']
    self.PossibleSources = self.available_source_vols(
        [os.path.join(mk, a) for a in os.listdir(mk) if not knownDrives.__contains__(a) and (len(a) <= 8)]) if \
            os.path.exists(mk) else []
    if self.opt.rename:
      # look for some known locations of unformatted backups
      wdBkp = os.path.join(mk,'KBWIFI','SD Card Imports/')
      bkpDirs = glob.glob(wdBkp+'*/*/*')
      bkpDirs.append(os.path.join(mk,'evo256','pix'))
      bkpDirs.append("/home/kevinbjorke/pix/Drag_SD_Data_Here")
      self.PossibleSources = bkpDirs + self.PossibleSources
    else:
      self.ForbiddenSources.append(os.path.join("Storage", "SD Card Imports"))
    # self.show_drives()

class UbuntuDrives(LinuxDrives):
  def init_drives(self):
    """
    TODO: modify for Raspberry (done?)
    """
    mk = self.identify_external_archives(os.path.join('/media/', os.environ['USER']))
    self.identify_local_archives()
    self.ForbiddenSources.append(os.path.join(mk, 'Legacy20'))
    self.ForbiddenSources.append(os.path.join(mk, 'KBWIFI', 'kbImport'))
    self.ForbiddenSources.append("Storage")
    knownDrives = ['pix20','KBWIFI','pix20s']
    self.PossibleSources = self.available_source_vols(
        [os.path.join(mk, a) for a in os.listdir(mk) if not knownDrives.__contains__(a) and (len(a) <= 8)]) if \
            os.path.exists(mk) else []
    if self.opt.rename:
      # look for some known locations of unformatted backups
      wdBkp = os.path.join(mk,'KBWIFI','SD Card Imports/')
      bkpDirs = glob.glob(wdBkp+'*/*/*')
      bkpDirs.append(os.path.join(mk,'evo256','pix'))
      bkpDirs.append("/home/kevinbjorke/pix/Drag_SD_Data_Here")
      self.PossibleSources = bkpDirs + self.PossibleSources
    else:
      self.ForbiddenSources.append(os.path.join("Storage", "SD Card Imports"))
    # self.show_drives()

class WSLDrives(LinuxDrives):
  def init_drives(self):
    mk = '/mnt'
    externalExtras = ['d']
    self.ForbiddenSources.append('/mnt/c')
    self.ForbiddenSources.append('/mnt/d')
    # TODO: review all this convoluted stuff
    knownDrives = ['pix20','KBWIFI','pix20s', 'd']
    archDrives = [d for d in knownDrives if os.path.exists(os.path.join(mk,d))]
    if not self.opt.force_local:
      if self.opt.force_cloud:
        print('Sorry -c option not yet supported on this platform')
      for d in [os.path.join(mk, d, 'kbImport') for d in archDrives]:
        if os.path.exists(d):
          externalExtras.append(d)
    self.identify_external_archives('/mnt', externalExtras)
    self.identify_local_archives(['/mnt/c/Users/kevin/Google Drive/kbImport'])
    self.ForbiddenSources.append(os.path.join(mk, 'Legacy20'))
    self.ForbiddenSources.append(os.path.join(mk, 'KBWIFI', 'kbImport'))
    self.ForbiddenSources.append("Storage")
    self.PossibleSources = self.available_source_vols(
        [os.path.join(mk, a) for a in os.listdir(mk) if not knownDrives.__contains__(a) and (len(a) <= 8)]) if \
            os.path.exists(mk) else []
    if self.opt.rename:
      # look for some known locations of unformatted backups
      wdBkp = os.path.join(mk,'KBWIFI','SD Card Imports/')
      bkpDirs = glob.glob(wdBkp+'*/*/*')
      bkpDirs.append(os.path.join(mk,'evo256','pix'))
      bkpDirs.append("/home/kevinbjorke/pix/Drag_SD_Data_Here")
      self.PossibleSources = bkpDirs + self.PossibleSources
    else:
      self.ForbiddenSources.append(os.path.join("Storage", "SD Card Imports"))
    # self.show_drives()

###########################################################
###########################################################
###########################################################

class WindowsDrives(Drives):
  @classmethod
  def getDriveName(cls, driveletter):
    q = subprocess.check_output(["cmd","/c vol "+driveletter]).decode()
    if 'has no' in q:
      return driveletter
    return q.split("\r\n")[0].split(" ").pop()

  def init_drives(self):
    # 2020 approach: iterate through drive names, looking for for /kbImport/
    #    if not found, look for Pix & Vid
    #    if not found, fall back on local drive
    # then go through sources again looking for DCIM. Don't delve deeply.
    # TODO: this hasn't been fleshed-out for windcows at all
    if not self.opt.force_local:
      if self.opt.force_cloud:
          v = os.path.join(os.environ['HOMEPATH'],'SynologyDrive', 'kbImport')
          # v = os.path.join(os.environ['HOMEPATH'],'Google Drive', 'kbImport')
          if os.path.exists(v):
            self.ExternalArchives.append(v)
            self.ForbiddenSources.append('C:')
      else:
        for ltr in [chr(a)+':' for a in range(68,76)]:
          v = os.path.join(ltr,'kbPix')  # TODO(kevin): really want `\\\\Bank65\\kbPix` etc
          if os.path.exists(v):
            if not self.opt.pix_only:
              print("Archiving photos only")
            self.opt.pix_only = True
            self.ExternalArchives.append(v)
            self.ForbiddenSources.append(ltr)
            self.ForbiddenSources.append(v)
          else:
            v = os.path.join(ltr,'kbImport')
            if os.path.exists(v):
              self.ExternalArchives.append(v)
              self.ForbiddenSources.append(ltr)
              self.ForbiddenSources.append(v)
            else:
              v = os.path.join(ltr,'Pix')
              if os.path.exists(v):
                self.ExternalArchives.append(ltr)
                self.ForbiddenSources.append(ltr)
                self.ForbiddenSources.append(ltr)
    self.LocalArchiveLocations = [r'C:\Users\kevin\SynologyDrive\kbImport'] # TODO(kevin) fix this!
    if self.opt.verbose:
      print("Primary archive: {} options available:".format(
          len(self.ExternalArchives)))
      print("  " + "\n  ".join(self.ExternalArchives))
    self.ForbiddenSources = self.ForbiddenSources + self.LocalArchiveLocations
    src_candidates = []
    for ltr in [chr(a)+':' for a in range(68,76)]:
      if self.ForbiddenSources.__contains__(ltr):
        continue
      v = os.path.join(ltr,'DCIM')
      if os.path.exists(v):
        src_candidates.append(ltr)
    # print(src_candidates)
    self.PossibleSources = self.available_source_vols(src_candidates)
    #if self.opt.win32:
    #  self.PossibleSources = [d for d in self.PossibleSources \
    #         if win32file.GetDriveType(d)==win32file.DRIVE_REMOVABLE]

  def pretty(self, Path):
    try:
      name = Drives.getDriveName(Path[:2])
      return '"{}" ({})'.format(name, Path) # was: name[0]
    except:
      print("Can't get volume info for '{}'".format(Path))
    return Path

  def process_options(self):
    if self.opt.force_local:
      self.ExternalArchives = []
      return
    if self.opt.archive is not None:
      self.ExternalArchives = [self.opt.archive]
      if self.opt.verbose:
        print("Windows tweak for empty '::' declarations")
    # TODO(kevin): what is wanted here? and why isn't it in the Drives object?
    self.ExternalArchives[0] = re.sub('::', 'TODO', self.ExternalArchives[0])

  def assign_removable(self, SourceName):
    self.PossibleSources = ['{}:'.format(SourceName)]
    self.PossibleSources[0] = re.sub('::', ':', self.PossibleSources[0])

###########################################################
###########################################################
###########################################################

class MacDrives(Drives):
  def cloud_archive(self):
      self.ExternalArchives = [os.path.join(os.environ['HOME'],'SynologyDrive','kbImport')]
  
  def identify_external_archives(self, MountPoint, MoreDrives=[]):
    # ignore Moredrives
    self.ExternalArchives = [os.path.join(MountPoint, D) for D in
                               ['kbPix',
                               os.path.join('pix20s', 'kbImport'),
                               os.path.join('KBWIFI', 'kbImport'),
                               'pix18', 'pix15',
                                'CameraWork', 'Liq', 'Pix17', 'BJORKEBYTES',
                                'T3', 'Sept2013']]
    self.ForbiddenSources += self.ExternalArchives
    return MountPoint

  def init_drives(self):
    """
    seek source and archive locations for mac
    """
    #self.ExternalArchives = [os.path.join(os.environ['HOME'],'Google Drive','kbImport')]
    Vols = self.available_archives(os.path.sep+'Volumes')
    self.identify_local_archives()
    # TODO: big list, should these just be last-choice external archive locations?
    self.ForbiddenSources += [os.path.join(Vols, D) for D in
                             ['Macintosh HD',
                              'MobileBackups',
                              'pix20',
                              'pix20s',
                              'Legacy20',
                              'KBWIFI',
                              'kbPix',
                              '.timemachine',
                              'Pix',
                              'lazyback',
                              'backchiefback',
                              'Storage',
                              'Recovery',
                              'My Passport for Mac']]
    self.PossibleSources = self.available_source_vols(
        [os.path.join('/Volumes', a) for a in os.listdir('/Volumes')])
    self.seekWDBackups()

###########################################################
###########################################################
###########################################################

def DriveBuilder(Options=AppOptions()):
  if Options.platform == Platform['LINUX']:
    d =  WindowsDrives(Options)
  elif Options.platform == Platform['UBUNTU']:
    d = UbutuDrives(Options)
  elif Options.platform == Platform['WSL']:
    d = WSLDrives(Options)
  elif Options.platform == Platform['CROSTINI']:
    d = ChromebookDrives(Options)
  elif Options.platform == Platform['WINDOWS']:
    d = WindowsDrives(Options)
  elif Options.platform == Platform['MAC']:
    d =  MacDrives(Options)
  else:
    d =  Drives(Options)
  d.init_drives()
  d.process_options()
  return d

###########################################################
###########################################################
###########################################################

if __name__ == '__main__':
  print("Drives testing time")
  opt = AppOptions()
  opt.testing = True
  opt.verbose = True
  opt.set_jobname('DrivesTest')
  d = DriveBuilder(opt)
  d.show_drives()
  b = d.found_archive_drive()
  print("Archive found? {}: '{}''".format(b, d.archiveDrive))
  # b = d.verify_archive_locations()
