#!/usr/bin/env python

#
# The following runs FMQL queries against Caregraf's Demo VistA ("livevista") which returns a requested flavor of JSON-LD. It examines the optimal default framing for
# FMQL JSON-LD.
# 
# There are many ways to arrange ("frame") the same content in JSON-LD. The following
# will manipulate different framings of VistA graphs returned by FMQL - the goal is
# A DEFAULT FRAMING BY FMQL that produces natural JSON and where the work of modeling
# and fitting into a wider world of linked data is done by an appropriate context. Bit by
# bit, we'll move towards more "tree" based framings which as the Framing spec (http://json-ld.org/spec/latest/json-ld-framing/) says
#
#   "A JSON-LD document is a representation of a directed graph. A single directed graph can have many different serializations, each expressing exactly the same information. Developers typically work with trees, represented as JSON objects"
#
# Currently (Nov 2013), there are two framings. More are coming.
#
# Javascript Equivalent Coming
#
# LICENSE:
# This program is free software; you can redistribute it and/or modify it under the terms of 
# the GNU Affero General Public License version 3 (AGPL) as published by the Free Software 
# Foundation.
# (c) 2013 caregraf
#

import re 
import urllib, urllib2
import json

# These settings should match your FMQL configuration 
# FMQLEP = "http://www.examplehospital.com/fmqlEP" # Endpoint address
FMQLEP = "http://livevista.caregraf.info/fmqlEP" # Endpoint address of Caregraf demo VistA

# ##############################################################
#
# JSON-LD Framing 1 - one context, shared referenced resources
#
# - one basic context shared between all FMQL replies means that Context doesn't define 
# the type of a predicate and any predicate values with a datatype or any URI will have
# Object values
# - referenced resources are not defined in line - they are defined elsewhere in @graph. 
# This makes for reuse but means not all resources in @graph's list are of the same type.
# It also makes for more indirection when looking up the label or meaning of a resource. 
#

"""
Patient record of patient 9
"""
def reportPatient9F1():

    print "\r=== A report patient 9 (Chris Jones in CG Demo VistA) ===\r"
    
    query = {"fmql": "DESCRIBE 2-9", "format": "JSON-LD"}
    queryURL = FMQLEP + "?" + urllib.urlencode(query)
    jreply = json.loads(urllib2.urlopen(queryURL).read())
    if jreply.has_key("error"):
        print "Got error %s trying to get definition of PATIENT - exiting" % patientDescription["error"]
        return
        
    # Take out the graph - it is id'ed by the FMQL that led to it which makes tracing easier. It is also dated.
    print
    print "FMQL returned Graph", jreply["id"], "on", jreply["generatedAt"]
    print
    
    # The default JSON form of "@graph" is a list of resource descriptions. We want to index by "id" for easy lookup.
    graph = indexGraph(jreply["@graph"])
    
    #
    # Now isolate all the patient descriptions in the graph. Patient is of type "vs:2"        
    #
    patientDescriptions = [graph[id] for id in graph if graph[id]["type"] == "vs:2"]
    
    # In this case, there is only one patient description
    patientDescription = patientDescriptions[0]
    
    # First let's print the basic properties of the description. All descriptions have
    # "id", "type" and "label". "type" is a reference to the type of resource we're 
    # describing. This time, it's "vs:2", "VistA Schema 2" and this is labeled elsewhere
    # in the graph.
    print "---- Contents: One Patient Description ----"
    print "about"
    print "\t", patientDescription["label"], "-", patientDescription["id"]
    print "type"
    print "\t", graph[patientDescription["type"]]["label"], "-", patientDescription["type"]
    print
    
    #
    # Two types of predicate value - simple literals or structured.
    #
    # Structured can:
    # - typed literals like booleans or dates
    #   ex/ 
    # - reference to another resource with its id. That resource will be labeled
    #   elsewhere in the graph.
    #   ex/  
    # - descriptions, in an ordered list, of contained resources
    #   ex/ {u'list': [{u'label': u'BLACK OR AFRICAN AMERICAN' ...
    #
    for predicate in patientDescription:
    
        # We printed the basic properties already
        if predicate in ["id", "type", "label"]:
            continue 
        
        value = patientDescription[predicate]
        
        print predicate
        
        # Structured Value
        if type(value) == dict:
            # A reference - print its id and label
            if "id" in value:
                print "\t", graph[value["id"]]["label"], "-", value["id"]
            # A list of contained resources: going to be crude. Just printing a label
            elif "list" in value:
                print "\tLIST ..."
                for containedDescription in value["list"]:
                    print "\t\t", containedDescription["label"], containedDescription["id"]
            # A typed value (boolean or date)
            else:
                print "\t", value["value"], "-", value["type"]
        # Simple Value
        else:
            print "\t", value
    print
    print "... note that properties can appear in any order. If you want a logical presentation for a large data type like PATIENT (2), you'll need to define an order, here, in the reporter or use JSON-LD toolchains to reframe the content more logically."
    
