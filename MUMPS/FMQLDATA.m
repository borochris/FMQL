FMQLDATA ;CG/CD - Caregraf - FMQL Data Query Processor; 11/25/2013  11:30
 ;;1.1b;FMQLQP;;Nov 25th, 2013
 ;
 ;
 ; FMQL Data Query Processor
 ;
 ; For queries for data. Peer of FMQLSCH
 ;
 ; FMQL Query Processor (c) Caregraf 2010-2013 AGPL
 ;
 ;
 ;
DESONE(REPLY,PARAMS) ;
 I '$D(PARAMS("TYPE")) D ERRORREPLY^FMQLJSON(REPLY,"Type Not Specified") Q
 I '$D(PARAMS("ID")) D ERRORREPLY^FMQLJSON(REPLY,"ID Not Specified") Q
 ; CNODESTOP defaults to 10 unless set explicitly
 N CNODESTOP S CNODESTOP=$S($D(PARAMS("CNODESTOP")):$G(PARAMS("CNODESTOP")),1:10)
 N NTYPE S NTYPE=$TR(PARAMS("TYPE"),"_",".")
 N FLINF D BLDFLINF^FMQLUTIL(NTYPE,.FLINF)
 I $D(FLINF("BAD")) D ERRORREPLY^FMQLJSON(REPLY,FLINF("BAD")) Q
 I '$D(FLINF("GL")) D ERRORREPLY^FMQLJSON(REPLY,"Can Only Describe a Global") Q
 I '$D(@FLINF("ARRAY")@(PARAMS("ID"),0)) D ERRORREPLY^FMQLJSON(REPLY,"No such identifier for type "_PARAMS("TYPE")) Q
 D REPLYSTART^FMQLJSON(REPLY)
 D LISTSTART^FMQLJSON(REPLY,"results") ; TBD: remove for new JSON
 D ONEOFTYPE(REPLY,.FLINF,FLINF("ARRAY"),PARAMS("ID"),CNODESTOP)
 D LISTEND^FMQLJSON(REPLY)
 ; the query as args
 D DICTSTART^FMQLJSON(REPLY,"fmql")
 D DASSERT^FMQLJSON(REPLY,"OP","DESCRIBE")
 D DASSERT^FMQLJSON(REPLY,"URI",FLINF("EFILE")_"-"_PARAMS("ID"))
 D DASSERT^FMQLJSON(REPLY,"CSTOP",CNODESTOP)
 D DICTEND^FMQLJSON(REPLY)
 D REPLYEND^FMQLJSON(REPLY)
 Q
 ;
 ;
