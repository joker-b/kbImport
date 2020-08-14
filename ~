#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
"""

import os
import sys

if sys.version_info < (3,):
  print("sorry, python3 required")
  sys.exit()


from ArchDB import *

def get_available_source_folder():
  'look for avaiilable source drives'
  root = '/Volumes'
  if not os.path.exists(root):
    root = '/mnt/chromeos/removeable'
  possible = [os.path.join(root, f) for f in [
      'pix20s/kbImport/Pix/',
      'pix18/kbImport/Pix/',
      'KBWIFI/kbImport/Pix/',
      'pix18/Pix/',
      'pix17/Pix/',
      'pix15/Pix/',
      'pix20/Pix/',
      'Sept2013/Pix/',
      'CameraWork/Pix/' ] ]
  possible.append('/home/kevinbjorke/pix/kbImport/Pix')
  possible.append('/Users/kevinbjorke/Pictures/kbImport/Pix/')
  possible.append('/Users/kevinbjorke/Google Drive/kbImport/Pix/')
  for f2 in possible:
    if os.path.exists(f2):
      return f2
  return '.' # less-awkward fail


def validate(DBFile='L8.pkl', ArchDir=None):
  'remember to assign when testing interactively!'
  # test_db = ArchDB()
  dest = ArchImgFile.dest(ArchDir)
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  test_db.describe()
  print('\nVerifying archive at {}:'.format(dest))
  missing = test_db.exists_at(dest)
  print("Identified {} unarchived records, such as:".format(len((missing))))
  print(missing[:3])
  f = open('missing_files.log', 'w')
  for m in missing:
    f.write(m)
  f.close()
  print('logged names')
  return test_db

def update_from_available_drives(SrcDBFile='L8.pkl',
                                 SrcFolder=None,
                                 ArchDir=None,
                                 DestDBFile=None):
  # test_db = ArchDB()
  test_db = ArchDB.load(SrcDBFile)
  if SrcFolder is None:
    test_folder = get_available_source_folder()
  else:
    test_folder = SrcFolder
  dest = ArchImgFile.dest(ArchDir)
  ArchImgFile.pretend(False)
  print("Add from folder: {}".format(test_folder))
  print("Destingation: {}".format(dest))
  nf = test_db.add_folder(test_folder)
  print('Added {} new files'.format(nf))
  # test_db.describe()
  test_db.dop_hunt()
  test_db.archive_to(dest)
  if DestDBFile is None:
    updated_db = SrcDBFile
  else:
    updated_db = DestDBFile
  ArchDB.save(test_db, updated_db)
  ArchDB.describe_created_dirs()

def mini_validate(DBFile='L8.pkl', ArchDir=None):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  dest = ArchImgFile.dest(ArchDir)
  # test_db.describe()
  for iid in ['DSCF5603', 'P1090125', 'KBXP1022', 'KBXP1023', 'bjorke_Cuba_XT1A5922', 'KEVT2922']:
    print('-------- {} ---------'.format(iid))
    ar = test_db.archRecs[iid]
    ar.print_arch_status2(dest)
  return test_db

def find_unknowns(DBFile='L8.pkl'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  print('found {} unknown files'.format(test_db.count_unknowns()))
  return test_db

def find_archived_unknowns(DBFile='L8.pkl', ArchDir=None):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  dest = ArchImgFile.dest(ArchDir)
  print('found {} archived unknown files'.format(test_db.find_archived_unknowns('unknowns.log', dest)))
  return test_db

def find_unarchived_raws(DBFile='L8.pkl', ArchDir=None):
  # 531  sed -e 's/.*# //' -e 's/ .*//' unarchived-raw.log | sort | uniq -c
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  dest = ArchImgFile.dest(ArchDir)
  print('found {} archived unknown files'.format(test_db.find_unarchived_raw('unarchived-raw.log', dest)))
  return test_db

def reconcile_misfiled(DBFile='L8.pkl', DestFile=None):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  test_db.reconcile_misfiled()
  if DestFile is not None:
    ArchDB.save(test_db, DestFile)
  return test_db

def complex_records(DBFile='L8.pkl', RecName='DSCF4743'):
  test_db = ArchDB.load(DBFile)
  for RecName in [ 'DSCF4743', 'KEVT2897', 'DSCF5754']:
    print("--------   {} --------".format(RecName))
    ar = test_db.archRecs[RecName]
    ar.print_stats()
  return ar

if __name__ == '__main__':
  # mini_validate()
  # find_unknowns()
  # find_archived_unknowns('L8.pkl')
  # complex_records('L8.pkl')
  #find_unarchived_raws('L8.pkl')
  # reconcile_misfiled('L8.pkl', 'L8.pkl')
  update_from_available_drives('L8.pkl', None, None)
  # sys.exit()
