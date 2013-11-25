#!/usr/bin/env python

#
# LICENSE:
# This program is free software; you can redistribute it and/or modify it 
# under the terms of the GNU Affero General Public License version 3 (AGPL) 
# as published by the Free Software Foundation.
# (c) 2010-2013 caregraf
#

import sys, os
import json
import urllib, urllib2
import getopt
import traceback
import time
from datetime import datetime
import cgi
import re

sys.path.append('../Framework')
from fmqlQP import FMQLQP
from brokerRPC import VistARPCConnection

"""
 FMQL Query Processor Unit Tests

 Two sorts of test:
 - generic: no assertions particular to a system (count patients)
 - system specific: assertions specific to a system (number of patients is 50000)
 
 To run the system specific tests on your system, you must change
 the constants set at the beginning of the system test section.

 Note: these tests run directly against the FMQL RPC and not the Apache
 resident endpoint.
"""

#
# FMQL Tests [Configure for specific system after first system-only run]
#

SYSTEMONLY = False # Change once system specific numbers below are set

def runTest(rpcc, testGroupName, testId, testDef):
    print "========= Test %s: %s ========" % (testGroupName, testId)
    print testDef["description"]
    start = datetime.now()
    try: 
        reply = rpcc.invokeRPC("CG FMQL QP", [testDef["fmql"]])
        end = datetime.now()
        delta = end-start
        jreply = json.loads(reply)
        end = datetime.now()
        jdelta = end-start
        print "... test took: %s/%s" % (delta, jdelta)
    except Exception as e:
        traceback.print_stack()
        print "ERROR: %s" % e
        print "REPLY", reply
        return 0
    if "error" in testDef:
        if "error" in jreply:
            print "Received Expected Error %s" % str(jreply["error"])
            print "PASSED"
            return 1
        print jreply
        print "ERROR"
        return 0
    if "dump" in testDef:
        print jreply
    if "count" in testDef:
        fmqlCount = "-1"
        if "count" in jreply:
            fmqlCount = jreply["count"]
        elif "total" in jreply:
            fmqlCount = jreply["total"]
        elif "results" in jreply:
            fmqlCount = str(len(jreply["results"]))
        if SYSTEMONLY or testDef["count"] == "PRINT":
            # print jreply
            print "Got count of %s" % fmqlCount
        elif "error" in jreply or fmqlCount != testDef["count"]:
            print jreply
            print "ERROR: COUNT %s doesn't match returned count %s!" % (testDef["count"], fmqlCount)
            return 0
    if "test" in testDef and not SYSTEMONLY:
        try:
            exec testDef["test"]
        except Exception as e:
            testResult = False
            print "Test failed to execute. Reply has unexpected form"
            print e
        if testResult:
            print "PASSED"
            return 1
        print "ERROR"
        return 0
    print "PASSED"
    return 1
    
# Utility to make testing DESCRIBE TYPE easy - comes back as array
def schemaField(jreply, fieldNumber):
    for fieldInfo in jreply["fields"]:
        if fieldInfo["number"] == fieldNumber:
            return fieldInfo
    return None
    
TESTSETS = []

# ####################### Generic/Cross System #############
#
# Tests on basic FMQL that don't depend on System content.
# Will print some counts to allow system specific tests to
# be configured
#

# Generic (Schema etc tests)
GENERICTESTS = {
    "name": "BASIC",
    "definitions": [
        {   
            "description": "Schema: Select Types",
            "fmql": "SELECT TYPES",
        },
        {
            "description": "Schema: DescribeType 2",
            "fmql": "DESCRIBE TYPE 2",
        },
        {
            "description": "Schema: Select Type Refs 2",
            "fmql": "SELECT TYPE REFS 2",
        },
        {
            "description": "Count Patients",
            "fmql": "COUNT 2",
            "count": "PRINT",
        },
        {
            "description": "Count orders",
            "fmql": "COUNT 100",
            "count": "PRINT",
        },
        {
            "description": "Count labs",
            "fmql": "COUNT 63",
            "count": "PRINT",
        },
    ]
}

TESTSETS.append(GENERICTESTS)

# Add:
# - invalid pointer in filter (.01=X and not X-Y)
NEGATIVETESTS = {
    "name": "NEGATIVETESTS - always invalid queries",
    "definitions": [
        {
            "description": "Select: Bad file",
            "fmql": "SELECT 999999999999999999",
            "error": ""
        },
        # Note: not doing typeId only to Describe as QP catches that.
        {
            "description": "Describe: Good file, bad ID",
            "fmql": "DESCRIBE 2-99999999999999999",
            "error": ""
        },
        { 
            "description": "Describe: Good file, 0 (bad) ID (0 can be tricky as it is in the array - as meta data)",
            "fmql": "DESCRIBE 2-0",
            "error": ""
        },
        {
            "description": "Describe: Bad file, bad ID",
            "fmql": "DESCRIBE 999999999999999999-99999999999999999",
            "error": ""
        },
        { 
            "description": "COUNT REFS: Good file, bad ID",
            "fmql": "COUNT REFS %s" % "2-99999999999999999",
            "error": ""
        },
        {
            "description": "COUNT REFS: Bad file, bad ID",
            "fmql": "COUNT REFS %s" % "9999999999999999-99999999999999999",
            "error": ""
        },
        {
            "description": "Select: BNode file",
            "fmql": "SELECT 63_04",
            "error": ""
        },
        {
            "description": "DescribeType: Bad file",
            "fmql": "DESCRIBE TYPE 9999999999999999",
            "error": ""
        },
        {
            "description": "Select Type Refs: Bad file",
            "fmql": "SELECT TYPE REFS 9999999999999999",
            "error": ""
        },
        {
            "description": "Select Type Refs: BNode file",
            "fmql": "SELECT TYPE REFS 63_04",
            "error": ""
        },
    ]
}

