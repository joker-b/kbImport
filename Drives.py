#! /bin/python

import sys
import os
import platform

#pylint: disable=too-many-instance-attributes
# Nine is reasonable in this case.

class Drives(object):
  """Source Devices"""
  PrimaryArchiveList = []
  LocalArchiveList = []
  ForbiddenSources = []
  RemovableMedia = []

  def __init__(self, Verbose=False, Win32=False):
    """blah"""
    self.verbose = Verbose
    self.win32 = Win32
    self.archiveDrive = ""
    self.pixDestDir = ""
    self.vidDestDir = ""
    self.audioDestDir = ""
    if os.name == 'posix': # mac?
      if platform.uname()[0] == 'Linux':
        self.init_drives_linux()
        self.show_drives()
      else: # mac
        self.init_drives_mac()
    elif os.name == "nt" or win32:
      self.init_drives_windows()
    else:
      print("Sorry no initialization for OS '{}' yet!".format(os.name))
      sys.exit()

  def show_drives(self):
    print('Primary: ', self.PrimaryArchiveList)
    print('Local: ', self.LocalArchiveList)
    print('Forbidden: ', self.ForbiddenSources)
    print('Removable: ', self.RemovableMedia)

  def init_drives_linux(self):
    """
    TODO: modify for Raspberry
    """
    # mk = '/media/kevin'
    mk = '/mnt'
    self.host = 'linux'
    # pxd = 'pix18'
    pxd = os.path.join('pix20s', 'kbImport')   # TODO(kevin): this is so bad
    mk = "/mnt/chromeos/removable"
    # pxd = 'pix20'
    self.PrimaryArchiveList = [os.path.join(mk, pxd)]
    # TODO(kevin): choose a better locl default?
    self.LocalArchiveList = [os.path.join(os.environ['HOME'], 'Pictures', 'kbImport')]
    self.ForbiddenSources = self.PrimaryArchiveList + self.LocalArchiveList
    self.ForbiddenSources.append("Storage")
    self.ForbiddenSources.append(os.path.join("Storage", "SD Card Imports"))
    self.RemovableMedia = self.available_source_vols(
        [os.path.join(mk, a) for a in os.listdir(mk) if a != pxd and (len(a) <= 8)]) if \
            os.path.exists(mk) else []

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
    self.RemovableMedia = self.available_source_vols(
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
    self.RemovableMedia = self.available_source_vols(['G:']) # , 'J:', 'I:', 'H:', 'K:','G:'])
    #if self.win32:
    #  self.RemovableMedia = [d for d in self.RemovableMedia \
    #         if win32file.GetDriveType(d)==win32file.DRIVE_REMOVABLE]

  def available_source_vols(self, Vols=[]):
    return [a for a in Vols if self.acceptable_source_vol(a)]

  def seekWDBackups(self):
    backupLocations = []
    for srcDevice in self.RemovableMedia:
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
    self.RemovableMedia = backupLocations + self.RemovableMedia

  def pretty(self, Path):
    if not self.win32:
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
      if self.verbose:
        print("{} doesn't exist"%(printable))
      return False
    if not os.path.isdir(Path):
      print('Error: Proposed source "{}" is not a directory'.format(printable))
      return False
    if Path in self.ForbiddenSources:
      if self.verbose:
        print("{} forbidden as a source"%(printable))
      return False
    s = os.path.getsize(Path) # TODO: this is not how you get volume size!
    if s > Volumes.largestSource:
      print('Oversized source: "{}"'.format(printable))
      return False
    if self.verbose:
      print("Found source {}".format(printable))
    return True

  def assign_removable(self, SourceName):
    if self.host == 'windows':
      self.RemovableMedia = ['{}:'.format(SourceName)]
      self.RemovableMedia[0] = re.sub('::', ':', self.RemovableMedia[0])
    else:
      self.RemovableMedia = [SourceName]

  def find_archive_drive(self):
    "find an archive destination"
    if self.find_primary_archive_drive():
      return True
    return self.find_local_archive_drive()

  def find_primary_archive_drive(self):
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
    if self.verbose:
      print("Primary archive disk unavailable, from these {} options:".format(
          len(self.PrimaryArchiveList)))
      print("  " + "\n  ".join(self.PrimaryArchiveList))
    return False

  def find_local_archive_drive(self):
    "find 'backup' destination"
    for arch in self.LocalArchiveList:
      if os.path.exists(arch):
        self.archiveDrive = arch
        if arch[-1] == ':':
          arch = arch+os.path.sep
        if self.verbose:
          print("Using local archive {}".format(arch))
        self.pixDestDir = os.path.join(arch, "Pix")
        self.vidDestDir = os.path.join(arch, "Vid")
        self.audioDestDir = os.path.join(arch, "Audio")
        return True
    print("Unable to find a local archive, out of these {} possibilities:".format(
        (len(self.LocalArchiveList))))
    print("  " + "\n  ".join(self.LocalArchiveList))
    return False

  def verify_archive_locations(self):
    "double-check existence of the archive directories"
    for d in [self.pixDestDir, self.vidDestDir, self.audioDestDir]:
      if not os.path.exists(d):
        print("Error, cannot verify archive {}".format(d))
        return False
    return True

if __name__ == '__main__':
  print("testing time")
