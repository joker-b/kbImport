#
# search for directories containing a named substring within kbImport-style hierarchies
#
# it's possible that just using 'find' would be faster, but this script is more flexible
# and can be used to search for multiple substrings at once
#
# usage: reca-find.py [options] <search-string> <root-dir>

# kbImport directory structure:
# root-dir/
#   Pix/ or Vid/
#     YYYY/
#       YYYY-MM-Mon/
#         YYYY_MM_DD-Job/

# we are searching for substrings in the "Job" part of the directory name

import os
import sys
import re
import argparse

def find_substring(search_string, root_dir):
    counter = 1
    good = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            counter += 1
            if search_string in dirname:
                good += 1
                print(os.path.join(dirpath, dirname))
    print(f'Found {good} out of {counter} dirs, searching for "{search_string}" in "{root_dir}"')

def find_any_substring(search_terms, root_dir):
    counter = 1
    good = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            counter += 1
            for search_string in search_terms:
                if search_string in dirname:
                    good += 1
                    print(os.path.join(dirpath, dirname))
                    break # don't get redundant names
    print(f'Found {good} out of {counter} dirs, searching for "{len(search_terms)}" items in "{root_dir}"')
    return good, counter

def singlemain():
    parser = argparse.ArgumentParser(description='Search for directories containing a named substring within kbImport-style hierarchies')
    parser.add_argument('search_string', help='substring to search for')
    parser.add_argument('root_dir', help='root directory to search in')
    args = parser.parse_args()

    find_substring(args.search_string, args.root_dir)

def main():
    terms = ['RECA', 'Reca', 'Dance', 'Zhuo', 'Fair', 'CCamp', 'EarthDay', 'Rave', 'SSU', 'CNY', 'Yin', 'Lion']
    volumes = ['/Volumes/ePix/kbPix', '/Volumes/kbPix/']
    allGood = 0
    allSearched = 0
    for vol in volumes:
        print(f'----- {vol} -----')
        g, c = find_any_substring(terms, vol)
        allGood += g
        allSearched += c
    print(f'Found {allGood} out of {allSearched} dirs, searching for "{len(terms)}" items in all volumes')
    # for term in terms:
    #     print(f'----- {term} -----')
    #    for vol in volumes:
    #        find_substring(term, vol)

main()