TESTSETS.append(NEGATIVETESTS)

########################## System Specifics ################

STESTSETS = []

# Set the following per test system
CNT_PATIENTS = "39"
CNT_ORDERS = "6"
CNT_LABS = "22"
TESTPATIENTID = "2-9"
TESTIHSPATIENTID = "9000001-9"
TESTOPATIENTID = "2-6" # Order patient different in CG Demo
CNT_CHLAB="19" # no of CH labs of test patient (was 38!)
CHLAB_URIFORMAT = "^63_04\-[^_]+_\d+$"
CNT_VITALSOFTP = "290" # no of vitals of test patient
CNT_VITALSOFTPNEIE="260" # Not entered in error
CNT_VITALSFROM2008ON="104" # Vitals from 2008 on
CNT_HVITALSOFTPNEIE="12" # Height Vitals of patient
CNT_ORDERSOFOTP = "5"
CNT_ACCESSIONS = "15"
CNT_REFS = "1116"
BADSCHEMANOFILE = "1_01"
BADSCHEMA01FILE = "627_99" # File with bad schema for its .01 field
MUMPSCODETESTID = "68-11"
MUMPSCODETEST="(re.match(r'I \$P\(\^LRO\(68,LRAA,1,LRAD,1,LRAN,0\),U,2\)=62.3 S LRTEST=\"\" D \^LRMRSHRT', jreply['results'][0]['ver_code']['value']))"
CTRLUDR32TESTID="3_075-60698"
# Escape Decimal 27 == u'\x1b'
CTRLUDR32TEST="re.search(r'\x1b', jreply['results'][0]['error_number']['value'][1]['variables_and_data']['value'][88]['data_value']['value'])"
NODEWITHSUCNODES="63-4"
CNODEFIELD="chem_hem_tox_ria_ser_etc"
TESTPROBLEMDIAGNOSIS="80-62"

# TODO: upgrade to test if FMQL response has BADTOO:true etc
# TODO: add for FILE=.109 ; allow .11 on but no .001 -> .1
TESTSCHEMATESTS = {
    "name": "SELECT TYPES in all its forms",
    "definitions": [
        {
            "description": "SELECT TYPES - no args (all good, no bad)",
            "fmql": "SELECT TYPES", 
            "count": "5393",
        },
        {
            "description": "SELECT TYPES TOPONLY",
            "fmql": "SELECT TYPES TOPONLY",
            "count": "2359"
        },
        {
            "description": "DESCRIBE BADTYPES",
            "fmql": "DESCRIBE BADTYPES",
            "count": "49",
            "test": "testResult=(len(jreply['results']) == int(jreply['badCount']))" 
        },
        {
            "description": "SELECT TYPES POPONLY",
            "fmql": "SELECT TYPES POPONLY",
            "count": "1245"
        }
    ]
}

STESTSETS.append(TESTSCHEMATESTS)

# OTHERS TO ADD:
# - 80_3-2 ... MUMPS (6) is .01 value. Seems to show properly
# - typeID: ["9002313.55"] has BAD IEN (1VA) in my system. I skip it properly ie. no entries show.

TESTPATIENTTESTS = {
    "name": "Ramble Test Patient %s" % TESTPATIENTID,
    "definitions": [
        {
            "description": "Describe %s" % TESTPATIENTID,
            "fmql": "DESCRIBE " + TESTPATIENTID, 
        },
        {
            "description": "COUNT REFS to %s" % TESTPATIENTID,
            "fmql": "COUNT REFS %s" % TESTPATIENTID,
            "count": CNT_REFS,
        },
    ]
}

STESTSETS.append(TESTPATIENTTESTS)

# Special case: "B" index 2 and 68 overloaded with alias names
# 68 has "SEND","SEND OUT" for same record in B index. Only exercised with >
# as it forces full walk of B
PATIENTALIASTEST = {
    "name": "Ensure don't count aliases of 'B'",
    "definitions": [
        {
            "description": "Patient Alias should be skipped",
            "fmql": "SELECT 68 FILTER(.01>R)",
            "count": "4"
        }
    ]
}

STESTSETS.append(PATIENTALIASTEST)

