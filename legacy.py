#! /usr/bin/python3


import sys
import argparse
sys.path.append('classes')
import ArchDB

def get_test_pic():
  return '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'

def get_test_folder():
  # f2 = '/home/kevinbjorke/pix/kbImport/Pix/'
  # f2 = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun'
  for f2 in [
      # '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_06_WoodX/',
      '/Volumes/pix20s/kbImport/Pix/',
      '/Volumes/pix18/kbImport/Pix/',
      '/Volumes/pix18/Pix/',
      '/Volumes/pix17/Pix/',
      '/Volumes/pix20/Pix/',
      '/Volumes/Sept2013/Pix/',
      '/Volumes/CameraWork/Pix/']:
    if os.path.exists(f2):
      return f2
  return '.' # less-awkward fail

def add_test_scan_to_db(Filename = None):
  test_pic = get_test_pic()
  test_folder = get_test_folder()
  # test_folder = '/home/kevinbjorke/pix/'
  if Filename is None:
    db = ArchDB()
  else:
    db = ArchDB.load(Filename)
  # d.add_file(f)
  print("let's scan {}".format(test_folder))
  nf = db.add_folder(test_folder)
  print('Added {} new files'.format(nf))
  return db

def test_archiving(db, DestDir):
  print("sending to {}".format(DestDir))
  total = db.archive_to(DestDir)
  print("Archived {} files".format(total))

#
# #######################
#

if __name__ == '__main__':
  test_db = ArchDB.ArchDB.load('pix18-20s-db.pkl')
  if test_db is None:
    sys.exit()
  if len(sys.argv) > 1:
    #test_db = add_test_scan_to_db('pix18-20s-db.pkl')
    # test_db.describe()
    # test_db.dop_hunt()
    # ArchDB.save(test_db, 'pix18-20s-db.pkl')
    test_archiving(test_db, '/Volumes/Legacy20/Pix')
    ArchDB.ArchDB.describe_created_dirs()
  else:
    test_db.describe()

'''
if __name__ == '__main__':
  arguments = options.default_arguments()
  if len(sys.argv) > 1:
    parser = argparse.ArgumentParser(
        description='Import/Archive Pictures, Video, & Audio from removeable media')
    parser.add_argument('jobname',
                        help='appended to date directory names')
    parser.add_argument('-u', '--unify',
                        help='Unify imports to a single directory (indexed TODAY)',
                        action="store_true")
    parser.add_argument('-p', '--prefix',
                        help='include string in filename as prefix')
    parser.add_argument('-j', '--jobpref',
                        help='toggle to include jobname in prefix',
                        action="store_true")
    parser.add_argument('-t', '--test',
                        help='test mode: list but do not copy',
                        action="store_true")
    parser.add_argument('-v', '--verbose',
                        help='noisy output', action="store_true")
    parser.add_argument('-s', '--source',
                        help='Specify source removeable volume (otherwise will guess)')
    parser.add_argument('-a', '--archive',
                        help='specify source archive directory (otherwise will use std names)')
    parser.add_argument('-r', '--rename',
                        help='rename on the same drive, rather than copy',
                        action="store_true")
    parser.add_argument('-n', '--numerate',
                        help='number images as an animation sequence',
                        action="store_true")
    try:
      arguments = parser.parse_args()
    except:
      print("adios")
      sys.exit()
  else:
    print("using fake arguments")

  # TODO(kevin): catch -h with empty args?
  options.user_args(arguments)

  activeVols = Volumes.Volumes(options)
  activeVols.archive()
 '''