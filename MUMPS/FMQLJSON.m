FMQLJSON ;CG/CD - Caregraf - FMQL JSON Builder; 11/26/2013  11:30
 ;;1.1.b;FMQLQP;;Nov 26th, 2013
 ;
 ; FMQL JSON Builder
 ; 
 ; A "class" for building JSON responses
 ; 
 ; FMQL Query Processor (c) Caregraf 2010-2013 AGPL
 ;
ERRORREPLY(REPLY,MSG) ;
 D REPLYSTART^FMQLJSON(.REPLY)
 D DASSERT^FMQLJSON(.REPLY,"error",MSG)
 D REPLYEND^FMQLJSON(.REPLY)
 Q
REPLYSTART(JSON) ;
 S @JSON@("INDEX")=0
 S @JSON@("OFFSET")=1
 S @JSON@(0)=""
 D PUTDATA(JSON,"{")
 S @JSON@("LSTLVL")=0
 S @JSON@("LSTLVL",0)=""
 Q
LISTSTART(JSON,LABEL) ;
 D CONTSTART(JSON,""""_LABEL_""":[")
 Q
DICTSTART(JSON,LABEL) ;
 I $D(LABEL) D CONTSTART(JSON,""""_LABEL_""":{") Q
 D CONTSTART(JSON,"{")
 Q
 ;
 ; List or Dict: both are containers that increase the 'level'. 
 ; Level monitoring comes from JSON's need for commas between multiples, something XML avoids
CONTSTART(JSON,MARK) ;
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))=","
 S @JSON@("LSTLVL")=@JSON@("LSTLVL")+1
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))=""
 D PUTDATA(JSON,MARK)
 Q
