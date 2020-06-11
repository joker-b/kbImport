#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
"""
import os
import sys
import re
import shutil

if sys.version_info > (3,):
  long = int

class ArchImgFile(object):
	'''
	A record indicating a single picture file
	TODO: add date, size
	TODO: cache some results
	'''
	def __init__(self, Filename = None):
		self.filename = Filename
		self.volume = self.seek_volume()
		self.orig = None
	def origin_name(self):
		"try to match camera standard naming patterns"
		if self.filename is None:
		 return None
		if self.orig:
			return self.orig
		b = os.path.basename(self.filename)
		b = os.path.splitext(b)[0]
		m = re.search(r'[A-Za-z_]{4}\d{4}', b)
		if not m:
			self.orig = b
		else:
			self.orig = m.group()
		return self.orig
	def seek_volume(self):
		if self.filename is None:
			return None
		# TODO: look at the local file system and determine the drive name


# todo complications: files of varying types
# xfc, png, tiff, etc....
class ArchRec(object):
	'''
	Data for one image.
	An image may have multiple representations, of varying formats and sizes.

	'''
	def __init__(self ):
		self.versions = [ ]
	def add_img_file(self, ArchImg):
		self.versions.append(ArchImg)
	def __str__(self):
		n = self.versions[0].origin_name()
		return '{}: {}'.format(n, len(self.versions))

class ArchDB(object):
	'''
	Collection of ArchRecs
	TODO: pickle
	TODO: debug messages, sizes, etc
	TODO: archive
	'''
	def __init__(self, dbFile=None):
		if dbFile is not None:
			# TODO load that file
			# if it fails, print an error and continue empty
			print("get db from storage")
		self.archRecs = {}
	def add_file(self, Filename):
		img = ArchImgFile(Filename)
		o = img.origin_name()
		rec = self.archRecs.get(o)
		if not rec:
			rec = ArchRec()
			self.archRecs[o] = rec
		rec.add_img_file(img)
	def add_folder(self, Folder):
		for d in os.listdir(Folder):
			full = os.path.join(Folder,d)
			if os.path.isdir(full):
				self.add_folder(full)
			else:
				self.add_file(full) # TODO: only images
	def __str__(self):
		return ('{} Images:\n'.format(len(self.archRecs)) + 
			'\n'.join([self.archRecs[a].__str__() for a in self.archRecs]))


def archive_folder(source_path):
	'go through folder adding ArchRecs and add to ArchDB'
	print("blah")

if __name__ == '__main__':
  print("testing time")
  f = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'
  f2 = '/home/kevinbjorke/pix/kbImport/Pix/'
  d = ArchDB()
  # d.add_file(f)
  d.add_folder(f2)
  # d.add_folder(os.path.split(f)[0])
  print(d)