# TBD: BNode included or not for count and bnode count.
# TBD: test BNode count stuff to confirm ... (limitation of Describe where BNodes are
# really first class entries, not scoped in any meaningful way) [A Schema Viewpoint]
# - RPMS: [MOST] 90213 (BDW Warehouse Export), 9002274_45, [MID] 50_8, 
#   9009016_2, 90536_03, 90057, 9009011
# - and 68, Accession too (in MMH too)
# Testing empties too
CNODETESTS = {
    "name": "CNODE",
    "definitions": [
        {
            "description": "Describe all CHEM in 63 - count em",
            "fmql": "DESCRIBE 63_04 IN 63-4",
            "count": CNT_CHLAB
        },
        {
            "description": "Count all CHEM in 63",
            "fmql": "COUNT 63_04 IN 63-4",
            "count": CNT_CHLAB
        },
        {
            "description": "Select all CHEM in 63 - count em",
            "fmql": "SELECT 63_04 IN 63-4",
            "count": CNT_CHLAB
        },
        { # Note: in my test system, chvals is empty
            "description": "Describe all CHEM in 63 - ensure Lab BNode generation works",
            "fmql": "DESCRIBE 63_04 IN 63-4",
            "test": "testResult=('chvals' in jreply['results'][0])"
        },
        {
            "description": "Select All CHEM in 63 - ensure URI format is 'right'",
            "fmql": "SELECT 63_04 IN 63-4",
            "test": "testResult=re.search(r'%s', jreply['results'][0]['uri']['value'])" % CHLAB_URIFORMAT,
        },
        {
            "description": "Count CHEM in 63, Offset %d" % (int(CNT_CHLAB)-9),
            "fmql": "COUNT 63_04 IN 63-4 OFFSET " + str(int(CNT_CHLAB)-9),
            "count": str(int(CNT_CHLAB)-10)
        },
        {
            "description": "Select CHEM in 63, Limit 10",
            "fmql": "SELECT 63_04 IN 63-4 LIMIT 10",
            "count": "10"
        },
        {
            "description": "Select 2_141 - expect 0",
            "fmql": "SELECT 2_141 IN " + TESTPATIENTID,
            "count": "0"
        },
        {
            "description": "Select sub sub node 70_03 - expect error",
            "fmql": "SELECT 70_03 IN 70-1",
            "error": ""
        },
        {
            "description": "Describe a Node (63) without its cnodes",
            "fmql": "DESCRIBE %s CSTOP 0" % NODEWITHSUCNODES,
            "test": "testResult = (jreply['results'][0]['%s'].has_key('stopped'))" % CNODEFIELD
        },
        {
            "description": "Describe a Node (63) without its sub nodes, setting limit = number of subnodes (limit threshold test)",
            "fmql": "DESCRIBE %s CSTOP %s" % (NODEWITHSUCNODES, CNT_CHLAB),
            "test": "testResult = (jreply['results'][0]['%s'].has_key('stopped'))" % CNODEFIELD
        },
        {
            "description": "Describe a Node (63) with its sub nodes",
            "fmql": "DESCRIBE %s CSTOP %s" % (NODEWITHSUCNODES, int(CNT_CHLAB)+1),
            "test": "testResult = ('%s' in jreply['results'][0])" % CNODEFIELD,
        },
        {
            "description": "Describe first 4 Nodes (63) without sub nodes",
            "fmql": "DESCRIBE %s LIMIT 4 CSTOP 0" % re.search(r'([^\-]+)', NODEWITHSUCNODES).group(1),
            # The fourth one has cnodes. The others don't.
            "test": "testResult = (jreply['count'] == '4' and (jreply['results'][3]['%s'].has_key('stopped')))" % CNODEFIELD,
        },
        {
            "description": "Stop/Limit CNode within CNode - recursion test",
            "fmql": "DESCRIBE %s CSTOP 10" % CTRLUDR32TESTID,
            "test": "testResult = ('stopped' in jreply['results'][0]['error_number']['value'][0]['variables_and_data'])"
        },
        {
            "description": "Describe first 2 C Nodes of a Node (63). LIMIT test",
            "fmql": "DESCRIBE 63_04 IN 63-4 LIMIT 2",
            "count": "2"
        },
        {
            "description": "Describe a Node without a CSTOP. 10 (default) is imposed by MUMPS QP",
            "fmql": "DESCRIBE %s" % NODEWITHSUCNODES,
            "test": "testResult = (jreply['fmql']['CSTOP'] == '10')"
        },
        {
            "description": "CNode List Element ie 1 or 3 types - set in cnode field",
            "fmql": "DESCRIBE 120_8-4",
            "test": "testResult = (jreply['results'][0]['drug_classes']['list'] == True)"
        }
    ]
}

STESTSETS.append(CNODETESTS)

