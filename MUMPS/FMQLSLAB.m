FMQLSLAB ;CG/CD - Caregraf - FMQL Schema Enhancement for Lab; 07/12/2013  11:30
 ;;1.0;FMQLQP;;Jul 12th, 2013
 ;
 ;
 ;
 ; FMQL Schema Enhancement for Lab (SLAB). 
 ; - peer of SSAM (SAMEAS)
 ;
 ; FMQL Query Processor (c) Caregraf 2010-2013 AGPL
 ; 
 ; Exposes hidden Lab (CH) variables to a blank node pending a set of 
 ; cross references that does this work in an enhanced lab schema. This makes
 ; CH labs look like Radiology and Pharmacy.
 ;
 ; This does similar calculations to (lot's of redundancy in lab):
 ; - HL7 lab: subroutines called from CH^LA7OBX1 from GCPR^LA7QRY
 ; - Lab query routines: TSTRES^LRRPU called from CH^LR7OR2
 ; - Other: CHNODE^LRPXAPI2.m
 ; 
 ; CH data is stored in a proprietary format in FileMan's location for a lab
 ; value. Example ...
 ;   "7.19^^81323.0000!!!4378!!!1^6877^70!4.8!10.8!2!50!!x10 3/uL!1!3^^^^1"
 ; The structure of such values is explained in the code below.
 ;
 ; Note: unlike the VA routines, the code below DOES NOT account for older versions
 ; of the lab package which failed to fill in certain values.
 ;
 ; Issue of inconsistent settings in 60:
 ; VistA seems to allow meaningless definitions in file 60 ...
 ; - numerics with no units? (ex/ GWB, 60-1100, 60-5173)
 ; - references for free texts (ex/ GWB, 60-6135, 60-5826)
 ; - set values with a mix of numeric and text and still get ref ranges and units
 ;   (ex/ GWB, 60-151)
 ; - numeric but interpretation is an explanation (60-5865)
 ; - ... TBD: check type in 60 AND ONLY send ranges, units if numeric.
 ; For now, this extractor DOES not remove such inconsistencies. Must choose the 
 ; right balance between a consistent schema and exposing what the system has.
 ;
 ; TBD:
 ; - panel to lab order. Work correlation - logic in LR7OR1. Custom indexes
 ;   in 68 and 69 to go from a "lab order id" to file 100 id. Not like pharma
 ;   - the id is not called out explicitly in a field
 ; - value of "see comment"
 ; - TYPE: SET vs NUMERIC vs STRING from 60
 ;   - LA7VOBX1: $S("canccomment"[$P(LA7VAL,"^"):1,1:0)
 ;   - OBX2^LA7VOBXA: TYPE
 ; - Partial or Final
 ;   S LA7X=$S("canccommentpending"[$P(LA7VAL,"^"):$P(LA7VAL,"^"),1:"F")
 ;   I LA7RS="C" S LA7X=LA7RS
 ;   S LA7OBX(11)=$$OBX11^LA7VOBX(LA7X)
 ; - Problem of "Free Text" 60 with a unit. ie. if non numeric nix unit
 ; - Critical vs Reference: HL7 V3 HH (High Alert) vs H (High)? Or just expose
 ;   critical and leave interpretation to the client?
 ;
 ;
BLDBNODES(FAR6304,FID) N BID,FLOC,ID,VAL
 S ID=$P(FID,"_")
 S BID=1
 D BNLISTSTART^FMQLJSON(REPLY,"9999999999_6304","CHVALS","9999999999")
 S FLOC=1 F  S FLOC=$O(@FAR6304@(ID,FLOC)) Q:FLOC'=+FLOC  D
 . S VAL=@FAR@(ID,FLOC)
 . D BLDBNODE(FLOC,VAL,BID_"_"_FID)
 . S BID=BID+1
 D BNLISTEND^FMQLJSON(REPLY)
 Q
 ;
BLDBNODE(FLOC,VAL,FID) ;
 ; Start with 60 reference. Must have it or quit.
 N LC S LC=$P(VAL,"^",3)  ; Codes
 Q:LC=""
 N LC60 S LC60=$P(LC,"!",7)  ; 60 ref is in 7th position of code section
 Q:LC60=""
 Q:'$D(^LAB(60,LC60))
 N LABEL60 S LABEL60="LABORATORY TEST/"_$P(^LAB(60,LC60,0),"^")
 ;
 N LVAL S LVAL=$P(VAL,"^")  ; Get Value. TBD: need to check if there is one?
 ;
 ; TBD: FILTER (two values to pick)
 ; Check if test is OK to send - (O)utput or (B)oth
 ; S LA7X=$P(VAL,"^",12)
 ; I LA7X]"","BO"'[LA7X Q
 ; I LA7X="",'$$OKTOSND^LA7VHLU1(LRSS,LRSB,+$P($P(LA7VAL,"^",3),"!",7)) Q
 ;
 D DICTSTART^FMQLJSON(REPLY)
 ;
 ; TMP: giving self 9999999999 as context for FMQL files/subfiles
 D ASSERT^FMQLJSON(REPLY,"URI",".01","7","9999999999_6304-"_$TR(FID,".","_"),"CHBNODE-"_LABEL60)
 ;
 ; Codes (TBD: don't take 64/LOINC. Take from 60->64->95.3)
 ; Result 64. Default to Order 64 (or ""). Nix NaN WKLD code
 ; S:$P(LC,"!")="81323.0000" $P(LC,"!")=""
 ; S:$P(LC,"!",2)="81323.0000" $P(LC,"!",2)=""
 ; N LC64 S LC64=$S($P(LC,"!",2)'="":$P(LC,"!",2),1:$P(LC,"!"))
 ; 0.1 IEN of 60
 ; N SAMEAS60 ; LOINC (95.3) or NLT (64) if available
 ; I $P(LC,"!",3)'="" S SAMEAS60("URI")="95_3-"_$P(LC,"!",3) S SAMEAS60("LABEL")="DUMMYLOINC"
 ; E  I LC64'="" S SAMEAS60("URI")="64-"_LC64 S SAMEAS60("LABEL")="DUMMY64"
 N SAMEAS60
 D RESVS60^FMQLSSAM(LC60,.SAMEAS60)
 D ASSERT^FMQLJSON(REPLY,"TEST",".01","7","60-"_LC60,LABEL60,.SAMEAS60)
 ;
 ; 0.2: Value (complication of "see comment" and type)
 D ASSERT^FMQLJSON(REPLY,"VALUE",".02","4",LVAL)
 ;
 ; 0.11: Method or Site - TBD redo per OBX17^LA7VOBX
 ; Note: Mayo appears here in MMH as one of three options. Goes to WKLD suffix.
 I $P(LC,"!",4) D
 . Q:'$D(^LAB(64.2,$P(LC,"!",4)))
 . N LABEL S LABEL="WKLD SUFFIX CODES/"_$P(^LAB(64.2,$P(LC,"!",4),0),"^")
 . D ASSERT^FMQLJSON(REPLY,"METHOD",".11","7","64_2-"_$P(LC,"!",4),LABEL)
 ;
 ; 0.4: Verify Person
 I $P(VAL,"^",4) D
 . Q:'$D(^DPT($P(VAL,"^",4)))
 . N LABEL S LABEL="NEW PERSON/"_$P(^DPT($P(VAL,"^",4),0),"^")
 . D ASSERT^FMQLJSON(REPLY,"VERIFY PERSON",".04","7","200-"_$P(VAL,"^",4),LABEL)
 ;
 ; Reference Ranges and Unit (Configured in 60.01 Specimen)
 ; take from value as 60.01 may have changed since interpretation
 ; TBD: consider interpretation as coded value for ease of mapping to obsi/H, obsi/L
 N LRU S LRU=$P(VAL,"^",5)  ; Reference Ranges and Unit
 D:$P(LRU,"!",7)'="" ASSERT^FMQLJSON(REPLY,"UNITS",".07","4",$P(LRU,"!",7))
 ; .08: Specimen (61). Also in $P(0,"^",5)
 I $P(LRU,"!") D
 . Q:'$D(^LAB(61,$P(LRU,"!")))
 . N LABEL S LABEL="TOPOGRAPHY FIELD/"_$P(^LAB(61,$P(LRU,"!"),0),"^")
 . D ASSERT^FMQLJSON(REPLY,"SPECIMEN",".08","7","61-"_$P(LRU,"!"),LABEL)
 ; .09,.10: Range - high and low
 ; Ignore criticals (4/5). Use reference. If none, use therapeutic.
 N LRLOW S LRLOW=$S($P(LRU,"!",2)'="":$P(LRU,"!",2),1:$P(LRU,"!",11))
 D:LRLOW'="" ASSERT^FMQLJSON(REPLY,"RANGE LOW",".09","4",LRLOW)
 N LRHIGH S LRHIGH=$S($P(LRU,"!",3)'="":$P(LRU,"!",3),1:$P(LRU,"!",12))
 D:LRHIGH'="" ASSERT^FMQLJSON(REPLY,"RANGE HIGH",".10","4",LRHIGH)
 ;
 ; 0.3: Interpretation (not there for NORMAL or no reference ranges)
 D:$P(VAL,"^",2)'="" ASSERT^FMQLJSON(REPLY,"INTERPRETATION",".03","4",$P(VAL,"^",2))
 ;
 D DICTEND^FMQLJSON(REPLY)
 ;
 Q
 ;