"""
Problems of Patient 9

Note: ignoring CONDITION: HIDDEN in this illustration. In real systems, 
these are filtered out.
"""
def reportProblems9F1():
    """
    Print out the problems of patient 9. This shows how the FMQL graph distinguishes references to terminologies like VA VUIDs or ICD9 from references to other data within a VistA.
    """    
    print "\r=== A report problems (Chris Jones in CG Demo VistA) ===\r"
    
    query = {"fmql": "DESCRIBE 9000011 FILTER(.02=9000001-9)", "format": "JSON-LD"}
    queryURL = FMQLEP + "?" + urllib.urlencode(query)
    jreply = json.loads(urllib2.urlopen(queryURL).read())
    if jreply.has_key("error"):
        print "Got error %s trying to get problems of PATIENT - exiting" % patientDescription["error"]
        return
        
    # Take out the graph - it is id'ed by the FMQL that led to it which makes tracing easier. It is also dated.
    graph = jreply["@graph"]
    print
    print "FMQL returned Graph", jreply["id"], "on", jreply["generatedAt"]
    print
    
    print "\r=== A report patient 9 (Chris Jones in CG Demo VistA) ===\r"
        
    # Take out the graph and index everything in it
    graph = indexGraph(jreply["@graph"])
    
    # As Graph gives descriptions in an ordered array, the returned entries will reflect the order in the file.
    problemDescriptions = [description for description in jreply["@graph"] if description["type"] == "vs:9000011"]
        
    for i, problemDescription in enumerate(problemDescriptions, 1):
        
        print "\r---- Problem Description ", i, "----"
        print "about"
        print "\t", problemDescription["label"], "-", problemDescription["id"]
        print "type"
        print "\t", graph[problemDescription["type"]]["label"], "-", problemDescription["type"]
        print
    
        for predicate in problemDescription:
    
            # We printed the basic properties already
            if predicate in ["id", "type", "label"]:
                continue 
        
            value = problemDescription[predicate]
        
            print predicate
        
            # Structured Value
            if type(value) == dict:
                # A reference - print its id and label
                if "id" in value:
                    if "sameAs" in graph[value["id"]]:
                        sameAsId = graph[value["id"]]["sameAs"]
                        sameAsLabel = graph[sameAsId]["label"]
                        print "\t", graph[value["id"]]["label"], "-", value["id"], "- SAMEAS -", sameAsLabel, "-", sameAsId
                    else:
                        print "\t", graph[value["id"]]["label"], "-", value["id"]
                # A list of contained resources: going to be crude. Just printing a label
                elif "list" in value:
                    print "\tLIST ..."
                    for containedDescription in value["list"]:
                        print "\t\t", containedDescription["label"], containedDescription["id"]
                # A typed value (boolean or date)
                else:
                    print "\t", value["value"], "-", value["type"]
            # Simple Value
            else:
                print "\t", value
    
    # Let's do some stats ...
    print
    print "---- Some Numbers ----"    
    print "This patient has", len(problemDescriptions), "problems"
    # Another way to deal with active, an enumeration, is to key off its label: graph[problemDescription["status-9000011"]["id"]]["label"] == "ACTIVE"
    print "Of which", sum(1 for problemDescription in problemDescriptions if problemDescription["status-9000011"]["id"] == "vs:9000011__12_E-ACTIVE"), "are active"
    # Optional predicate 'service_connnected' - first check if there and then check the value
    print sum(1 for problemDescription in problemDescriptions if "service_connected-9000011" in problemDescription and problemDescription["service_connected-9000011"]["value"] == "true"), "are service connected"
    print "Distinct diagnoses", len(set(problemDescription["diagnosis-9000011"]["id"] for problemDescription in problemDescriptions if "diagnosis-9000011" in problemDescription))
    
    # Let's print the still active diagnoses
    print
    print "---- Active Problems (remember this is just demo data!) ----"
    for i, pd in enumerate([pd for pd in problemDescriptions if pd["status-9000011"]["id"] == "vs:9000011__12_E-ACTIVE"], 1):
        diagSameAs = graph[pd["diagnosis-9000011"]["id"]]["sameAs"]
        print "\t", i, graph[diagSameAs]["label"], "-", graph[diagSameAs]["id"]
        
    # TODO: a nice thing about shared referenced resources is that it is easy to see
    # which ones are used throughout a graph. You don't need to traverse individual
    # resources - you just need to grab resources by type.
        
# ##############################################################
#
# JSON-LD Framing 2 - per graph context, shared referenced resources
#
# - each graph returned through FMQL gets its own context that defines the type of 
# non-simple values like resources referenced (@id) or typed literals (dateTime, boolean ...)
# - referenced resources are not defined in line - they are defined elsewhere in @graph. 
# This makes for reuse but means not all resources in @graph's list are of the same type.
# It also makes for more indirection when looking up the label or meaning of a resource. 
#
# Conclusion: probably better to go with Frame 1 or go all the way to Frame 3 with inline
# data. Here you need to chase down the graph AND work the context.
#