# FILTER TESTS
# - TBD: ] test for names
FILTERTESTS = {
    "name": "FILTER",
    "definitions": [
        {
            "description": "All Vitals of Patient 9, not entered in error",
            "fmql": "DESCRIBE 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2))",
            "count": CNT_VITALSOFTPNEIE
        },
        {
            "description": "All Height Vitals of Patient 9, not entered in error",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)&.03=120_51-8)",
            "count": CNT_HVITALSOFTPNEIE
        },
        {
            "description": "All Vitals of Patient 9, from 2008 on",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)&.01>2008-01-01)",
            "count": CNT_VITALSFROM2008ON
        },
        {
            "description": "All Vitals of Patient 9, before 2008",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)&.01<2008-01-01)",
            "count": str(int(CNT_VITALSOFTPNEIE)-int(CNT_VITALSFROM2008ON))
        },
        {
            "description": "First 12 Patients with names beginning with P on",
            "fmql": "SELECT 2 FILTER(.01>P) LIMIT 12",
            "count": "12"
        },
        {
            "description": "Labs with bound CHEM, HEM ie/ top level bound cnode test",
            "fmql": "COUNT 63 FILTER(bound(4))",
            "count": "1" # only 9 has labs
        },
        {
            "description": "Labs without bound CHEM, HEM ie/ top level bound cnode test",
            "fmql": "COUNT 63 FILTER(!bound(4))",
            "count": "21"
        },
        {
            "description": "Contained Node Non VA Meds with route 'MOUTH'",
            "fmql": "SELECT 55_05 IN 55-9 FILTER(3=MOUTH)",
            "count": "6"
        },      
        {
            "description": "Contained Node CHEM, HEM with bound creatinine (4).",
            "fmql": "COUNT 63_04 IN 63-4 FILTER(bound(4))",
            "count": "2"
        },  
        {
            "description": "Contained Node CHEM, HEM before 1/1/2007. TBD [add to triple of all, before and after and carry totals as a variable]",
            "fmql": "COUNT 63_04 IN 63-4 FILTER(.01<'2007-01-01T000000')",
            "count": "15"
        },  
        {
            "description": "Contained Node CHEM, HEM after 1/1/2007. Should be 10",
            "fmql": "COUNT 63_04 IN 63-4 FILTER(.01>'2007-01-01T000000')",
            "count": "4"
        },  
        { # TBD: V0.9 - should raise error
            "description": "Bad filter (no such field) on select patients",
            "fmql": "SELECT 2 FILTER(.999999=X)",
            "count": "0"
        },
        {
            "description": "Month filter: HL7 Exceptions in a month (2005/11)",
            "fmql": "SELECT 79_3 FILTER(.01>2005-11&.01<2005-12)",
            "count": "17"
        },
        {
            "description": "HL7 Exceptions on a day (2005/11/01)",
            "fmql": "SELECT 79_3 FILTER(.01>2005-11&.01<2005-11-02)",
            "count": "14"
        },
        {
            "description": "HL7 Exceptions after an hour of a day (2005/11/01:17))",
            "fmql": "SELECT 79_3 FILTER(.01>2005-11-01T17&.01<2005-11-02)",
            "count": "6"
        },
        {
            "description": "HL7 Exceptions in a year (2005)",
            "fmql": "SELECT 79_3 FILTER(.01>2004&.01<2006)",
            "count": "107"
        },
        {
            "description": "HL7 Exceptions after a precise time (down to seconds)",
            "fmql": "SELECT 79_3 FILTER(.01>2005-11-01T17:46:09)",
            "count": "10"
        },
        {
            "description": "Doc types called BMI, single quote",
            "fmql": "COUNT 8925_1 FILTER(.01='BMI')",
            "count": "1"
        },
        {
            "description": "Doc type History & Physical. It has an embedded &. For pre V0.9, must escape. TBD change",
            "fmql": "COUNT 8925_1 FILTER(.01='HISTORY \& PHYSICAL')",
            "count": "1"
        },
        {
            "description": "Doc type CHF DAY 1 (C) has embedded ('s",
            "fmql": "COUNT 8925_1 FILTER(.01='CHF DAY 1 (C)')",
            "count": "1"
        },
        { 
            "description": "Doc type ALLERGIES/ADR is made _ by FMQL. Need to lookup with /",
            "fmql": "COUNT 8925_1 FILTER(.01='ALLERGIES/ADR')",
            "count": "1"
        },
        {
            "description": "&& test. Make sure can do &&",
            "fmql": "COUNT 8925_1 FILTER(.01='MISC/OTHER SVCS'&&.04='DC')",
            "count": "1"
        },
        {
            "description": "V0.8 & Test. Will go with forced && in V0.9",
            "fmql": "COUNT 8925_1 FILTER(.01='MISC/OTHER SVCS'&.04='DC')",
            "count": "1"
        },
    ]
}

STESTSETS.append(FILTERTESTS)

# LIMIT and OFFSET TESTS (Make Sure Test Patients has Vitals)
LIMITTESTS = {
    "name": "LIMIT/OFFSET",
    "definitions": [
        {
            "description": "Vitals of a Patient, limit 5",
            "fmql": "DESCRIBE 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) LIMIT 5",
            "count": "5"
        },
        {
            "description": "Vitals of a Patient, limit 5, offset 3",
            "fmql": "DESCRIBE 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) LIMIT 5 OFFSET 3",
            "count": "5"
        },
        {
            "description": "Select Vitals of a Patient, offset CNT_VITALSOFTPNEIE - 1 (ie. start one off end)",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) OFFSET " + str(int(CNT_VITALSOFTPNEIE)-1),
            "count": "1"
        },
        {
            "description": "Select Vitals of a Patient, offset 1 past end",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) OFFSET " + str(int(CNT_VITALSOFTPNEIE)+1),
            "count": "0"
        },
        {
            "description": "Count Patients, offset 5",
            "fmql": "COUNT 2 OFFSET 5",
            "count": str(int(CNT_PATIENTS)-5)
        },
        {
            "description": "Select all Patients, offset 3, limit 2",
            "fmql": "SELECT 2 LIMIT 2 OFFSET 3",
            "count": "2"
        },
    ]
}

