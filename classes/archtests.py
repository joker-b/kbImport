#! /bin/python
"""
Each ImgInfo object contains archive data about a single image
"""

from ArchDB import *

def get_test_pic():
  return '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-05-May/2020_05_31_BLM/bjorke_BLM_KBXF8642.RAF'

def get_test_folder():
  # f2 = '/home/kevinbjorke/pix/kbImport/Pix/'
  # f2 = '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun'
  for f2 in [
      '/home/kevinbjorke/pix/kbImport/Pix',
      # '/home/kevinbjorke/pix/kbImport/Pix/2020/2020-06-Jun/2020_06_06_WoodX/',
      '/Volumes/pix20s/kbImport/Pix/',
      '/Volumes/pix18/kbImport/Pix/',
      '/Volumes/pix18/Pix/',
      '/Volumes/pix17/Pix/',
      '/Volumes/pix15/Pix/',
      '/Volumes/pix20/Pix/',
      '/Volumes/Sept2013/Pix/',
      # '/Users/kevinbjorke/Pictures/kbImport/Pix/2020/2020-01-Jan/2020_01_02_Putnam/',
      # '/Users/kevinbjorke/Pictures/kbImport/Pix/',
      #'/Users/kevinbjorke/Google Drive/kbImport/Pix/',
      '/Volumes/CameraWork/Pix/']:
    if os.path.exists(f2):
      return f2
  return '.' # less-awkward fail


def validate(DBFile='L4.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  'remember to assign when testing interactively!'
  # test_db = ArchDB()
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  test_db.describe()
  print('\nVerifying archive at {}:'.format(ArchDir))
  missing = test_db.exists_at(ArchDir)
  print("Identified {} unarchived records, such as:".format(len((missing))))
  print(missing[:3])
  f = open('missing_files.log', 'w')
  for m in missing:
    f.write(m)
  f.close()
  print('logged names')
  return test_db

def update_from_available_drives(SrcDBFile='L4.pkl', SrcFolder=None,
                                 ArchDir='/Volumes/Legacy20/Pix', DestDBFile=None):
  # test_db = ArchDB()
  test_db = ArchDB.load(SrcDBFile)
  # test_pic = get_test_pic()
  if SrcFolder is None:
    test_folder = get_test_folder()
  else:
    test_folder = SrcFolder
  ArchImgFile.pretend(False)
  print("Add test folder: {}".format(test_folder))
  nf = test_db.add_folder(test_folder)
  print('Added {} new files'.format(nf))
  test_db.describe()
  test_db.dop_hunt()
  test_db.archive_to(ArchDir)
  if DestDBFile is None:
    updated_db = SrcDBFile
  else:
    updated_db = DestDBFile
  ArchDB.save(test_db, updated_db)
  ArchDB.describe_created_dirs()

def mini_validate(DBFile='L4.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  # test_db.describe()
  for iid in ['DSCF5603', 'P1090125', 'KBXP1022', 'KBXP1023', 'bjorke_Cuba_XT1A5922', 'KEVT2922']:
    print('-------- {} ---------'.format(iid))
    ar = test_db.archRecs[iid]
    ar.print_arch_status2(ArchDir)
  return test_db

def find_unknowns(DBFile='L4.pkl'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  print('found {} unknown files'.format(test_db.count_unknowns()))
  return test_db

def find_archived_unknowns(DBFile='L4.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  print('found {} archived unknown files'.format(test_db.find_archived_unknowns('unknowns.log', ArchDir)))
  return test_db

def find_unarchived_raws(DBFile='L4.pkl', ArchDir='/Volumes/Legacy20/Pix'):
  test_db = ArchDB.load(DBFile)
  if test_db is None:
    print("sorry")
    return None
  print('found {} archived unknown files'.format(test_db.find_unarchived_raw('unarchived-raw.log', ArchDir)))
  return test_db

def complex_records(DBFile='L4.pkl', RecName='DSCF4743'):
  ''''
  others: KEVT2897 DSCF5754
  /Volumes/Legacy20/Pix/2004/300D/2004-04-April/2004_04_24/175_7515.CRW
  /Volumes/Legacy20/Pix/2003/300D/2003-11-Nov/2003_11_16-London/VSMD0052.CRW
  /Volumes/Legacy20/Pix/2006/Digi/2006_08/2006_08_07-Negs/534_3470.DNG
  /Volumes/Legacy20/Pix/2007/Reb/2007_07_29/647CANON/CRW_4704.CRW
  /Volumes/Legacy20/Pix/2007/Reb/2007_07_29/647CANON/CRW_4744.CRW
/Volumes/Legacy20/Pix/2011/2011-03-Mar/2011_03_09/P1000016_1.dng
/Volumes/Legacy20/Pix/2011/2011-03-Mar/2011_03_09_LX5/test.dng
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_24_City/JOKR9972.RAF
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_26_CityIsaac/f10590080.raf
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_26_CityIsaac/f11696064.raf
/Volumes/Legacy20/Pix/2014/2014-09-Sep/2014_09_26_CityIsaac/f8935744.raf
/Volumes/Legacy20/Pix/2014/2014-10-Oct/2014_10_08_Pizza/PICS0750.RAF
/Volumes/Legacy20/Pix/2015/2015-09-Sep/2015_09_06_FineArts/bjorke_FineArts_P1080536.DNG
/Volumes/Legacy20/Pix/2006/Digi/2006_06/2006_06_24-hockey/502_0282.DNG
/Volumes/Legacy20/Pix/2006/Digi/2006_06/2006_06_26_slapPractice/502_0298.DNG
  '''
  test_db = ArchDB.load(DBFile)
  for RecName in [ 'DSCF4743', 'KEVT2897', 'DSCF5754']:
    print("--------   {} --------".format(RecName))
    ar = test_db.archRecs[RecName]
    ar.print_stats()
  return ar
  # problem archive: DSCF4743.RAF - multiple camera versions!


if __name__ == '__main__':
  # mini_validate()
  # find_unknowns()
  # find_archived_unknowns('L4.pkl')
  complex_records('L4.pkl')
  # find_unarchived_raws('L4.pkl')
  #update_from_available_drives('L4.pkl', '/Volumes/Drobo/Pix',
  #            '/Volumes/Legacy20/Pix', 'L4.pkl')
  # sys.exit()
  # update_from_available_drives()