ALL(REPLY,PARAMS) ;
 N FLINF,BPERR,PFLINF,PID,IENA,LIMIT,OFFSET,NOIDXMX,ORDERBY,AFTERIEN,CNODESTOP,TOX,CNT
 I '$D(PARAMS("TYPE")) D ERRORREPLY^FMQLJSON(REPLY,"Type Not Specified") Q
 S FILE=$TR(PARAMS("TYPE"),"_",".")
 D BLDFLINF^FMQLUTIL(FILE,.FLINF)
 I $D(FLINF("BAD")) D ERRORREPLY^FMQLJSON(REPLY,FLINF("BAD")) Q
 I '$D(FLINF("GL")) D  ; Handle Describe or Count of contained nodes.
 . I '$D(PARAMS("IN")) S BPERR="Missing: Contained Node Selection requires 'IN'" Q
 . D PARSEURL^FMQLUTIL(PARAMS("IN"),.PFLINF,.PID)
 . I '$D(PID) S BPERR="Bad Value: 'IN' requires ID" Q
 . I '$D(PFLINF("GL")) S BPERR="Bad Value: 'IN' must be a global type" Q
 . I PFLINF("FILE")'=FLINF("PARENT") S BPERR="Bad Value: CNode parent must be in 'IN'" Q
 . S IENA=$NA(@PFLINF("ARRAY")@(PID,FLINF("PLOCSUB")))
 E  S IENA=""
 I $D(BPERR) D ERRORREPLY^FMQLJSON(REPLY,BPERR) Q
 ; Defaults of -1,0,-1 for no LIMIT, no offset, no max cut off if no IDX, 
 S LIMIT=$S($G(PARAMS("LIMIT"))?0.1"-"1.N:PARAMS("LIMIT"),1:-1)
 S OFFSET=$S($G(PARAMS("OFFSET"))?1.N:PARAMS("OFFSET"),1:0)
 S NOIDXMX=$S($G(PARAMS("NOIDXMX"))?1.N:PARAMS("NOIDXMX"),1:-1)
 S ORDERBY=$G(PARAMS("ORDERBY"))
 S AFTERIEN=$S($G(PARAMS("AFTERIEN"))?1.N:PARAMS("AFTERIEN"),1:"")
 I AFTERIEN'="" S OFFSET=0  ; Make sure AFTERIEN takes precedence
 ; Forcing default CNODESTOP to be 10
 I PARAMS("OP")="DESCRIBE" S CNODESTOP=$S($D(PARAMS("CNODESTOP")):$G(PARAMS("CNODESTOP")),1:10)
 ; Default value is "" for COUNT
 S TOX=$S((PARAMS("OP")="SELECT"):"D JSEL^FMQLDATA(REPLY,.FLINF,FAR,IEN,.PARAMS)",(PARAMS("OP")="DESCRIBE"):"D JDES^FMQLDATA(REPLY,.FLINF,FAR,IEN,CNODESTOP,.PARAMS)","1":"")
 D REPLYSTART^FMQLJSON(REPLY)
 D LISTSTART^FMQLJSON(REPLY,"results")
 S CNT=$$XONFL^FMQLUTIL(.FLINF,$G(PARAMS("FILTER")),IENA,LIMIT,OFFSET,AFTERIEN,ORDERBY,NOIDXMX,TOX,.PARAMS)
 D LISTEND^FMQLJSON(REPLY)
 ; Note: if problem listing (no indexed filter), CNT<0
 D DASSERT^FMQLJSON(REPLY,"count",CNT)
 ; TBD: how to record NOIDXMX?
 D DICTSTART^FMQLJSON(REPLY,"fmql")
 D DASSERT^FMQLJSON(REPLY,"OP",PARAMS("OP"))
 D DASSERT^FMQLJSON(REPLY,"TYPELABEL",FLINF("LABEL"))
 D DASSERT^FMQLJSON(REPLY,"TYPE",FLINF("EFILE"))
 I PARAMS("OP")'="COUNT" D
 . D DASSERT^FMQLJSON(REPLY,"LIMIT",LIMIT)
 . ; TODO: handle alternative of AFTERIEN for OFFSET above and do one or other
 . I $D(PARAMS("AFTERIEN")) D DASSERT^FMQLJSON(REPLY,"AFTERIEN",PARAMS("AFTERIEN"))
 . E  D DASSERT^FMQLJSON(REPLY,"OFFSET",OFFSET)
 I $D(PARAMS("FILTER")) D DASSERT^FMQLJSON(REPLY,"FILTER",PARAMS("FILTER"))
 ; Only for DESCRIBE
 I $D(CNODESTOP) D DASSERT^FMQLJSON(REPLY,"CSTOP",CNODESTOP)
 D DICTEND^FMQLJSON(REPLY)
 D REPLYEND^FMQLJSON(REPLY)
 Q
 ;
 ;
 ; Build JSON for one selection
 ; - FAR = FLINF("ARRAY") for Global; FAR = Qualified location for CNode
 ; Note: supports only top level CNodes
 ; Note: "g"]"H" in MUMPS ie. lower case follows upper case. This means
 ;       selection order is case sensitive. This may be unexpected.
 ; 
 ; Note: MAY DEPRECATE AS SBYPRED is more useful, DESCRIBE CSTOP 0 is succinct enough
 ; or expand to take a list of predicates.
 ; 
 ; 
