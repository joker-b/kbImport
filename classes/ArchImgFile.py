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
import xml.etree.ElementTree as ET

# never needed?
if sys.version_info > (3,):
  long = int

'''
EXIF Tags we care about
Rating: 0
UserComment: ""

pp3 fields: (grep)
Rank=2
ColorLabel=0

xmp fields:
xmp:Rating="3"

(xmp files can be general or for specific JPG/RAF files... by DarkTable?)
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
    self.rating = None
    self.label = None
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

  def _query_xmp(self):
    '''
    only if the file is xmp... could also use exiftool!
    '''
    tree = ET.parse(self.filename)
    root = tree.getroot()
    desc = root[0][0] # risky?
    ratingI = '{http://ns.adobe.com/xap/1.0/}Rating'
    labelI = '{http://ns.adobe.com/xap/1.0/}Label'
    self.rating = desc.get(ratingI)
    self.label = desc.get(labelI)
  def _query_exif(self):
    j = subprocess.run(["exiftool", "-json", "-Rating", "-Label", "-UserComment", self.filename],
          capture_output=True)
    exif = json.loads(j.stdout)[0]
    print(exif)
    self.rating = exif.get('Rating')
    self.label = exif.get('Label')
  def _query_pp3(self):
    rank_exp = re.compile(r'Rank=(\d+)')
    label_exp = re.compile(r'ColorLabel=(\d+)')
    for line in open(self.filename, 'r'):
      m = rank_exp.match(r'Rank=(\d+)', line)
      if m:
        self.rating = int(m.group(1))
      m = label_exp.match(line)
      if m:
        self.label = int(m.group(1))
  def query_rating(self):
    if not os.path.exists(self.filename):
      return None
    ext = os.path.splitext(self.filename)[1].lower()
    if ext == '.pp3':
      self._query_pp3()
    elif ext == '.xmp':
      self._query_xmp()
    elif ext == '.jpg':
      self._query_exif()
    else:
      self._query_exif()
    return self.rating
  def __str__(self):
    return '.../{}: rating {}, arch to {}'.format(os.path.basename(self.filename),
      self.query_rating(), self.archive_location())


#
# Unit Test
#
if __name__ == '__main__':
  #H = os.environ['HOME']
  #f = H+'/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_13_XE/bjorke_XE_ESCF4060.JPG'
  H = '/home/kevinbjorke/pix/kbImport/Pix/2020'
  samples = [
    H+'/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF',
    H+'/2020-06-May/2020_06_06_WoodX/bjorke_Wood_DSCF6121.JPG',
    H+'/2020-06-May/2020_06_06_WoodX/bjorke_Wood_DSCF6121.RAF',
    H+'/2020-06-May/2020_06_06_WoodX/bjorke_Wood_DSCF6121.xmp',
  ]
  for f in samples:
    aif = ArchImgFile(f) 
    print("Archive Location {}".format(aif.archive_location()))
    print(aif)
