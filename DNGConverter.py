#! /bin/python

class DNGConverter(object):
  """handle optional DNG conversion"""
  def __init__(self, Active=False):
    self.active = bool(Active and WIN32_OK)
    self.nConversions = 0
    self.seek_converter()

  def convert(self, srcPath, destPath, destName):
    "TODO: check for testing? - based on old dng_convert()"
    # TODO: get command from Volumes instance
    if not WIN32_OK:
      return False
    cmd = "\"{}\" -c -d \"{}\" -o {} \"{}\"".format(
        self.converter, destPath, destName, srcPath)
    # print(cmd)
    if TESTING:
      print(cmd)
      return True # pretend
    p = os.popen(r'cmd /k')
    p[0].write('{}\r\n'%cmd)
    p[0].flush()
    p[0].write('exit\r\n')
    p[0].flush()
    print(''.join(p[1].readlines()))
    self.nConversions += 1    # TODO - Volume data
    return True

  def seek_converter(self):
    """find a DNG converter, if one is available"""
    self.converter = None
    if not WIN32_OK:
      self.active = False
      return
    pf = os.environ.get('PROGRAMFILES')
    if pf: # windows
      self.converter = os.path.join(pf, "Adobe", "Adobe DNG Converter.exe")
      if not os.path.exists(self.converter):
        pfx = os.environ.get('PROGRAMFILES(X86)')
        self.converter = os.path.join(pfx, "Adobe", "Adobe DNG Converter.exe")
      if not os.path.exists(self.converter):
        self.converter = None

if __name__ == '__main__':
  print("testing time")