STESTSETS.append(LIMITTESTS)

# AFTERIEN - alternative to OFFSET 
AFTERIENTESTS = {
    "name": "AFTERIEN",
    "definitions": [
        {
            "description": "Vitals of a Patient, AFTER 6th last IEN",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) AFTERIEN 290",
            "count": "5"
        },
        {
            "description": "Vitals of a Patient, AFTER 6th last IEN, limit 2",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) AFTERIEN 290 LIMIT 2",
            "count": "2"
        },
        {
            "description": "Vitals of a Patient, AFTER 6th last IEN, set OFFSET but expect it to be reset",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) AFTERIEN 290 OFFSET 22",
            "test": "testResult=(jreply['fmql']['OFFSET']=='0')"
        },
        {
            "description": "Vitals of a Patient, AFTER last IEN, expect no entries",
            "fmql": "SELECT 120_5 FILTER(.02=" + TESTPATIENTID + "&!bound(2)) AFTERIEN 295",
            "count": "0"
        },
    ]
}

STESTSETS.append(AFTERIENTESTS)

FORMATTESTS = {
    "name": "Format (date) tests",
    "definitions": [
        {
            "description": "Date with trailing '1' which is rendered as 1, not 01 in FileMan's internal format. Is it flipped in the XML?", 
            "fmql": "DESCRIBE 79_3-14",
            "test": "testResult = (jreply['results'][0]['exception_date_time']['value']=='2005-04-18T08:06:01Z')",
        },
    ]
}

STESTSETS.append(FORMATTESTS)

# No Index Max tests. There is a limit on filtered selects when the filter doesn't assert
# the value of an index.
# 
# Note: TBD: may change definition of no index max so an error is returned.
#
NOIDXMXTESTS = {
    "name": "No Index MX tests",
    "definitions": [
        {
            "description": "No Index Max for patients set to 1 (there are 39). Filter on non indexed field and expect to be rejected", 
            "fmql": "COUNT 50_68 FILTER(.05=11-2) NOIDXMAX 1",
            "count": "-1"
        },
        {
            "description": "No index max for patients set to 1 (there are 39). Filter on name. Expect result of 1 as .01 name is indexed.", 
            "fmql": "COUNT 2 FILTER(.01=AYERS,ASHLEY) NOIDXMAX 1",
            "count": "1"
        },
        {
            "description": "No index max for array kicks in for < filter, even on an idx (won't for follow on > filter ie/ < can't use indexes",
            "fmql": "SELECT 79_3 FILTER(.01<2005-10) NOIDXMAX 10",
            "count": "-1"
        },
        {
            "description": "No index max doesn't matter for indexed > filter. Will pull index",
            "fmql": "SELECT 79_3 FILTER(.01>2005-10) NOIDXMAX 10",
            "test": "testResult= (len(jreply['results']) > 0)"
        },
    ]
}

STESTSETS.append(NOIDXMXTESTS)

# ORDER BY and No B IDX (means can't order) tests
ORDERBYTESTS = {
    "name": "No B Index tests",
    "definitions": [
        {
            "description": "2 with ORDER BY (Z should be last)",
            "fmql": "SELECT 2 ORDERBY .01",
            "test": "testResult = (jreply['results'][len(jreply['results'])-1]['uri']['value']=='2-1')",
        },
        {
            "description": "2 without ORDER BY (Z should be first)",
            "fmql": "SELECT 2",
            "test": "testResult = (jreply['results'][0]['uri']['value']=='2-1')",
        },
        {
            "description": "8985_1 has no simple, inline B Index. It can be listed but the list is in IEN order. Note: ICD Diagnosis 80 has no B Index either!",
            "fmql": "SELECT 8985_1 ORDERBY .01",
            "test": "testResult = (jreply['results'][0]['uri']['value']=='8985_1-1')",
        }
    ]
}

STESTSETS.append(ORDERBYTESTS)

SELECTPREDTESTS = {
    "name": "Select Tests",
    "definitions": [
        {
            "description": "Select patient id for 100 problems",
            "fmql": "SELECT .02 FROM 9000011 LIMIT 10",
            "test": "testResult = (jreply['count']=='10' and 'patient_name' in jreply['results'][0])",
        },
        # TMP
        # {
        #   "description": "Select patients with a diagnosed problem",
        #   "query": {"op": ["Select"], "typeId": ["9000011"], "predicate": [".02"], "filter": [".01=" + TESTPROBLEMDIAGNOSIS]},
        #   "test": "testResult = ('patient_name' in jreply['results'][0] and jreply['results'][0]['patient_name']['value'] == '%s')" % TESTIHSPATIENTID,
        # },
    ]
}

STESTSETS.append(SELECTPREDTESTS)

