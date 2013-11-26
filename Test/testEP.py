#!/usr/bin/env python

#
# LICENSE:
# This program is free software; you can redistribute it and/or modify it 
# under the terms of the GNU Affero General Public License version 3 (AGPL) 
# as published by the Free Software Foundation.
# (c) 2010-2013 caregraf
#

"""
Do EP tests that match the stand-alone QP tests: use delegator
so same tests will work with both (better).
"""

import json
import urllib
import urllib2
try:
    import simplejson as json # faster
except ImportError:
    import json
import time
from datetime import datetime

FMQLEP = "http://www.examplehospital.com/fmqlEP"

def simpleEPTests():
    start = datetime.now()
    bquery = {"nada": "nah"}
    queryURL = FMQLEP + "?" + urllib.urlencode(bquery)
    reply = urllib2.urlopen(queryURL).read()
    print reply
    queries = ["DESCRIBE 2-1", "COUNT REFS 2-9", "DESCRIBE 2", "SELECT 2", "COUNT 2", "DESCRIBE 2_0361 IN 2-3", "SELECT 2 LIMIT 3 OFFSET 1", "SELECT 2 FIELD .01 LIMIT 3", "DESCRIBE 79_3 FILTER(.03=2-1)", "COUNT 50_68 FILTER(.05=11-2) NOIDXMAX 1", "BADQUERY"]
    output = "json"
    for query in queries:
        print "=========================================================="
        print query
        queryURL = FMQLEP + "?" + urllib.urlencode({"fmql": query, "output": output})
        reply = urllib2.urlopen(queryURL).read()
        print reply
        if output == "json":
            json.loads(reply)
    oqueries = ["SELECT TYPES TOPONLY", "SELECT TYPES", "DESCRIBE TYPE 2", "SELECT TYPE REFS 2", "BADOP"]
    for oquery in oqueries:
        print "=========================================================="
        print oquery
        queryURL = FMQLEP + "?" + urllib.urlencode({"fmql": oquery, "output": output})
        reply = urllib2.urlopen(queryURL).read()
        print reply
        if output == "json":
            json.loads(reply)
    end = datetime.now()
    delta = end-start
    print "... test took: %s" % (delta)

simpleEPTests()
