#!/usr/bin/env python

#
# LICENSE:
# This program is free software; you can redistribute it and/or modify it 
# under the terms of the GNU Affero General Public License version 3 (AGPL) 
# as published by the Free Software Foundation.
# (c) 2010-2013 caregraf
#

import re
from collections import defaultdict

"""
The schema companion of DescribeReply: a utility to cross the protocol-model boundary. This turns a DESCRIBE TYPE reply into FileInfos, FileMan schema definitions.
"""

class FileInfo(object):

    """
    A simple facade for easy access to an FMQL Describe Type result, a peer of FMQLDescribeResult. To FMQL's exposure of FileMan's Native Schema, it highlights:
    - list multiple: multiples with only one field - these 'sub files' represent simple lists of items
    - does a field "own" its name ie/ is it the first user of a name. Remember that 
    - set of codes: some are just booleans (Y or Y/N). These are distinguished from "proper" sets of codes.
    
    Fixes FMQL quirks:
    - file id returned in . form in Schema but Data uses _ form. _ form used here
    - lot's of "detail" stuffed into one 'detail' field. Expanded in FieldInfo

    TODO: 
    - the easy access provided here will inform improvements to the raw FMQL JSON scheduled for V1.1.
    - handle "corrupt" file and "corrupt" field info properly for easy reports
    - dinum etc and a lot more nuance in fields including ranges [for fuller schema defn]
    """ 
    def __init__(self, describeTypeResult, fmType="VISTA"):
        if "error" in describeTypeResult:
            raise Exception("Can't access error results")
        self.__result = describeTypeResult
        self.__fmType = fmType
        
    def __str__(self):
        mu = "File: " + self.name + " (" + self.id + ")\n"
        mu += "Count (FileMan): " + self.count + "\n" if self.count else ""
        if self.location:
            mu += "Location: " + self.location + "\n"
            mu += "Array: " + self.array + "\n"
        mu += "Parent: " + self.parent + "\n" if self.parent else ""
        mu += "Description: " + self.description + "\n" if self.description else ""
        if self.isListMultiple:
            mu += "List Multiple\n"
            mu += "\tpredicate name: " + self.fieldInfos()[0].predicateName + "\n"
            mu += "\ttype: " + self.fieldInfos()[0].type + "\n"
            return mu
        # The following won't apply to list multiples
        mu += "Files referenced (not including multiples and theirs): " + str(len(self.references())) + "\n"
        fieldInfos = self.fieldInfos()
        mu += "Number of fields: " + str(len(fieldInfos)) + "\n"
        mu += "Number of indexed fields: " + str(len([fieldInfo for fieldInfo in fieldInfos if fieldInfo.index])) + "\n"
        fieldInfosByType = defaultdict(list)
        for fieldInfo in fieldInfos:
            # Want to distinguish boolean and non boolean enum
            ftype = fieldInfo.type
            if ftype == FieldInfo.FIELDTYPES["3"] and fieldInfo.type == "BOOLEAN":
                ftype = "SET OF CODES [BOOLEAN]"
            fieldInfosByType[ftype].append(fieldInfo)
        for i, fieldType in enumerate(fieldInfosByType, 1):
            no = len(fieldInfosByType[fieldType])
            mu += "Number of " + fieldType + ": " + str(no) + " (" + str((no*100)/len(fieldInfos)) + "%) " + "\n"
        mu += "** Duplicates one or more field names **\n" if self.hasDuplicatedFieldNames else ""
        return mu
           
    @property
    def id(self):
        return re.sub(r'\.', '_', self.__result["number"])
           
    @property
    def name(self):
        return self.__result["name"].title()
        
    @property
    def description(self):
        return self.__result["description"]["value"] if "description" in self.__result else ""
        
    @property
    def count(self):
        return self.__result["count"] if "count" in self.__result else ""
        
    @property
    def applicationGroups(self):
        return self.__result["applicationGroups"] if "applicationGroups" in self.__result else ""
        
    @property
    def lastIEN(self):
        return self.__result["lastIEN"] if "lastIEN" in self.__result else ""
    
    @property        
    def location(self):
        if "location" in self.__result:
            return self.__result["location"]
        return ""
        
    @property
    def array(self):
        """
        Base array ie DPT or ... Way to gather files that all share an array!
        """
        if not self.location:
            return ""
        return re.match(r'\^([^\(]+)', self.location).group(1)
       
    @property
    def parent(self):
        # Test if multiple this way too
        if "parent" in self.__result:
            return re.sub(r'\.', '_', self.__result["parent"]) 
        return ""
            
    @property
    def isListMultiple(self):
        """
        TODO: FMQL - embed number of fields in the FieldInfo of a multiple field. That way, can know if it is a list multiple.
        """
        if not self.parent:
            return False
        if len(self.fieldInfos()) == 1:
            return True
        return False
        
    @property
    def isBlankNodeMultiple(self):
        raise Exception("Not yet implemented - may do from inputTransform if any")
        
    def multiples(self):
        return [fieldInfo.multipleId for fieldInfo in self.fieldInfos() if fieldInfo.type == "MULTIPLE"]
        
    def references(self):
        """
        Note: unlike DESCRIBE for data, DESCRIBE TYPE does not return the (meta) data about contained entities. You need to explicitly go through DescribeTypeReply's for contained multiples to get all the references of the tree represented by this type of record.
        ie/ 
        allReferences(fId, fileInfoManager):
            references = fileInfoManager.fileInfo(fId).references()
            for cFId in fi.multiples():
                references |= allReferences(cFId, fileInfoManager)
            return references
        """
        return set(range for fieldInfo in self.fieldInfos() if fieldInfo.type in ["POINTER TO A FILE", "VARIABLE-POINTER"] for range in fieldInfo.ranges())
                
    def fieldInfos(self): # only non corrupt
        """
        Iterator of field information - returns tuples that describe each field
        """
        try:
            return self.__fieldInfos
        except:
            pass
        self.__fieldInfos = []
        namesSoFar = set()
        nnamesSoFar = set() # may have unique name but not when normalization is taken into account
        for fieldResult in self.__result["fields"]:
            if "corruption" in fieldResult: # corruption (may be a name, maybe not)
                continue
            nname = FieldInfo.normalizeFieldName(fieldResult["name"])                
            self.__fieldInfos.append(FieldInfo(self.id, fieldResult, fieldResult["name"] not in namesSoFar, nname not in nnamesSoFar, self.__fmType))
            namesSoFar.add(fieldResult["name"])
            nnamesSoFar.add(nname)
        return self.__fieldInfos
        
    def fieldInfo(self, id):
        for fieldInfo in self.fieldInfos():
            if fieldInfo.id == id:
                return fieldInfo
        return None
        
    @property
    def hasDuplicatedFieldNames(self):
        """
        REM: FileMan only enforces uniqueness for field ids, not for field names.
        """
        for fieldInfo in self.fieldInfos():
            if not fieldInfo.isNameOwner:
                return True
        return False
        
    @property
    def hasDuplicatedNFieldNames(self):
        """
        REM: name may be unique but what about the normalized name that leads to a predicate?
        """
        for fieldInfo in self.fieldInfos():
            if not fieldInfo.isNNameOwner:
                return True
        return False
        
    def corruptFields(self):
        pass
                    