# Special for Orders (until V0.9)
ORDERTESTS = {
    "name": "ORDERS",
    "definitions": [
        {
            "description": "Select orders, filtered. Test if hard coded filter works by setting noidxmx low",
            "fmql": "SELECT 100 FILTER(.02=" + TESTOPATIENTID + ") NOIDXMAX 1",
            "count": CNT_ORDERSOFOTP
        },
        {
            "description": "Describe orders, filtered. Same as Select but Describe",
            "fmql": "DESCRIBE 100 FILTER(.02=" + TESTOPATIENTID + ")",
            "count": CNT_ORDERSOFOTP
        },
        {
            "description": "Count orders - filtered on non-index, noidxmx low. Should be refused.", 
            "fmql": "COUNT 100 FILTER(1=200-1) NOIDXMAX 1",
            "count": "-1"
        }
    ]
}

STESTSETS.append(ORDERTESTS)

"""
Two Provider Narrative 9999999_27 tests fixed with arrays
until fill arrays in test system. Test where narrative maps
and where it doesn't. By side effect, testing when 757_01 maps
and when it doesn't.

HPTC: problem of many not in kgraf - Osteopath/207P00000X is but many others are not! ... find out range match and range not.

OPEN>S ^AUTNPOV(352,0)="Chronic Fatigue Syndrome^"
OPEN>S ^AUTNPOV(352,757)=304659    

OPEN>S ^AUTNPOV(11,0)="HAIR TOO LONG^" 

OPEN>S SAMEAS("URI")="LOCAL"

OPEN>D RESOLVE9999999dot27^FMQLSSAM(11,.SAMEAS) 

OPEN>ZWR SAMEAS
SAMEAS("URI")="LOCAL"

OPEN>D RESOLVE9999999dot27^FMQLSSAM(352,.SAMEAS)

OPEN>ZWR SAMEAS
SAMEAS("LABEL")="Fatigue Syndrome, Chronic"
SAMEAS("URI")="VA:757-9335"
"""
# SAMEAS Tests
SAMEASTESTS = {
    "name": "SAMEAS",
    "definitions": [
        {
            # TBD: Vital with VUID (1 BP) once added properly
            "description": "VUID FILE: most vitals have VUIDs. Picking Vital (AB Girth 10) with LOCAL only", 
            "fmql": "DESCRIBE 120_51-10",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'LOCAL')",
        },
        {
            # TBD: GMR Allergy with VUID (2 Choc) once added properly
            "description": "VUID FILE: most GMR Allergies have VUIDs. Picking one (Other 1) with LOCAL only", 
            "fmql": "DESCRIBE 120_82-1",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'LOCAL')",
        },
        {
            "description": "ICD (same goes for CPT 81).",
            "fmql": "DESCRIBE 80-1",
            "test": "testResult = (('ICD9CM:' + jreply['results'][0]['code_number']['value']) == jreply['results'][0]['uri']['sameAs'])",
        },
        {
            "description": "Major Concept sameas out",
            "fmql": "DESCRIBE 757-9335",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'VA:757-9335')",
        },
        {
            "description": "Expression to Major Concept",
            "fmql": "DESCRIBE 757_01-304659",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'VA:757-9335')",
        },
        {
            "description": "Provider Narrative with Expression to major concept",
            "fmql": "DESCRIBE 9999999_27-352",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'VA:757-9335')",
        },
        {
            "description": "Provider Narrative with no expression, marked local",
            "fmql": "DESCRIBE 9999999_27-11",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'LOCAL')",
        },        
        {
            "description": "VUID FILE: VA Generic (50_6) has VUID. Same goes for 50_68, 50_416, 50_605",
            "fmql": "DESCRIBE 50_6-95",
            "test": "testResult = (('VA:' + jreply['results'][0]['vuid']['value']) == jreply['results'][0]['uri']['sameAs'])",
        },
        {
            "description": "Drug (50) with map",
            "fmql": "DESCRIBE 50-1",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'VA:4000987')",
        },
        {
            "description": "Drug (50) local only",
            "fmql": "DESCRIBE 50-9",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'LOCAL')",
        },          
        {
            "description": "Pharmacy Orderable (50.7) with map",
            "fmql": "DESCRIBE 50_7-1",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'VA:4000987')",
        },
        {
            "description": "Pharmacy Orderable (50.7) maps to 50 but it is local only so get LOCAL:50-X",
            "fmql": "DESCRIBE 50_7-7",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'LOCAL:50-9')",
        }, 
        #   For these labs manually fixed 60 and 64 as follows:
        #   - S ^LAB(60,5721,64)=666 (WBC)
        #   - S ^LAB(60,5482,64)=1918 and S ^LAM(1918,9)="787^^^^" (MCV)
        {
            "description": "Lab 60 to WKLD 64 and no further",
            "fmql": "DESCRIBE 60-5721", # WBC
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'VA:wkld85030')",
        }, 
        {
            "description": "Lab 60 all the way to LOINC",
            "fmql": "DESCRIBE 60-5482",
            "test": "testResult = (jreply['results'][0]['uri']['sameAs'] == 'LOINC:787-2')",
        }, 
        # Add: 50_7 LOCAL ONLY (ie/ no 50)
        # Add: 71, 790_2 - needs CPT filled. Browse of system with CPT works V0.9
    ]
}

