#!/usr/bin/env python

# author: Chuck King
# https://github.com/cwkingjr/silk-data-available
# date: 2012-07-30
# license: GPLv3, see license file
# purpose: Figure out what silk data is on line by class/type/date-range
# note: expects a specific silk record file path format of 
# /datadir/class/type/year/month/day/hour_files.

import optparse
import os
import sys
import re

datadir = "/data"
silkconf = "%s/silk.conf" % datadir

# list to manage available classes seen in silk.conf
classes = []

# collections to track classtypes and first and last seen datetimes
classtypes = []
classtypefirst = {}
classtypelast  = {}

# precompiled regex pattern
# silk files end in YYYYMMDD format
patternfilename = re.compile("\d{8}\.\d{2}$")

def processOptions():
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)
    parser.add_option("-q",
                      "--quiet",
                      action="store_true",
                      dest="quiet",
                      help="Optional. Drop some info printing while processing.")
    parser.add_option("-c",
                      "--silkclass",
                      dest="silkclass",
                      help="Optional. Single class name you want to check.")
    parser.add_option("-d",
                      "--dryrun",
                      action="store_true",
                      dest="dryrun",
                      help="Optional. Just show classes we will/will not use and exit.")
    parser.add_option("-p",
                      "--datapath",
                      dest="datapath",
                      help="Optional. Silk data parent directory (default = /data).")
    parser.add_option("-v",
                      "--verbose",
                      action="store_true",
                      dest="verbose",
                      help="Optional. Verbose adds a few extra processing print statements.")

    (options,args) = parser.parse_args()
    return (options,args)

(options, args) = processOptions()

if options.datapath:
    datadir = options.datapath
    silkconf = "%s/silk.conf" % datadir
if options.verbose:
    print "[INFO] Using %s as the data parent directory\n" % datadir
    print "[INFO] Using %s as the silk.conf path\n" % silkconf

# open the silkconf file using file handle 
try:
    fh = open(silkconf,"r")
except IOError, argument:
    print "IOError",argument
    sys.exit()

# parse the silk.conf file to determine all possible classes
for line in fh:
    if re.match("class",line):
        # example line:class isr
        # grab the class name after the config file "class" designator
        myclassline = re.split(" ",line)
        myclassname = myclassline[1].strip()
        # add class to the potential deployed classes list
        classes.append(myclassname)

if options.silkclass:
    dirs = [options.silkclass]
else:
    # grab a list of the directories at the datadir variable location
    dirs = [dirname for dirname in os.listdir(datadir) if os.path.isdir(os.path.join(datadir,dirname))] 

# keep a list of only the directories that are also in the classes list
classdirs = [dirname for dirname in dirs if dirname in classes]
# keep a list of only the directories that are not also in the classes list
notusing  = [dirname for dirname in dirs if dirname not in classes]

if not options.quiet:
    # let user know about directires that will not be traversed and why
    if not options.silkclass:
        print "[INFO] Found these directories, not in the silk.conf as class, so not using: \n"
        for dir in sorted(notusing):
            print "%s" % dir,
        print "\n"
    else:
        print "[INFO] Not looking for classes found in silk.conf due to using silkclass option\n"

if not options.quiet:
    if not options.silkclass:
        # let user know what directories will be traversed
        print "[INFO] Found and using class dirs named:\n"
        for name in sorted(classdirs):
            print "%s" % name,
        print "\n"
    else:
        print "[INFO] Only looking for info on silkclass option: %s\n" % options.silkclass

if options.dryrun:
    print "[INFO] Exiting due to --dryrun option\n"
    sys.exit()

