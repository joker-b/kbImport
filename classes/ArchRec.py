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
	'''
	def __init__(self, Filename = None):
		self.filename = Filename
		self.volume = self.seek_volume()
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
	def __init__(self, Filename):
		self.versions = [ ArchImgFile(Filename) ]

class ArchDB(object):
	'collection of ArchRecs'
	archRecs = {} # indexed on tuple (origname,date) ?
	def __init__(self, dbFile=None):
		if dbFile is not None:
			# TODO load that file
			# if it fails, print an error and continue empty
			print("get db from storage")
	def add_image(self, rec):
		print('add to archRecs')

def archive_folder(source_path):
	'go through folder adding ArchRecs and add to ArchDB'
	print("blah")

if __name__ == '__main__':
  print("testing time")
  r = ArchRec('blah.jpg')
  d = ArchDB()
  d.add_image(r)