STESTSETS.append(SAMEASTESTS)

#
# NOTE: \x and \u interchange for <255
#
# jdata = {"stuff": "some   other   " + unichr(234)}
# in = json.dumps(jdata)
# ... {"stuff": "some\tother\t\u00ea"} <--- serialized string 
# out = json.loads(in)
# ... {u'stuff': u'some\tother\t\xea'} <--- printed python
# print out["stuff"]==jdata["stuff"]
# ... True
# x = u'\xea' y = u'\u00ea'
# print x==y <-------- down just to the character
# ... True 
# print re.search(r'\xea', y) - matches but re.search(r'\u00ea' doesn't
# as it seems to be treated as a string sequence.
# Go beyond 255 and \x is gone, \u is in.
# print repr(unichr(255)) print repr(unichr(256))
# ... u'\xff' ... u'\u0100'
#
# TBD: more arabic tests ...
# X = "{\"test\": \"\ud8a7\uD984\uD8B3\uD8A7\uD985\uD8A7\uD984\uD987\uD8A7\uD8A8\uD98A\uD984\u01FF\"}"
# are valid unicode (surrogates) but flipped by loads. Need to work out why GT/M exports surrogates.
#

CHARACTERTESTS = {
    "name": "Character set tests - make sure proper data is transferred",
    "definitions": [
        {
            "description": "MUMPS code",
            "fmql": "DESCRIBE " + MUMPSCODETESTID,
            "test": "testResult = " + MUMPSCODETEST
        },
        # CTRL < 32 TEST (3_075-60698)
        # Escape Decimal 27 == u'\x1b'
        # print jreply['results'][0]["error_number"]["value"][1]["variables_and_data"]["value"][88]["data_value"]
        # NOTE: need CSTOP as relying on a large set of bnodes
        {
            "description": "CTRL Chars < 32 rendered as \u00XX",
            "fmql": "DESCRIBE %s CSTOP 500" % CTRLUDR32TESTID,
            "test": "testResult = " + CTRLUDR32TEST
        }
        # \" TEST (... see in 3_075 too)

        # \\\ TEST ?
    
        # \r\n\... < 32 TEST .... try find in 8925. \t too

        # >127 TEST
    ]
}

STESTSETS.append(CHARACTERTESTS)

# Small now: in V9, enhanced Schema Graph will support a full schema audit.
# TODO: add in DESCRIBE TYPE 394_4 - file with no COUNT/FMSIZE
BADSCHEMATESTS = {
    "name": "Bad Schema Tests",
    "definitions": [
        {
            "description": "File with bad .01 schema. Try to list it. Get back count 0",
            "fmql": "SELECT " + BADSCHEMA01FILE,
            "count": "0",
        },
        {
            "description": "File defined but it doesn't exist",
            "fmql": "SELECT " + BADSCHEMANOFILE,
            "error": "",
        },
    ]
}

STESTSETS.append(BADSCHEMATESTS)

# . IEN tests. This is to support date stamps mainly but the test
# system doesn't have date stamped (labs) IENs yet. For now, test
# with _11 which has some.
DOTIENTESTS = {
    "name": "Dot IEN Tests",
    "definitions": [
        {
            "description": "Basic describe of element with . IEN",
            "fmql": "DESCRIBE _11-.1102",
            "test": "testResult=(jreply['results'][0]['uri']['value']=='_11-.1102')"
        },
        {
            "description": "Select first 5 of file with . IEN",
            "fmql": "SELECT _11 LIMIT 5",
            "test": "testResult=((jreply['count']=='5') and (jreply['results'][0]['uri']['value']=='_11-.001'))",
        },
        {
            "description": "Describe record with .IEN CSTOP",
            "fmql": "DESCRIBE _11-.1102 CSTOP 0",
            "test": "testResult=('stopped' in jreply['results'][0]['crossreference_values'])",
        },
        {
            "description": "Count CNodes inside a .IEN'ed record",
            "fmql": "COUNT _114 IN _11-.1102",
            "count": "1",
        }
    ]
}

STESTSETS.append(DOTIENTESTS)