# walk the dir structure in a way that will keep looking down the tree starting with the oldest directory path
def getoldestfileinfo(mydatadir,myclass,mytype):
    mypath = "%s/%s/%s/" % (mydatadir,myclass,mytype)
    years = [name for name in os.listdir(mypath) if os.path.isdir(os.path.join(mypath,name))]
    for myyear in sorted(years):
        mypathyear = "%s/%s" % (mypath,myyear)
        months = [str(name) for name in os.listdir(mypathyear) if os.path.isdir(os.path.join(mypathyear,name))]
        for mymonth in sorted(months):
            mypathmonth = "%s/%s" % (mypathyear,mymonth)
            days = [str(name) for name in os.listdir(mypathmonth) if os.path.isdir(os.path.join(mypathmonth,name))]
            for myday in sorted(days):
                mypathdays = "%s/%s" % (mypathmonth,myday)
                files = [name for name in os.listdir(mypathdays) if os.path.isfile(os.path.join(mypathdays,name))]
                # if we have some files
                if len(files) > 0:
                    # check each file to see if we can find one that matches a flow file format
                    # if we find one, consider this folder as good and quite checking
                    # if not, keep walking the nested date lists until we do
                    for filename in files:
                        if patternfilename.search(filename):
                            # use this folder
                            mydate = "%s-%s-%s" % (myyear,mymonth,myday)
                            mykey = "%s|%s" % (myclass,mytype)
                            classtypefirst[mykey] = mydate 
                            if not options.quiet:
                                print "[INFO] Chose %s as oldest date for %s %s\n" % (mydate,myclass,mytype)
                            return
                    
# see section above for comments as this section is almost a duplicate, but using different
# sorting to walk the the directories in reverse order
def getnewestfileinfo(mydatadir,myclass,mytype):
    mypath = "%s/%s/%s" % (mydatadir,myclass,mytype)
    years = [name for name in os.listdir(mypath) if os.path.isdir(os.path.join(mypath,name))]
    for myyear in reversed(sorted(years)):
        mypathyear = "%s/%s" % (mypath,myyear)
        months = [str(name) for name in os.listdir(mypathyear) if os.path.isdir(os.path.join(mypathyear,name))]
        for mymonth in reversed(sorted(months)):
            mypathmonth = "%s/%s" % (mypathyear,mymonth)
            days = [str(name) for name in os.listdir(mypathmonth) if os.path.isdir(os.path.join(mypathmonth,name))]
            for myday in reversed(sorted(days)):
                mypathdays = "%s/%s" % (mypathmonth,myday)
                files = [name for name in os.listdir(mypathdays) if os.path.isfile(os.path.join(mypathdays,name))]
                if len(files) > 0:
                    for filename in files:
                        if patternfilename.search(filename):
                            mydate = "%s-%s-%s" % (myyear,mymonth,myday)
                            mykey = "%s|%s" % (myclass,mytype)
                            classtypelast[mykey] = mydate 
                            if not options.quiet:
                                print "[INFO] Chose %s as newest date for %s %s\n" % (mydate,myclass,mytype)
                            return

# iterate over each class dir and launch the old and new checks for each possible class and type
for myclass in classdirs:
    mypath = "%s/%s" % (datadir,myclass)
    # the class types are included as directory names just under each class dir
    types = [name for name in os.listdir(mypath) if os.path.isdir(os.path.join(mypath,name))] 
    # find the oldest and newest dates for each class type
    for mytype in types:
        if options.verbose:
            print "[INFO] Starting search for oldest & newest data files for class: %s, type: %s\n" % (myclass,mytype)
        classtype = "%s|%s" % (myclass,mytype) 
        # keep track of all class/types so we can print them in sorted order later
        if classtype not in classtypes:
            classtypes.append(classtype)
        # find the oldest date with files
        getoldestfileinfo(datadir,myclass,mytype)
        # find the newest date with files
        getnewestfileinfo(datadir,myclass,mytype)


# print header
print "CLASS|TYPE|FROM > TO ('None' indicates no data found)\n"

# iterate over the class types and print out what we found for each
for classtype in sorted(classtypes):
    # get the first value
    if classtype in classtypefirst:
        first = classtypefirst[classtype]
    else:
        first = 'None'

    # get the last value
    if classtype in classtypelast:
        last = classtypelast[classtype]
    else:
        last = 'None'

    # print the results
    print "%s|%s > %s\n" % (classtype,str(first),str(last))
