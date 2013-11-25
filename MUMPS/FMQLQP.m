FMQLQP ;CG/CD - Caregraf - FMQL Query Processor Entry Point; 11.25.2013  11:30
 ;;1.1b;FMQL;;Nov 25th, 2013
 ;
 ; FMQL Query Processor Entry Point
 ; 
 ; FMQL Query Processor (c) Caregraf 2010-2013 AGPL
 ; 
 ;
 ; Process Query
 ; support RPC or Web serializing friendly ^TMP holding JSON response 
 ; example: QUERY(.REPLY,"DESCRIBE 2-9") will describe the 9th entry in
 ; file 2 into ^TMP($J,"FMQLJSON")
 ; 
QUERY(REPLY,QUERY) ;
 N PARAMS,PRSRES
 ; Note: storing in TMP for large JSON and older Cache-based systems
 K ^TMP($J,"FMQLJSON")  ; VistA Coding Convention
 ; Need to identify namespace of FM (VISTA or C***)
 K ^TMP($J,"NS") S ^TMP($J,"NS")=$S($P(^DIC(4.3,0),"^")="KERNEL SITE PARAMETERS":"C***",1:"VS")
 S PRSRES=$$PRSQUERY(QUERY,.PARAMS)
 I PRSRES'="" S ^TMP($J,"FMQLJSON",0)="{""error"":""Bad Query Form: "_PRSRES_"""}"
 E  D PROCQRY($NA(^TMP($J,"FMQLJSON")),.PARAMS)
 S REPLY=$NA(^TMP($J,"FMQLJSON"))
 Q
 ;
FMQLRPC(RPCREPLY,RPCARG) ;
 D QUERY(.RPCREPLY,RPCARG)
 Q
 ; 
 ;
 ; PRSQUERY
 ; - invoke by S RESULT=$$PRSQUERY(INPUT,.PARAMS)
 ; ... returns a parse error when the INPUT is invalid, otherwise ""
 ;
 ; TODO: 
 ; - fully 'eat' input
 ; - support SELECT fld FROM fid
 ; - ) inside filter (last ))
 ; - default values (noidxmax, cstop)
 ; - move unescape for HTTP out of here (responsibility of stack)
 ;
