#! /usr/bin/python3

import sys
import time

if sys.version_info > (3,):
  long = int

def now():
    # return time.process_time() if sys.version_info > (3, 3)  else time.clock()
    return time.perf_counter() if sys.version_info > (3, 3)  else time.clock()

class PerfMon(object):
  "keep track of time"

  def __init__(self):
    self.start()
    self.endTime = self.startTime
    self.elapsed = 0

  def start(self):
    self.startTime = now()

  def halt(self):
    self.endTime = now()
    self.elapsed = self.endTime - self.startTime

  def report_elapsed(self):
    if self.elapsed > 100:
      print("{} minutes elapsed".format(self.elapsed/60))
    else:
      print("{} seconds elapsed".format(self.elapsed))

  def report_throughput(self, nBytes=long(0)):
    throughput = nBytes / self.elapsed
    throughput /= (1024.*1024.) # to megabytes
    print("Estimated performance: {} Mb/sec".format(throughput))

#####

if __name__ == '__main__':
  print("PerfMon testing time")
  v = PerfMon()
  #print("Started: {}".format(v.startTime))
  time.sleep(0.3)
  v.halt()
  v.report_elapsed()
  v.report_throughput(1024*1024) # one mb