# .001's are special - reaches into Schema view displaying them and data where value is a pointer or a date. Current test system has no example of the pointer form which is in three places in C***'s Lab schema.
# SELECT .001 FROM 50_6 LIMIT 10
OO1IENTESTS = {
    "name": ".001 IEN Tests",
    "definitions": [
        {
            "description": "SCHEMA 50_6 - .001 shows up",
            "fmql": "DESCRIBE TYPE 50_6",
            "test": "testResult=(jreply['fields'][0]['number'] == '.001')"
        },
        {
            "description": "DATA 50_6-95 - .001 field is numeric and ignored",
            "fmql": "DESCRIBE 50_6-95",
            "test": "testResult=('number' not in jreply['results'][0])",
        },
        { # 2.98 may be better candidate if fill in scheduling
            "description": "SCHEMA 3_07 - .001 field is Date",
            "fmql": "DESCRIBE TYPE 3_07",
            "test": "testResult=((jreply['fields'][0]['flags'] == 'D') and (jreply['fields'][0]['number'] == '.001'))",
        },
        {
            "description": "DATA 3_07 - .001 field is Date exposed",
            "fmql": "DESCRIBE 3_07 LIMIT 1",
            "test": "testResult=(('date_time' in jreply['results'][0]) and (jreply['results'][0]['date_time']['fmType'] == '1'))",
        },
        {
            "description": "DATA 3_07 - even its .001 can't be isolated in SELECT FROM",
            "fmql": "SELECT .001 FROM 3_07 LIMIT 2",
            "test": "testResult=('date_time' not in jreply['results'][0])",
        },
        {
            "description": "Schema 2006_552 - .001 is a pointer",
            "fmql": "DESCRIBE TYPE 2006_552",
            "test": "testResult=(jreply['fields'][0]['details'] == '2')",
        }
        # TODO: add ex of this pointer being resolved. Only one in FOIA - not yet populated in test system. 2006_552
        
    ]
}

STESTSETS.append(OO1IENTESTS)

# Boolean 'set of codes' apply fixed maps (Y->true etc) to turn binary and unary valued set of codes into booleans. This cuts down on the number of coded-values/enums needed in a graph or its schema.
BOOLEANCODETESTS = {
    "name": "Boolean Code Tests",
    "definitions": [
        {
            "description": "1:YES;0:NO - 52/10.1",
            "fmql": "DESCRIBE TYPE 52",
            "test": "testResult=(jreply['fields'][12]['type'] == '12')"
        },
        {
            "description": "1:YES - 52/34.1",
            "fmql": "DESCRIBE TYPE 52",
            "test": "testResult=(schemaField(jreply,'34.1')['type'] == '12')"
        },
        {
            "description": "0:NO;1:YES (order different) - 52/116",
            "fmql": "DESCRIBE TYPE 52",
            "test": "testResult=(schemaField(jreply,'116')['type'] == '12')"
        },
        {
            "description": "MALE:FEMALE SEX is Enum not boolean - 2/.02",
            "fmql": "DESCRIBE TYPE 2",
            "test": "testResult=(schemaField(jreply,'.02')['type'] == '3')"
        },
        {
            "description": "YES/NO/UNKNOWN is Enum not boolean - 2/3025",
            "fmql": "DESCRIBE TYPE 2",
            "test": "testResult=(schemaField(jreply,'.3025')['type'] == '3')"
        },
        {
            "description": "1;Yes:0;No (lowers) - 120.86/1",
            "fmql": "DESCRIBE TYPE 120_86",
            "test": "testResult=(schemaField(jreply,'1')['type'] == '12')"
        }
    ]
}

STESTSETS.append(BOOLEANCODETESTS)

TESTSETS.extend(STESTSETS)

def orderPatientReturnTest(qp):
    fileId = "2"
    print "Going to ensure returns file %s in order" % fileId
    reply = qp.processQuery("SELECT " + fileId)
    jreply = json.loads(reply)
    print "Checking %d results" % len(jreply["results"])
    lastResult = None
    passed = True
    for result in jreply["results"]:
        if lastResult and lastResult["uri"]["label"] > result["uri"]["label"]:
            print "ORDER PROBLEM: %s (%s) after %s (%s)" % (result["uri"]["value"], result["uri"]["label"], lastResult["uri"]["value"], lastResult["uri"]["label"])
            passed = False
        lastResult = result
    print "---- done: passed - %s ----" % passed

# Caused problems when FMQL used GETS: URL: 790_2-28

# ##########################################################################

class DefaultLogger:
    def __init__(self):
        pass
    def logInfo(self, tag, msg):
        # self.__log(tag, msg)
        pass
    def logError(self, tag, msg):
        self.__log(tag, msg)
    def __log(self, tag, msg):
        print "Test QP -- %s %s" % (tag, msg)

def main():
 
    opts, args = getopt.getopt(sys.argv[1:], "")
    if len(args) < 5:
        print "Enter <host> <port> <access> <verify> (access/verify for FMQL RPC) <fmql host>"
        print "Ex: localhost 9201 'QLFM1234' 'QLFM1234!!' http://www.examplehospital.com/fmqlEP'"
        return

    fmqlEP = args[4] + "/fmqlEP"

    try:
        rpcc = VistARPCConnection(args[0], int(args[1]), args[2], args[3], "CG FMQL QP USER", DefaultLogger())
    except Exception as e:
        print "Failed to log in to VistA (bad parameters?): %s ... exiting" % e
        return

    times = []

    try:

        fails = 0
        total = 0
        testNo = 0
        stopOnFail = True
        for i, testSet in enumerate(TESTSETS, 1):
            for j, testDef in enumerate(testSet["definitions"], 1):
                total += 1
                if not runTest(rpcc, testSet["name"], str(i) + ":" + str(j), testDef):
                    fails += 1
                    if stopOnFail:
                        break
        print "=== All Done: %d of %d failed ===" % (fails, total)

    except Exception as e:
        print "Exception %s" % e
        traceback.print_exc()

if __name__ == "__main__":
    main()