PRSQUERY(INPUT,PARAMS) ;
 N ERROR,QRYDEFS,OP,VAL,QUAL,TOKEN,NSTRT,NEND,INPUTTV,CHECK
 S ERROR=""
 S QRYDEFS("SELECT","TYPE","LIMIT")="NUM"
 S QRYDEFS("SELECT","TYPE","OFFSET")="NUM"
 S QRYDEFS("SELECT","TYPE","AFTERIEN")="NUM"
 S QRYDEFS("SELECT","TYPE","NOIDXMAX")="NUM"
 S QRYDEFS("COUNT","TYPE","LIMIT")="NUM"
 S QRYDEFS("COUNT","TYPE","OFFSET")="NUM"
 S QRYDEFS("COUNT","TYPE","AFTERIEN")="NUM"
 S QRYDEFS("COUNT","TYPE","NOIDXMAX")="NUM"
 S QRYDEFS("COUNT REFS","QID")=""
 S QRYDEFS("DESCRIBE","QID","CSTOP")="NUM"
 S QRYDEFS("DESCRIBE","TYPE","LIMIT")="NUM"
 S QRYDEFS("DESCRIBE","TYPE","OFFSET")="NUM"
 S QRYDEFS("DESCRIBE","TYPE","AFTERIEN")="NUM"
 S QRYDEFS("DESCRIBE","TYPE","CSTOP")="NUM"
 S QRYDEFS("DESCRIBE","TYPE","NOIDXMAX")="NUM"
 S QRYDEFS("DESCRIBE","TYPE","IN")="QID"
 S QRYDEFS("SELECT TYPES","NONE","TOPONLY")=""
 S QRYDEFS("SELECT TYPES","NONE","POPONLY")=""
 S QRYDEFS("SELECT TYPE REFS","TYPE")=""
 S QRYDEFS("DESCRIBE BADTYPES","NONE")=""
 S QRYDEFS("DESCRIBE TYPE","TYPE","FULL")=""
 ; Account for %20 if query over HTTP is not unescaped
 D UNESCSP(.INPUT)
 ; OP must be at start and can have spaces so loop to find
 D SKPWHITE(.INPUT)
 ; Go through all OPs each time - longest at end of list
 S OP="" F  S OP=$O(QRYDEFS(OP)) Q:OP=""  D
 . S VAL=$E(INPUT,1,$L(OP))
 . ; Either space is next or OP takes up whole input
 . Q:'($L(OP)=$L(INPUT)!($A(INPUT,$L(OP)+1)=32))
 . I VAL=OP S PARAMS("FOP")=OP S PARAMS("OP")=$$EXTTOINT(OP) Q
 I '$D(PARAMS("OP")) S ERROR="OP MISSING"
 Q:ERROR'="" ERROR
 S OP=PARAMS("FOP")
 D EATINP(.INPUT,OP)
 S QUAL="NONE"
 I '$D(QRYDEFS(OP,"NONE")) D
 . S VAL=$$PRSINP(.INPUT)
 . ; QID form ends in E to allow for non numeric 'meaningful' IENs
 . I $D(QRYDEFS(OP,"QID")),VAL?0.N0.1"_"1.N1"-"1.E S PARAMS("TYPE")=$P(VAL,"-",1) S QUAL="QID" S PARAMS("ID")=$P(VAL,"-",2) Q
 . I $D(QRYDEFS(OP,"TYPE")),VAL?0.N0.1"_"1.N S QUAL="TYPE" S PARAMS("TYPE")=VAL Q  
 . S ERROR="TYPE MISSING"
 Q:ERROR'="" ERROR
 ; Take out FILTER text before looking at other arguments. It may contain those arguments as keywords. NOIDXMAX is a proxy for FILTER support.
 I $D(QRYDEFS(OP,QUAL,"NOIDXMAX")) D
 . S NSTRT=$F(INPUT,"FILTER")
 . Q:NSTRT=0
 . ; TODO: allow embedded brackets
 . S NEND=$F(INPUT,")",NSTRT)
 . I NEND=0 S ERROR="FILTER ) MISSING" Q
 . S VAL=$E(INPUT,NSTRT,NEND-1)
 . D SKPWHITE(.VAL)
 . I $E(VAL,1)'="(" S ERROR="FILTER ( MISSING" Q
 . S PARAMS("FILTER")=$E(VAL,2,$L(VAL)-1) ; less brackets
 . ; Redo INPUT to remove FILTER entirely
 . S INPUT=$E(INPUT,1,NSTRT-$L("FILTER")-1)_$E(INPUT,NEND,$L(INPUT))
 Q:ERROR'="" ERROR
 S TOKEN="" F  S TOKEN=$O(QRYDEFS(OP,QUAL,TOKEN)) Q:TOKEN=""!(ERROR'="")  D
 . S NSTRT=$F(INPUT,TOKEN)
 . Q:NSTRT=0  ; TOKEN not found  
 . ; TOKEN only argument - by convention make value = 1
 . I QRYDEFS(OP,QUAL,TOKEN)="" S PARAMS(TOKEN)=1 Q
 . S INPUTTV=$E(INPUT,NSTRT,$L(INPUT))  ; There is an argument
 . S VAL=$$PRSINP(.INPUTTV," ",0)
 . S CHECK=$S(QRYDEFS(OP,QUAL,TOKEN)="NUM":VAL?1.N,QRYDEFS(OP,QUAL,TOKEN)="QID":VAL?0.N0.1"_"1.N1"-"1.N,1:1)
 . I CHECK=0 S ERROR="INVALID VALUE FOR "_TOKEN Q
 . S PARAMS($$EXTTOINT(TOKEN))=VAL
 Q:ERROR'="" ERROR
 Q ""
 ;
PROCQRY(REPLY,FMQLPARAMS) ;
 I '$D(FMQLPARAMS("OP")) S @REPLY@(0)="{""error"":""No Operation Specified""}" Q
 ; Schema
 I FMQLPARAMS("OP")="SELECT TYPES" D ALLTYPES^FMQLSCH(REPLY,.FMQLPARAMS) Q
 I FMQLPARAMS("OP")="DESCRIBE BADTYPES" D BADTYPES^FMQLSCH(REPLY,.FMQLPARAMS) Q
 I FMQLPARAMS("OP")="SELECT TYPE REFS" D ALLREFERRERSTOTYPE^FMQLSCH(.REPLY,.FMQLPARAMS) Q
 I FMQLPARAMS("OP")="DESCRIBE TYPE" D DESCRIBETYPE^FMQLSCH(REPLY,.FMQLPARAMS) Q
 ; Data
 I FMQLPARAMS("OP")="COUNT REFS" D CNTREFS^FMQLDATA(REPLY,.FMQLPARAMS) Q
 I ((FMQLPARAMS("OP")="DESCRIBE")&($D(FMQLPARAMS("ID")))) D DESONE^FMQLDATA(REPLY,.FMQLPARAMS) Q
 I ((FMQLPARAMS("OP")="SELECT")!(FMQLPARAMS("OP")="COUNT")!(FMQLPARAMS("OP")="DESCRIBE")) D ALL^FMQLDATA(REPLY,.FMQLPARAMS) Q
 S @REPLY@(0)="{""error"":""No Such Operation: "_FMQLPARAMS("OP")_"""}"
 Q
 ;
 ; 
 ; TODO: internal code uses slightly different names for some parameters
 ;
EXTTOINT(EXTNAME) ;
 I EXTNAME="NOIDXMAX" Q "NOIDXMX"
 I EXTNAME="CSTOP" Q "CNODESTOP"
 Q EXTNAME
 ;
 ;
 ; 
 ;
PRSINP(INPUT,SEP,EAT) ;
 N VAL
 S:'$D(SEP) SEP=" "
 S:'$D(EAT) EAT=1
 D SKPWHITE(.INPUT)
 S VAL=$P(INPUT,SEP,1)
 I EAT D EATINP(.INPUT,VAL)
 Q VAL
 ;
 ;
 ;
 ;
EATINP(INPUT,VAL) ;
 S INPUT=$E(INPUT,$L(VAL)+1,$L(INPUT))
 Q
 ;
 ;
 ;
 ;
SKPWHITE(INPUT) ;
 N IDX,NEXT,DONE
 S IDX=1
 S DONE=0 F  D  Q:DONE
 . S NEXT=$E(INPUT,IDX)
 . I NEXT="" S DONE=1 Q
 . I $A(NEXT)>32 S DONE=1 Q
 . S IDX=IDX+1
 Q:IDX=1
 S INPUT=$E(INPUT,IDX,$L(INPUT))
 Q
 ;
UNESCSP(INPUT) ;
 N NEXT,DONE
 S DONE=0 F  D  Q:DONE
 . S NEXT=$F(INPUT,"%20")
 . I NEXT=0 S DONE=1 Q
 . S INPUT=$E(INPUT,1,NEXT-4)_" "_$E(INPUT,NEXT,$L(INPUT))
 Q