def reportVitals9F2():

    print "\r=== A report vitals (Chris Jones in CG Demo VistA) ===\r"
    
    # Vitals of patient 9 from April 2008 on
    query = {"fmql": "DESCRIBE 120_5 FILTER(.02=2-9&.01>2008-04-01)", "format": "JSON-LD2"}
    queryURL = FMQLEP + "?" + urllib.urlencode(query)
    jreply = json.loads(urllib2.urlopen(queryURL).read())
    if jreply.has_key("error"):
        print "Got error %s trying to get vitals of PATIENT - exiting" % patientDescription["error"]
        return
        
    # Take out the graph - it is id'ed by the FMQL that led to it which makes tracing easier. It is also dated.
    graph = jreply["@graph"]
    context = jreply["@context"] # it will matter in this case
    print
    print "FMQL returned Graph", jreply["id"], "on", jreply["generatedAt"]
    print
    
    print "\r=== A report patient 9 (Chris Jones in CG Demo VistA) ===\r"
        
    # Take out the graph and index everything in it
    graph = indexGraph(jreply["@graph"])
    
    vitalDescriptions = [description for description in jreply["@graph"] if description["type"] == "vs:120_5"]
        
    for i, vitalDescription in enumerate(vitalDescriptions, 1):
        
        print "\r---- Vital Description ", i, "----"
        print "about"
        print "\t", vitalDescription["label"], "-", vitalDescription["id"]
        print "type"
        print "\t", graph[vitalDescription["type"]]["label"], "-", vitalDescription["type"]
        print
    
        for predicate in vitalDescription:
    
            # We printed the basic properties already
            if predicate in ["id", "type", "label"]:
                continue 
        
            value = vitalDescription[predicate]
        
            print predicate
        
            # Structured Value - in this framing, only structured values are defined
            # in the context.
            if predicate in context:
                # A list of contained resources: context declares container to be a list
                if "@container" in context[predicate]:
                    print "\tLIST ..."
                    # List of simple values vs 
                    if "@type" in context[predicate] and context[predicate]["@type"] == "@id":
                        for cvalue in value:
                            print "\t", graph[cvalue]["label"], "-", cvalue
                    else:
                        for containedDescription in value:
                            print "\t\t", containedDescription["label"], containedDescription["id"]
                # A reference - print its id and label
                elif context[predicate]["@type"] == "@id":
                    print context[predicate]
                    print value
                    if "sameAs" in graph[value]:
                        sameAsId = graph[value]["sameAs"]
                        sameAsLabel = graph[sameAsId]["label"]
                        print "\t", graph[value]["label"], "-", value, "- SAMEAS -", sameAsLabel, "-", sameAsId
                    else:
                        print "\t", graph[value]["label"], "-", value
                # A typed value (boolean or date)
                else:
                    print "\t", value, "-", context[predicate]["@type"]
            # Simple Value
            else:
                print "\t", value
                
# ##############################################################
#
# JSON-LD Framing 3 - per graph context, inline referenced resources
#
# - each graph returned through FMQL gets its own context that defines the type of 
# non-simple values like resources referenced (@id) or typed literals (dateTime, boolean ...)
# - referenced resources are defined (redundantly) in line. This means @graph entries
# are all of one type.
#
# ... COMING 
#

# ##############################################################
#
# JSON-LD Framing 4 - per graph context, inline referenced resources, predicates
# normalized
#
# Ala Framing 3 but all predicates are normalized ... name-2 -> name in the context
#
# ... COMING 
#
                
# ############################ Using pyld ################
#
# To use json-ld's Python toolkit, install pyl
#

try: # for testing only
    from pyld import jsonld
except:
    pass

def usePyld():

    # Grab the vitals used in frame 2 
    query = {"fmql": "DESCRIBE 120_5 FILTER(.02=2-9&.01>2008-04-01)", "format": "JSON-LD2"}
    queryURL = FMQLEP + "?" + urllib.urlencode(query)
    jreply = json.loads(urllib2.urlopen(queryURL).read())
    json.dump(jreply, open("fmql_FMQLEX.json", "w"), indent=2)

    # Let's produce different forms of JSON-LD (and RDF) from this 
    
    # 1. Expanded form
    print "pyld expand ..."
    expanded = jsonld.expand(jreply)
    json.dump(expanded, open("pyld_EXP_FMQLEX.json", "w"), indent=2)
    
    # 2. Compact it - using the basic context of framing 1
    print "pyld compact ..."
    compact = jsonld.compact(jreply, json.load(open("vsfmcontextBase.json")))
    json.dump(compact, open("pyld_COMP_FMQLEX.json", "w"), indent=2)

    # 3. Dump RDF -- only nquads are supported ... others return errors
    print "pyld tordf ..."
    open("pyld_RDF_FMQLEX.rdf", "w").write(jsonld.to_rdf(jreply, {"format": "application/nquads"}))
            
# ############################ Utilities #################

def indexGraph(graph):
    """
    All FMQL Describes return graphs of resources - at least one main resource and information about resources referenced.
    
    JSON-LD @graph holds a list of resource definitions. Turn that into an indexed
    dictionary
    """
    return {description["id"]: description for description in graph}

# ############################# Demo Driver ####################################

def main():

    reportPatient9F1()

    reportProblems9F1()
    
    reportVitals9F2()
    
    usePyld()

if __name__ == "__main__":
    main()