JSEL(REPLY,FLINF,FAR,IEN,PARAMS) ;
 D DICTSTART^FMQLJSON(REPLY)
 ; FID=IEN for Globals. Only qualify for CNodes
 ; - replace for unusual IENS in .11 etc.
 N FID S FID=$S('$D(FLINF("GL")):IEN_"_"_$QS(FAR,$QL(FAR)-1),1:IEN)
 D IDFIELD(.FLINF,FAR,IEN,FID)
 I $D(PARAMS("FIELD")) D
 . N FDINF D BLDFDINF^FMQLUTIL(.FLINF,PARAMS("FIELD"),.FDINF)
 . Q:$D(FDINF("BAD"))  ; TBD: centralize
 . Q:FDINF("TYPE")=9  ; Don't allow CNode selection this way. Force "IN".
 . Q:FDINF("TYPE")=11  ; For now, don't allow .001 as most not explicitly exposed
 . D ONEFIELD(FAR,IEN,.FDINF)
 D DICTEND^FMQLJSON(REPLY)
 Q
 ;
 ;
 ; Same as JSEL except returns full description
JDES(REPLY,FLINF,FAR,IEN,CNODESTOP,PARAMS) ;
 ; Last Subscript for CNode
 N ID S ID=$S('$D(FLINF("GL")):IEN_"_"_$QS(FAR,$QL(FAR)-1),1:IEN)
 D ONEOFTYPE(REPLY,.FLINF,FAR,ID,CNODESTOP)
 Q
 ;
 ;
ONEOFTYPE(REPLY,FLINF,FAR,FID,CNODESTOP) ;
 N ID S ID=$P(FID,"_") ; Allow for CNode
 Q:$P($G(@FAR@(ID,0)),"^")=""  ; All need an .01 field
 D DICTSTART^FMQLJSON(REPLY)
 N FIELD S FIELD=0 F  S FIELD=$O(^DD(FLINF("FILE"),FIELD)) Q:FIELD'=+FIELD  D
 . N FDINF D BLDFDINF^FMQLUTIL(.FLINF,FIELD,.FDINF)
 . Q:$D(FDINF("BAD"))
 . I FDINF("TYPE")=9 D  ; TBD: loop with walkers and B Index
 . . Q:'$D(@FAR@(ID,FDINF("LOCSUB")))
 . . N NFAR S NFAR=$NA(@FAR@(ID,FDINF("LOCSUB")))
 . . ; Pharma+ case: CNode location but no list params in 0 node
 . . Q:$P($G(@NFAR@(0)),"^",4)=""
 . . ; Using $O to skip missing CNodes, starting after 1 etc.
 . . N BFLINF D BLDFLINF^FMQLUTIL(FDINF("BFILE"),.BFLINF)
 . . ; Ignore if over CNODESTOP
 . . N CCNT S CCNT=0
 . . N BID S BID=0 F  S BID=$O(@NFAR@(BID)) Q:BID'=+BID!(CCNT=CNODESTOP)  S CCNT=CCNT+1
 . . I CCNT'=CNODESTOP  D
 . . . Q:CCNT=0  ; Don't mark empty bnodes (Pharma et al)
 . . . N ISLIST S ISLIST=$S(BFLINF("NOFIELDS")=1:1,1:0)
 . . . D BNLISTSTART^FMQLJSON(REPLY,BFLINF("EFILE"),FDINF("LABEL"),FIELD,ISLIST)
 . . . ; No need for NFAR or BFLINF if FLINF (even if CNode) supports ARRAY
 . . . N BID S BID=0 F  S BID=$O(@NFAR@(BID)) Q:BID'=+BID  D
 . . . . D ONEOFTYPE(REPLY,.BFLINF,NFAR,BID_"_"_FID,CNODESTOP)
 . . . D BNLISTEND^FMQLJSON(REPLY)
 . . E  D BNLISTSTOPPED^FMQLJSON(REPLY,BFLINF("EFILE"),FDINF("LABEL"),FIELD)
 . E  D
 . . I FDINF("FIELD")=.001 D OO1FIELD(ID,.FDINF) Q
 . . D ONEFIELD(FAR,ID,.FDINF) D:FDINF("FIELD")=.01 IDFIELD(.FLINF,FAR,ID,FID)
 ; TBD: properly count SLABS ala other CNodes
 I FLINF("FILE")="63.04",CNODESTOP>0,^TMP($J,"NS")="VS" D BLDBNODES^FMQLSLAB(FAR,FID)
 D DICTEND^FMQLJSON(REPLY)
 Q
 ;
 ;
 ; ID is special. Derived from resolving the .01 field.
 ;
IDFIELD(FLINF,FAR,ID,FID) ;
 ; TBD: is this redundant?
 N O1L S O1L=$P($G(@FAR@(ID,0)),"^")
 ; All records should have a value for .01. TBD: check above.
 ; Saw bug in RPMS (9001021) where index has "^" as name and 0 is "^".
 Q:O1L=""
 N FDINF D BLDFDINF^FMQLUTIL(.FLINF,.01,.FDINF)  ; Assume ok. FLINF checked
 N EVALUE S EVALUE=$$GETEVAL^FMQLUTIL(.FDINF,O1L)
 N PVALUE S PVALUE=$TR(FLINF("FILE"),".","_")_"-"_FID
 N PLABEL S PLABEL=$TR(FLINF("LABEL"),"/","_")_"/"_$TR(EVALUE,"/","_")
 ; SAMEAS ONLY FOR GLOBALS
 N PSAMEAS I $D(FLINF("GL")),$L($T(RESOLVE^FMQLSSAM)) D RESOLVE^FMQLSSAM(FLINF("FILE"),ID,PLABEL,.PSAMEAS)
 D ASSERT^FMQLJSON(REPLY,"URI",".01","7",PVALUE,PLABEL,.PSAMEAS)
 Q
 ;
 ;
 ; Build JSON for one non-CNode Field
 ;
 ; Assume: FDINF is good
 ;
ONEFIELD(FAR,ID,FDINF) ;
 Q:FDINF("TYPE")=6  ; Computed - includes .001
 Q:'$D(@FAR@(ID,FDINF("LOCSUB")))
 I FDINF("TYPE")=5 D
 . ; Pharma+ case: WP location but no entries (ala special case for 9)
 . ; TBD: "" only entry. Seen in RAD, P/H. 
 . Q:'$D(@FAR@(ID,FDINF("LOCSUB"),1))
 . D WPASTART^FMQLJSON(REPLY,FDINF("LABEL"),FDINF("FIELD"))
 . F WPR=1:1 Q:'$D(@FAR@(ID,FDINF("LOCSUB"),WPR))  D
 . . D WPALINE^FMQLJSON(REPLY,@FAR@(ID,FDINF("LOCSUB"),WPR,0))
 . D WPAEND^FMQLJSON(REPLY)
 E  D
 . ; Check as sub values may exist but not the value indicated. 
 . ; Saw WP field's location overloaded for another field 
 . ; (RPMS:811.8 vs VistA's which is ok)
 . Q:$G(@FAR@(ID,FDINF("LOCSUB")))=""
 . N LOCSUB S LOCSUB=@FAR@(ID,FDINF("LOCSUB"))
 . ; For $E values, don't just take the $E limit.
 . N IVALUE S IVALUE=$S($D(FDINF("LOCPOS")):$P(LOCSUB,"^",FDINF("LOCPOS")),1:LOCSUB) Q:IVALUE=""
 . N EVALUE S EVALUE=$$GETEVAL^FMQLUTIL(.FDINF,IVALUE)
 . I FDINF("TYPE")=7 D
 . . N PFLINF D BLDFLINF^FMQLUTIL(FDINF("PFILE"),.PFLINF)
 . . Q:$D(PFLINF("BAD"))
 . . S PVALUE=$TR(PFLINF("FILE"),".","_")_"-"_IVALUE
 . . S PLABEL=$TR(PFLINF("LABEL"),"/","_")_"/"_$TR(EVALUE,"/","_")
 . . N PSAMEAS I $L($T(RESOLVE^FMQLSSAM)) D RESOLVE^FMQLSSAM(PFLINF("FILE"),IVALUE,PLABEL,.PSAMEAS)
 . . D ASSERT^FMQLJSON(REPLY,FDINF("LABEL"),FDINF("FIELD"),"7",PVALUE,PLABEL,.PSAMEAS)
 . E  I FDINF("TYPE")=8 D
 . . N PID S PID=$P(IVALUE,";")
 . . Q:PID'=+PID  ; Corrupt pointer
 . . Q:$P(IVALUE,";",2)=""  ; Corrupt pointer
 . . N LOCZ S LOCZ="^"_$P(IVALUE,";",2)_"0)"  ; 0 has file's description
 . . Q:'$D(@LOCZ)
 . . N PFI S PFI=@LOCZ
 . . N PFILE S PFILE=+$P(PFI,"^",2)
 . . N PFLBL S PFLBL=$TR($P(PFI,"^",1),"/","_")
 . . S PVALUE=$TR(PFILE,".","_")_"-"_PID
 . . S PLABEL=$TR(PFLBL,"/","_")_"/"_$TR(EVALUE,"/","_")
 . . N PSAMEAS I $L($T(RESOLVE^FMQLSSAM)) D RESOLVE^FMQLSSAM(PFILE,PID,PLABEL,.PSAMEAS)
 . . D ASSERT^FMQLJSON(REPLY,FDINF("LABEL"),FDINF("FIELD"),"8",PVALUE,PLABEL,.PSAMEAS)
 . E  D ASSERT^FMQLJSON(REPLY,FDINF("LABEL"),FDINF("FIELD"),FDINF("TYPE"),EVALUE)
 Q
 ;
 ;
 ; .001 is special: its value is the IEN of a record. Nothing is stored inside the file.
 ; Some values (Date, Pointer) should be first class fields.
 ;
OO1FIELD(ID,FDINF)  ;
 N PFLINF,PVALUE,PLABEL,EVALUE,PSAMEAS
 Q:FDINF("TYPE")'=11
 ; IEN is a pointer
 I $D(FDINF("PFILE")) D
 . D BLDFLINF^FMQLUTIL(FDINF("PFILE"),.PFLINF)
 . Q:$D(PFLINF("BAD"))
 . S PVALUE=$TR(PFLINF("FILE"),".","_")_"-"_ID
 . S FDINF("TYPE")=7  ; Overload .001 defn as a pointer
 . S EVALUE=$$GETEVAL^FMQLUTIL(.FDINF,ID)
 . S PLABEL=$TR(PFLINF("LABEL"),"/","_")_"/"_$TR(EVALUE,"/","_")
 . I $L($T(RESOLVE^FMQLSSAM)) D RESOLVE^FMQLSSAM(PFLINF("FILE"),ID,PLABEL,.PSAMEAS)
 . D ASSERT^FMQLJSON(REPLY,FDINF("LABEL"),FDINF("FIELD"),FDINF("TYPE"),PVALUE,PLABEL,.PSAMEAS)
 ; IEN is a date - TODO: issue of DX vs D?
 E  I FDINF("FLAGS")["D" D
 . S FDINF("TYPE")=1
 . S EVALUE=$$GETEVAL^FMQLUTIL(.FDINF,ID)
 . D ASSERT^FMQLJSON(REPLY,FDINF("LABEL"),FDINF("FIELD"),FDINF("TYPE"),EVALUE)
 S FDINF("TYPE")=11
 Q
 ;
 ;
 ; CNTREFS
 ;
 ; Ex/ COUNTREFS 2-9 - count the referrers to entry 9 in file 2
 ;
 ; Unlike generic graph stores that are specialized for 
 ; "SELECT * FILTER(*=2-9)", the strongly typed FileMan
 ; has no central index of referrents. As a result, such
 ; a general query is slow and unnatural. However, a querier
 ; still needs to know about the graph a file entry appears in.
 ; 
 ; This operation is a compromise. It counts references from
 ; appropriately indexed referrers. These counts provide a
 ; starting off point for exploring a file entry's graph.
 ;
 ; In: type, id
 ; Out: total, count per file/field combo
 ;
 ; NB: NOIDXMX is key here. If set too low then certain referrer
 ; grabs will go far too long. This is set in the Python query
 ; processor.
 ;
CNTREFS(REPLY,PARAMS) ;
 I '$D(PARAMS("TYPE")) D ERRORREPLY^FMQLJSON(REPLY,"Type Not Specified") Q
 I '$D(PARAMS("ID")) D ERRORREPLY^FMQLJSON(REPLY,"ID Not Specified") Q
 N NTINF D BLDFLINF^FMQLUTIL(PARAMS("TYPE"),.NTINF)
 I $D(NTINF("BAD")) D ERRORREPLY^FMQLJSON(REPLY,NTINF("BAD")) Q
 I '$D(@NTINF("ARRAY")@(PARAMS("ID"),0)) D ERRORREPLY^FMQLJSON(REPLY,"No such identifier for type "_PARAMS("TYPE")) Q
 N TARGET S TARGET=NTINF("EFILE")_"-"_PARAMS("ID")
 ; NOIDXMX is important. Otherwise the unimportant will take time.
 N NOIDXMX S NOIDXMX=$G(PARAMS("NOIDXMX"))
 S:(NOIDXMX'=+NOIDXMX) NOIDXMX=-1
 N TCNT S TCNT=0
 D REPLYSTART^FMQLJSON(REPLY)
 D LISTSTART^FMQLJSON(REPLY,"results")
 N RFL ; Order referrer types by name
 S FILE="" F  S FILE=$O(^DD(NTINF("FILE"),0,"PT",FILE)) Q:FILE'=+FILE  D
 . N FLINF D BLDFLINF^FMQLUTIL(FILE,.FLINF)
 . Q:($D(FLINF("BAD"))!$D(FLINF("PARENT")))
 . S RFL(FLINF("LABEL"),FILE)=""
 ; Walk referring files in order (know ok as orderer catches bad files)
 S FILELABEL="" F  S FILELABEL=$O(RFL(FILELABEL)) Q:FILELABEL=""  D
 . S FILE="" F  S FILE=$O(RFL(FILELABEL,FILE)) Q:FILE=""  D
 . . N FLINF D BLDFLINF^FMQLUTIL(FILE,.FLINF)
 . . ; Q:FLINF("FMSIZE")<1  ; surely empty files aren't costly
 . . N FIELD S FIELD="" F  S FIELD=$O(^DD(NTINF("FILE"),0,"PT",FILE,FIELD)) Q:FIELD'=+FIELD  D
 . . . N FDINF D BLDFDINF^FMQLUTIL(.FLINF,FIELD,.FDINF)
 . . . I $D(FDINF("BAD")) Q
 . . . I FDINF("TYPE")'=7 Q  ; PTR only for now (no vptr)
 . . . N FLT S FLT=FIELD_"="_NTINF("FILE")_"-"_PARAMS("ID")
 . . . N CNT S CNT=$$XONFL^FMQLUTIL(.FLINF,FLT,"",-1,0,"","",NOIDXMX,"")
 . . . Q:CNT=-1  ; means no idx max exceeded.
 . . . Q:CNT=0 
 . . . D DICTSTART^FMQLJSON(REPLY)
 . . . N FLDLABEL S FLDLABEL=FDINF("LABEL") ; Add predicate
 . . . D DASSERT^FMQLJSON(REPLY,"file",FLINF("EFILE"))
 . . . D DASSERT^FMQLJSON(REPLY,"fileLabel",FILELABEL)
 . . . D DASSERT^FMQLJSON(REPLY,"field",FIELD)
 . . . D DASSERT^FMQLJSON(REPLY,"fieldLabel",FDINF("PRED"))
 . . . D DASSERT^FMQLJSON(REPLY,"count",CNT)
 . . . D DICTEND^FMQLJSON(REPLY)
 . . . S TCNT=TCNT+CNT
 D LISTEND^FMQLJSON(REPLY)
 D DASSERT^FMQLJSON(REPLY,"total",TCNT)
 D DICTSTART^FMQLJSON(REPLY,"fmql")
 D DASSERT^FMQLJSON(REPLY,"OP","COUNT REFS")
 D DASSERT^FMQLJSON(REPLY,"URI",TARGET)
 D DICTEND^FMQLJSON(REPLY)
 D REPLYEND^FMQLJSON(REPLY)
 Q
 ;
