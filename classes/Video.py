#! /usr/bin/python3

import re

class Video(object):
  "file type services relating to video"
  regexVidFiles = re.compile(r'\.(M4V|MP4|MOV|3GP)') # TODO(kevin): ignore case?
  def __init__(self):
    pass
  @classmethod
  def has_filetype(cls, Filename):
    return cls.regexVidFiles.search(Filename) is not None

if __name__ == '__main__':
  print("Video testing time")
  v = Video()
  print(Video.has_filetype('thing.mov'))
  print(Video.has_filetype('thing.MOV'))
