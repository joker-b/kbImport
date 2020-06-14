'''
  A record indicating a single picture file
  TODO: add date, size
  TODO: look for selection markers: ratings, colors
         (may be in exif, in XMP or PP3 files)
  TODO: check for archive status
  TODO: determine best archive location as appropriate
'''

import os
import sys
import re
import subprocess
import json

# never needed?
if sys.version_info > (3,):
  long = int

'''
EXIF Tags we care about
Rating: 0
UserComment: ""

'''

class ArchImgFile(object):
  '''
  '''
  def __init__(self, Filename = None):
    self.filename = Filename
    self.volume = None
    self.orig = None
    self.archived = False
    self.archDir = None
  def origin_name(self):
    "try to match camera standard naming patterns"
    if self.filename is None:
     return None
    if self.orig:
      return self.orig
    b = os.path.basename(self.filename)
    b = os.path.splitext(b)[0]
    m = re.search(r'[A-Za-z_][A-Za-z_]{3}\d{4}', b)
    if not m:
      self.orig = b
    else:
      self.orig = m.group()
    return self.orig
  def folder(self):
    chain = self.filename.split(os.path.sep)
    if len(chain) < 2:
      return '.'
    return chain[-2]
  def in_structured_folder(self):
    chain = self.filename.split(os.path.sep)
    if not re.match(r'\d{4}$', chain[-4]):
      return False
    self.yearDir = chain[-4]
    self.monthDir = chain[-3]
    self.dayDir = chain[-2]
    return True
  def in_annual_folder(self):
    chain = self.filename.split(os.path.sep)
    if len(chain) < 2:
      return False
    look = 2
    while look <= len(chain):
      if re.match(r'\d{4}$', chain[-look]):
        self.annualDir = os.path.sep.join(chain[-look:-1])
        return True
      look = look + 1
    return False
  def archive_location(self):
    if self.archDir:
      return self.archDir
    if self.in_structured_folder():
      self.archDir = os.path.join(self.yearDir, self.monthDir, self.dayDir)
    elif self.in_annual_folder():
      self.archDir = self.annualDir
    else:
      self.archDir = self.folder()
    return self.archDir
  def query_rating(self):
    j = subprocess.run(["exiftool", "-json", "-Rating", "-UserComment", self.filename],
          capture_output=True)
    exif = json.loads(j.stdout)[0]
    print(exif)
    self.rating = exif.get('Rating')
    return self.rating

  def __str__(self):
    return '.../{}: rating {}, arch to {}'.format(os.path.basename(self.filename),
      self.query_rating(), self.archive_location())


#
# Unit Test
#
if __name__ == '__main__':
  f = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'
  #H = os.environ['HOME']
  #f = H+'/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_13_XE/bjorke_XE_ESCF4060.JPG'
  aif = ArchImgFile(f) 
  print("Archive Location {}".format(aif.archive_location()))
  print(aif)