ASSERT(JSON,FIELD,IFIELD,FMTYPE,VALUE,PLABEL,PSAMEAS) ;
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))="," ; if next el then put a col before it
 ; TODO: change to pass FDINF which has predicate
 S PRED=$$FIELDTOPRED^FMQLUTIL(FIELD)
 D PUTDATA(JSON,""""_PRED_""":{""fmId"":"""_IFIELD_""",""fmType"":"""_FMTYPE_""",""value"":"""_$$JSONSTRING(VALUE)_"""")
 I $G(PLABEL)'="" D
 . D PUTDATA(JSON,",""type"":""uri"",""label"":"""_$$JSONSTRING(PLABEL)_"""")
 . I $D(PSAMEAS) D
 . . D PUTDATA(JSON,",""sameAs"":"""_PSAMEAS("URI")_"""")
 . . D:$D(PSAMEAS("LABEL")) PUTDATA(JSON,",""sameAsLabel"":"""_$$JSONSTRING(PSAMEAS("LABEL"))_"""")
 E  D
 . I FMTYPE="1" D PUTDATA(JSON,",""type"":""typed-literal"",""datatype"":""xsd:dateTime""") Q
 . I FMTYPE="12" D PUTDATA(JSON,",""type"":""typed-literal"",""datatype"":""xsd:boolean""") Q
 . D PUTDATA(JSON,",""type"":""literal""")
 D PUTDATA(JSON,"}")
 Q
DASSERT(JSON,LVALUE,RVALUE) ;
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))="," ; if next el then put a col before it
 D PUTDATA(JSON,""""_LVALUE_""":"""_$$JSONSTRING(RVALUE)_"""")
 Q
VASSERT(JSON,LVALUE,VALUE) ;
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))="," ; if next el then put a col before it
 D PUTDATA(JSON,""""_LVALUE_""":{""type"":""literal"",""value"":"""_VALUE_"""}")
 Q
WPASTART(JSON,FIELD,IFIELD) ;
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))="," ; if next el then put a col before it
 S @JSON@("LSTLVL")=@JSON@("LSTLVL")+1
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))=""
 D PUTDATA(JSON,""""_$$FIELDTOPRED^FMQLUTIL(FIELD)_""":{""fmId"":"""_IFIELD_""",""fmType"":""5"",""type"":""typed-literal"",""datatype"":""http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral"",""value"":""")
 Q
 ;
 ; May add $$HTML^DILF escape
WPALINE(JSON,LINE) ;
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))="\r" ; if next el then put a col before it
 D PUTDATA(JSON,$$JSONSTRING(LINE))
 Q
WPAEND(JSON) ;
 D CONTEND(JSON,"""}")
 Q
BNLISTSTART(JSON,BFL,BFDLBL,BFD,ISL) ; 
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))=","
 S @JSON@("LSTLVL")=@JSON@("LSTLVL")+1
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))=""
 N ISLJ S ISLJ=$S($G(ISL)=1:",""list"":true",1:"")
 D PUTDATA(JSON,""""_$$FIELDTOPRED^FMQLUTIL(BFDLBL)_""":{""fmId"":"""_BFD_""",""type"":""cnodes"",""file"":"""_BFL_""""_ISLJ_",""value"":[")
 Q
BNLISTEND(JSON) ;
 D CONTEND(JSON,"]}")
 Q
BNLISTSTOPPED(JSON,BFL,BFDLBL,BFD) ;
 D PUTDATA(JSON,@JSON@("LSTLVL",@JSON@("LSTLVL")))
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))=","
 S @JSON@("LSTLVL")=@JSON@("LSTLVL")+1
 S @JSON@("LSTLVL",@JSON@("LSTLVL"))=""
 D PUTDATA(JSON,""""_$$FIELDTOPRED^FMQLUTIL(BFDLBL)_""":{""fmId"":"""_BFD_""",""type"":""cnodes"",""stopped"":""true"",""file"":"""_BFL_"""")
 D CONTEND(JSON,"}")
 Q
DICTEND(JSON) ;
 D CONTEND(JSON,"}")
 Q
LISTEND(JSON) ;
 D CONTEND(JSON,"]")
 Q
CONTEND(JSON,MARKUP) ;
 D PUTDATA(JSON,MARKUP)
 K @JSON@("LSTLVL",@JSON@("LSTLVL"))
 S @JSON@("LSTLVL")=@JSON@("LSTLVL")-1
 Q
REPLYEND(JSON) ;
 D PUTDATA(JSON,"}")
 K @JSON@("LSTLVL")
 K @JSON@("INDEX")
 K @JSON@("OFFSET")
 Q
PUTDATA(JSON,DATA) ;
 S NODESIZE=201 ; TBD: lower (10) slows replies. But little advan over 1024, even slows the small.
 N LEN S LEN=$L(DATA)
 N NUM S NUM=LEN
 N OFFSET S OFFSET=@JSON@("OFFSET")
 N INDEX S INDEX=@JSON@("INDEX")
 I NUM+OFFSET-1>NODESIZE D
 . S NUM=NODESIZE-OFFSET+1
 . S @JSON@(@JSON@("INDEX"))=@JSON@(@JSON@("INDEX"))_$E(DATA,1,NUM)
 . S @JSON@("OFFSET")=1 S @JSON@("INDEX")=INDEX+1 S @JSON@(@JSON@("INDEX"))=""
 . D PUTDATA(JSON,$E(DATA,NUM+1,LEN))
 . Q
 E  D
 . S @JSON@(@JSON@("INDEX"))=@JSON@(@JSON@("INDEX"))_DATA
 . S @JSON@("OFFSET")=@JSON@("OFFSET")+NUM
 . Q
 Q
 ;
 ;
 ; Rules for JSON Values from www.json.org
 ; A JSON Value can be a string in double quotes, number, array, object (dictionary), 
 ; true|false|null.
 ;
 ; For string values
 ; 1. CTRL characters (0-31 except the escaped noted below) are not allowed as themselves.
 ; GT/M using UTF2HEX, Cache using ZHEX
 ; 2. Escape the following with a \
 ; - QUOTE 34 "
 ; - Backslash 92 \
 ; - BS 8 ^H Backspace, works on HP terminals/computers (b)
 ; - HT 9 ^I Horizontal tab, move to next tab stop (t)
 ; - LF 10 ^J Line Feed (n)
 ; - FF 12 ^L Form Feed, page eject (f) 
 ; - CR 13 ^M Carriage Return (r)
 ; 3. From 128->255+. Turn to \u0080 on. Note that "M" or "ASCII"
 ; is just to 255.
 ;
 ; Note: 
 ; - If character set is utf-8, then $L(($C(256))=1 (cheap check).
 ; - not escaping forward slash (47). JSON standard seems to say yes but few encoders
 ;   do this and all decoders accept it as is.
 ;
 ; NOTE: will get warning on GT/M as doesn't like conditional call to Cache's ZHEX.
 ;
JSONSTRING(IN) N ASCII,II,HEX,HH,OUT
 S ASCII(8)="\b"
 S ASCII(9)="\t"
 S ASCII(10)="\n"
 S ASCII(12)="\f"
 S ASCII(13)="\r"
 S ASCII(34)="\"""
 S ASCII(92)="\\"
 S OUT="" F II=1:1:$L(IN) D
 . S ASCII=$A(IN,II)
 . I $G(ASCII(ASCII))'="" S OUT=OUT_ASCII(ASCII) Q
 . I ASCII>31,ASCII<127 S OUT=OUT_$C(ASCII) Q
 . S HEX="" F HH=1:1:4 S HEX=$E("0123456789abcdef",ASCII#16+1)_HEX,ASCII=ASCII\16
 . S OUT=OUT_"\u"_HEX
 . Q
 Q OUT
 ;
