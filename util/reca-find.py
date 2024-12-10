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
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            if search_string in dirname:
                print(os.path.join(dirpath, dirname))

def main():
    parser = argparse.ArgumentParser(description='Search for directories containing a named substring within kbImport-style hierarchies')
    parser.add_argument('search_string', help='substring to search for')
    parser.add_argument('root_dir', help='root directory to search in')
    args = parser.parse_args()

    find_substring(args.search_string, args.root_dir)
