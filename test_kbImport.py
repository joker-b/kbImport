# /usr/bin/python

"""
tests for kbImport"
"""

import logging
import unittest

from kbImport3 import *

class MyTest(unittest.TestCase):
	def setUp(self):
		self.v = Volumes()
	def test_safe_mkdir(self):
		forceTest = True
		self.assertTrue(safe_mkdir('/Users/kevinbjorke/dummy/anywhere','~/anywhere',forceTest))
		self.assertTrue(safe_mkdir('/Users/kevinbjorke/src/kbImport','~/src/kbImport',forceTest))
	def test_hasPrimary(self):
		self.assertTrue(len(self.v.PrimaryArchiveList) > 0)
	def test_hasRLocal(self):
		self.assertTrue(len(self.v.LocalArchiveList) > 0)
	def test_archive_loc(self):
		"obviously this test needs to be run on a machine with such a drive..."
		self.assertTrue(self.v.find_archive_drive())

if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	# get the default logger
	logger = logging.getLogger()
	# add a file handler
	logger.addHandler(logging.FileHandler('stdout.txt', mode='w'))
	# set up a stream for all stderr output
	stderr_file = open('stderr.txt', 'w')
	# attach that stream to the testRunner
	unittest.main(testRunner=unittest.TextTestRunner(stream=stderr_file))
	runner = unittest.TextTestRunner(stream=stderr_file)
	itersuite = unittest.TestLoader().loadTestsFromTestCase(MyTest)
	runner.run(itersuite)
	# unittest.main()
	#sys.exit()

