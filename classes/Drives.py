#! /bin/python

import sys
import os
import platform
import re
import glob
from AppOptions import AppOptions

#pylint: disable=too-many-instance-attributes
# Nine is reasonable in this case.

class Drives(object):
  """Source Devices"""
  PrimaryArchiveList = []
  LocalArchiveList = []
  ForbiddenSources = []
  PossibleSources = []
  # in GB - hack to not scan hard drives as source media
  largestSource = 130 * 1024*1024*1024

  def __init__(self, Options=AppOptions()):
    """blah"""
    self.opt = Options
    self.archiveDrive = ""
    self.pixDestDir = ""
    self.vidDestDir = ""
    self.audioDestDir = ""
    if os.name == 'posix': # mac?
      if platform.uname()[0] == 'Linux':
        self.init_drives_linux()
      else: # mac
        self.init_drives_mac()
    elif os.name == "nt" or self.opt.win32:
      self.init_drives_windows()
    else:
      print("Sorry no initialization for OS '{}' yet!".format(os.name))
    self.process_options()

  def process_options(self):
    if self.opt.archive is not None:
      self.PrimaryArchiveList = [self.opt.archive]
      if self.host == 'windows':
        # TODO(kevin): what is wanted here? and why isn't it in the Drives object?
        self.PrimaryArchiveList[0] = re.sub('::', 'TODO', self.PrimaryArchiveList[0])

  def show_drives(self):
    print('Primary: ', self.PrimaryArchiveList)
    print('Local: ', self.LocalArchiveList)
    print('Forbidden: ', self.ForbiddenSources)
    print('Removable: ', self.PossibleSources)

  def init_drives_linux(self):
    """
    TODO: modify for Raspberry
    """
    # mk = '/media/kevin'
    mk = '/mnt'
    self.host = 'linux'
    ch = os.path.join(mk,'chromeos')
    knownDrives = ['pix20s','KBWIFI','pix20']
    if os.path.exists(ch):
      self.host = 'crostini'
      mk = "/mnt/chromeos/removable"
      knownDrives.append('evo256')
    archDrives = [d for d in knownDrives if os.path.exists(os.path.join(mk,d))]
    self.PrimaryArchiveList = [os.path.join(mk, d, 'kbImport') for d in archDrives]
    # TODO(kevin): choose a better local default?
    self.LocalArchiveList = [os.path.join(os.environ['HOME'], 'pix', 'kbImport')]
    self.ForbiddenSources = self.PrimaryArchiveList + self.LocalArchiveList
    self.ForbiddenSources.append("Storage")
    self.PossibleSources = self.available_source_vols(
        [os.path.join(mk, a) for a in os.listdir(mk) if not knownDrives.__contains__(a) and (len(a) <= 8)]) if \
            os.path.exists(mk) else []
    if self.opt.rename:
      # look for some known locations of unformatted backups
      wdBkp = os.path.join(mk,'KBWIFI','SD Card Imports/')
      bkpDirs = glob.glob(wdBkp+'*/*/*')
      bkpDirs.append(os.path.join(mk,'evo256','pix'))
      bkpDirs.append("/home/kevinbjorke/pix/SD")
      self.PossibleSources = bkpDirs + self.PossibleSources
    else:
      self.ForbiddenSources.append(os.path.join("Storage", "SD Card Imports"))
    # self.show_drives()

  def init_drives_mac(self):
    self.host = 'mac'
    #self.PrimaryArchiveList = [os.path.join(os.environ['HOME'],'Google Drive','kbImport')]
    Vols = os.path.sep+'Volumes'
    self.PrimaryArchiveList = [os.path.join(Vols, D) for D in
                               ['pix20', 'pix18', 'pix15',
                                os.path.join('pix20s', 'kbImport'),
                                'CameraWork', 'Liq', 'Pix17', 'BJORKEBYTES',
                                'T3', 'Sept2013']]
    self.LocalArchiveList = [os.path.join(os.environ['HOME'], 'Pictures', 'kbImport')]
    self.ForbiddenSources = [os.path.join(Vols, D) for D in
                             ['Macintosh HD',
                              'MobileBackups',
                              'pix20s',
                              'Storage',
                              'Recovery',
                              'My Passport for Mac']]
    self.ForbiddenSources = self.ForbiddenSources + self.PrimaryArchiveList + self.LocalArchiveList
    self.PossibleSources = self.available_source_vols(
        [os.path.join('/Volumes', a) for a in os.listdir('/Volumes')])
    self.seekWDBackups()

  def init_drives_windows(self):
    # Defaults for Windows
    # TODO(kevin): this is a mess. Use the drive string name if possible...
    #   and attend to ForbiddenSources
    self.host = 'windows'
    self.PrimaryArchiveList = [r'I:\kbImport'] # , 'F:', 'R:']
    self.LocalArchiveList = [r'I:\kbImport']
    self.ForbiddenSources = self.PrimaryArchiveList + self.LocalArchiveList
    self.PossibleSources = self.available_source_vols(['G:']) # , 'J:', 'I:', 'H:', 'K:','G:'])
    #if self.opt.win32:
    #  self.PossibleSources = [d for d in self.PossibleSources \
    #         if win32file.GetDriveType(d)==win32file.DRIVE_REMOVABLE]

  def available_source_vols(self, Vols=[]):
    return [a for a in Vols if self.acceptable_source_vol(a)]

  def seekWDBackups(self):
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
    if not self.opt.win32:
      return Path
    try:
      name = win32api.GetVolumeInformation(Path)
      return '"{}" ({})'.format(name[0], Path)
    except:
      pass # print("Can't get volume info for '{}'".format(Path))
    return Path

  def acceptable_source_vol(self, Path):
    printable = self.pretty(Path)
    if not os.path.exists(Path):
      if self.opt.verbose:
        print("{} doesn't exist"%(printable))
      return False
    if not os.path.isdir(Path):
      print('Error: Proposed source "{}" is not a directory'.format(printable))
      return False
    if Path in self.ForbiddenSources:
      if self.opt.verbose:
        print("{} forbidden as a source"%(printable))
      return False
    s = os.path.getsize(Path) # TODO: this is not how you get volume size!
    if s > Drives.largestSource:
      print('Oversized source: "{}"'.format(printable))
      return False
    if self.opt.verbose:
      print("Found source {}".format(printable))
    return True

  def assign_removable(self, SourceName):
    if self.host == 'windows':
      self.PossibleSources = ['{}:'.format(SourceName)]
      self.PossibleSources[0] = re.sub('::', ':', self.PossibleSources[0])
    else:
      self.PossibleSources = [SourceName]

  def found_archive_drive(self):
    "find an archive destination"
    if self.found_primary_archive_drive():
      return True
    return self.found_local_archive_drive()

  def found_primary_archive_drive(self):
    "find prefered destination"
    for arch in self.PrimaryArchiveList:
      if os.path.exists(arch):
        self.archiveDrive = arch
        if arch[-1] == ':':       # windows
          arch = arch+os.path.sep
        self.pixDestDir = os.path.join(arch, "Pix")
        self.vidDestDir = os.path.join(arch, "Vid")
        self.audioDestDir = os.path.join(arch, "Audio")
        return True
    if self.opt.verbose:
      print("Primary archive disk unavailable, from these {} options:".format(
          len(self.PrimaryArchiveList)))
      print("  " + "\n  ".join(self.PrimaryArchiveList))
    return False

  def found_local_archive_drive(self):
    "find 'backup' destination"
    for arch in self.LocalArchiveList:
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
        (len(self.LocalArchiveList))))
    print("  " + "\n  ".join(self.LocalArchiveList))
    return False

  def verify_archive_locations(self, store):
    "double-check existence of the archive sub_directories"
    for d in [self.pixDestDir, self.vidDestDir, self.audioDestDir]:
      if store.safe_mkdir(d) is None:
        print("Error, cannot verify archive {}".format(d))
        return False
    return True

if __name__ == '__main__':
  print("Drives testing time")
  opt = AppOptions()
  opt.testing = True
  opt.verbose = True
  opt.set_jobname('DrivesTest')
  d = Drives(opt)
  d.show_drives()
  b = d.found_archive_drive()
  print("Archive found? {}: '{}''".format(b, d.archiveDrive))
  # b = d.verify_archive_locations()