class FieldInfo(object):

    """
    TODO: FMQL v1.1 - remove client side overrides of FMQL type assignments
    
    TODO: multiple tied to its field and isListMultiple excluded from having a range
    
    Note on "IEN" == .001/NUMBER field
        in VistA FM (but not C***), .001 is reserved as a field for IENs. It serves both as an identifier for "IEN" in the FileMan API (ie/ ask for IEN just like any other field) and in its computation, it sets a range for IENs. Not that not all files (284 out of 5743 in FOIA 2013) have this field. Even where they don't, FileMan's API treats the keyword "NUMBER" to mean IEN - even if the IEN is a date or other format.
    """

    # TMP Til FMQL uses .8. ie/ I FLDFLAGS["D" S FLDTYPE=1 ; Date 
    # will look into file .81/^DI(.81,"C","D")
    # TODO: add "BOOLEAN" ... "FREE TEXT" -> STRING, FORMATTED STRING, POINTER etc.
    FIELDTYPES = {
        "1": "DATE-TIME",
        "2": "NUMERIC",
        "3": "SET OF CODES",
        "4": "FREE TEXT",
        "5": "WORD-PROCESSING",
        # BC, DC and Cp# will decide the type of a computed field ie/ computed field type
        "6": "COMPUTED", 
        "7": "POINTER TO A FILE",
        "8": "VARIABLE-POINTER",
        "9": "MULTIPLE",
        # Q C***, K VISTA
        "10": "MUMPS", 
        "11": "IEN", # IEN match in .001
        # Both attributed by FMQL and BC for Computed
        "12": "BOOLEAN" # SET UP IN FMQL - SET OF CODES turned into boolean in schema
    }

    # a name owner is the FIRST field in the file to use a name. All others don't 'own' the name
    def __init__(self, fileId, describeFieldResult, isNameOwner, isNNameOwner, fmType="VISTA"):
        self.__fileId = fileId
        self.__result = describeFieldResult   
        self.__isNameOwner = isNameOwner
        self.__isNNameOwner = isNNameOwner
        self.__fmType = fmType
        self.type
        
    def __str__(self):
        mu = "Field: " + self.name + " (" + self.id + ")\n"
        return mu
        
    @property
    def raw(self):
        return self.__result
                
    @property
    def id(self):
        """
        Unlike for file, leaving . form for id of field
        """
        return self.__result["number"]
        
    @property
    def fileId(self):
        return self.__fileId
        
    @property
    def name(self):  
        # Note: only container would know if ambiguous
        return self.__result["name"].title()
        
    @property
    def isNameOwner(self):
        """
        Owner is the first (order by id) user of a name in a file
        """
        return self.__isNameOwner
                
    @property
    def isNNameOwner(self):
        return self.__isNNameOwner
                
    @property
    def predicateName(self):
        """
        Predicate name is unique in the file, lowercase normalized (for RDF etc) and in the context of the file (ie/ not unique across all files so must suffix with fileId)
        
        Note: only the quote and the equal sign are excluded, so anything, except " and = are acceptable BUT other schemes are stricter.
        
        Note: could walk all files and see if unique across all files BUT problem that a new definition could change everything. Better to air on side of "in file context" caution.
        
        TODO: currently this is an instance method as need all the meta to decide if a name is ambiguous. Once FMQL notes ambiguity on the server side, then this method becomes much simpler and should be a class method like normalizeFieldName. In effect, relies on ordered walk of all field names, making sure their normalized form is unique.
        """
        if self.isNNameOwner: # Not just name owner but normalized name owner
            return FieldInfo.normalizeFieldName(self.__result["name"]) + "-" + self.fileId
        # Not owner so must add the fieldId as well as the fileId to the name!
        return FieldInfo.normalizeFieldName(self.__result["name"]) + "-" + re.sub(r'\.', '_', self.id) + "-" + self.fileId
        
    @staticmethod
    def normalizeFieldName(fieldName):
        """
        Static to allow the same normalization to be used without creating the full fieldInfo         
        For now, going a lot stricter than standards ie/ excluding all but A-Za-z\d_\-
        
        No $, ., #, %, (), [], {}, :, &, @, ', / or comma

        ex/ Utility doesn't like ":" in a field name ex/ ROUTINES (RN1:RN2) -> ROUTINES (RN1-RN2)
        ex/ ALIAS FMP/SSN ... don't want / in a URL'ed id
        """
        return re.sub(r'[^A-Za-z\d_\-]', "_", fieldName).lower()

    @property
    def description(self):
        return self.__result["description"]["value"] if "description" in self.__result else ""
    
    @property 
    def type(self):
        """
        Accounts for COMPUTED - makes range concrete but also ensures a computation is there. Will avoid with FMQL v1.1. where can drop Computed as a "type"
        """
        # FMQL v1.1 - remove this override of FMQL MUMPS type assignment
        if self.__fmType != "VISTA":
            # MUMPS_FLAG = "K" if self.__fmType == "VISTA", "Q" for C***
            # K is C*** means consistency check.
            # FMQL V1.1 will fix but now, absence of K means making MUMPS!
            # Careful - C*** 1.23/.01 has F and Q but really just a string
            # but note that it can be either MUMPS or a String (Q or F) if you
            # read its comment.
            if self.__result["type"] == "4" and (re.search(r'Q', self.__result["flags"]) and not re.search(r'F', self.__result["flags"])): # ie defaulted to MUMPS as no Q etc.
                return self.FIELDTYPES["10"]
            # Reverse application_filter-757_2
            if self.__result["type"] == "10": # based on K - wrong: crude but default to String
                return self.FIELDTYPES["4"]  
        # FMQL returns "COMPUTED" for type of computed field. Break out to subtype     
        # Important: Cm == is NOT computed multiple. m means multi-line as in multi-line computed. These are strings.
        # Note: ignoring M (as to enter values into a multiple as MP is just a pointer.         
        if self.__result["type"] == "6": # 6 as has "C"
            # Need computation for computed types - otherwise how does user know?
            if not re.search(r'C', self.__result["flags"]):
                raise Exception("FMQL Bug - marked as computed " + self.id + " but C not in flags")
            if not self.computation:
                raise Exception("Computed field " + self.id + " has no computation")
            # DC, BC, Cp{fid}
            # Test ex/ CHCSS:1 Number-Meaningful 411
            if re.search(r'B', self.__result["flags"]):
                return self.FIELDTYPES["12"]
            # Before V1.1, FMQL already noted this as D so won't get here
            # Note: there are exs of DC in C*** but all corrupt? Don't show
            if re.search(r'D', self.__result["flags"]):
                return self.FIELDTYPES["1"]
            # C*** has Cmp for multiple pointer. VistA has Cp for computed pointer
            if re.search(r'Cm?p[\d\.]+', self.__result["flags"]):
                return self.FIELDTYPES["7"] # need to take care of range below
            return self.FIELDTYPES["4"] # default to String      
        return self.FIELDTYPES[self.__result["type"]]
        
    @property
    def flags(self):
        return self.__result["flags"]
                        
    @property
    def location(self):
        """
        Computed/IEN have no location.
        """
        if "location" in self.__result:
            return self.__result["location"]
        return ""

    @property
    def index(self):
        return self.__result["index"] if "index" in self.__result else ""
        
    @property
    def inputTransform(self):
        """
        An INPUT transform is M code for a particular field that is executed to determine if the data for that field is valid
        """
        return self.__result["inputTransform"] if "inputTransform" in self.__result else ""

    @property
    def triggers(self):
        """
        TODO: will improve for 1.1 (right now: field id -> field name must be done outside)
        """
        return self.__result["triggers"] if "triggers" in self.__result else ""
        
    @property
    def crossReferenceCount(self):
        return self.__result["crossReferenceCount"] if "crossReferenceCount" in self.__result else ""
        
    @property
    def inputTransform(self):
        """
        An INPUT transform is M code for a particular field that is executed to determine if the data for that field is valid
        """
        return self.__result["inputTransform"] if "inputTransform" in self.__result else ""

    @property
    def computation(self):
        return self.__result["computation"] if "computation" in self.__result else ""

    @property
    def multipleId(self):
        return re.sub(r'\.', '_', self.__result["details"]) if self.__result["type"] == "9" else ""  

    def ranges(self):
        """
        TODO: FMQL V1.1 - should record NAME of file pointed to as well as its id and
        this goes for Cp{id} too.
        
        TODO: not catching "0" or invalid file id as range. Need to - at least note corruption.
        
        Testing examples:
        - Computed Multiple Pointer: CHCSS:diagnosis-2_9505
        """
        # Can be COMPUTED Cp{id} too
        if self.type not in ["POINTER TO A FILE", "VARIABLE-POINTER"]:
            return []
        if self.__result["type"] == "7":
            return [re.sub(r'\.', '_', self.__result["details"])]
        if self.__result["type"] == "6": # must be Cp{id} or Cmp{id} (CHCS only)
            return [re.sub(r'\.', '_', re.search(r'Cm?p([\d\.]+)', self.__result["flags"]).group(1))]
        # 8 VARIABLE POINTER         
        return [re.sub(r'\.', '_', vrFileId) for vrFileId in self.__result["details"].split(";")]
        
    @property
    def rangeType001(self):
        """
        IEN FLAGS:
        - NJ12,0 ... 999999999999 is max; NJ2,0 ... 999 but X>100 for NJ3,0
        (ie/ loop IEN fields for patterns)
        """
        if self.__result["type"] != "11":
            raise Exception("Not an .001")
        # Most .001's are #'s with computations like 'K:+X'=X!(X>999999)!(X<1)!(X?.E1"."1N.N) X'
        if re.match(r'N', self.__result["flags"]):
            return "NUMBER"
        # ex/ 2_98 Field: Appointment Date/Time
        if re.match(r'D', self.__result["flags"]):
            return "DATE"
        return "OTHER" # TBD: range check
        
    def codes(self):
        """
        Singleton coded values (bound only): len(codes) == 1
        """
        if self.__result["type"] not in ["3", "12"]:
            return []
        codes = []
        for enumValue in self.__result["details"].split(";"):
            if not enumValue:
                continue
            if re.search(r':', enumValue):
                enumMN = enumValue.split(":")[0]
                enumLabel = enumValue.split(":")[1]
            else:
                # TBD: FMQL TODO - RPMS "BORDERLINE" has no :
                enumMN = enumValue
                enumLabel = enumValue  
            codes.append((enumMN, enumLabel))  
        return codes
        
    def booleanOfValue(self, value):
        if self.type != "BOOLEAN":
            raise Exception("Not boolean coded")
        if value in ["Y", "YES", "1", self.__result["name"]]:
            return True
        return False
           
# ############################# Test Driver ####################################

import sys
import urllib
import urllib2
import json

# FMQLEP = "http://www.examplehospital.com/fmqlEP"
FMQLEP = "http://livevista.caregraf.info/fmqlEP"     

def main():

    queryURL = FMQLEP + "?" + urllib.urlencode({"fmql": "DESCRIBE TYPE 2"}) 
    reply = json.loads(urllib2.urlopen(queryURL).read())
    fi = FileInfo(reply)
    print fi

if __name__ == "__main__":
    main()