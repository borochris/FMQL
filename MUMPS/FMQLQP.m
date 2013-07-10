FMQLQP; Caregraf - FMQL Query Processor RPC Entry Point ; Jul, 2013
 ;;1.0;FMQLQP;;Jul 12th, 2013
 ;
 ; FMQL RPC
 ; 
 ; Entry point for FMQL RPC
 ; 
 ; FMQL Query Processor (c) Caregraf 2010-2012 AGPL
 ; 
FMQLRPC(RPCREPLY,RPCPARAMS) 
 N FMQLPARAMS,RPCPARAM
 K ^TMP($J,"FMQLJSON")  ; VistA Coding Convention
 I $G(RPCPARAMS)'="" D
 . N RPCPN S RPCPN=1
 . F  S RPCPARAM=$P(RPCPARAMS,"^",RPCPN) Q:RPCPARAM=""  D
 . . S RPCPN=RPCPN+1
 . . S FMQLPARAMS($P(RPCPARAM,":",1))=$P(RPCPARAM,":",2)
 D PROCQRY($NA(^TMP($J,"FMQLJSON")),.FMQLPARAMS)
 S RPCREPLY=$NA(^TMP($J,"FMQLJSON"))
 Q
 ;
PROCQRY(REPLY,FMQLPARAMS) 
 I '$D(FMQLPARAMS("OP")) S @REPLY@(0)="{""error"":""No Operation Specified""}" Q
 ; Schema
 I FMQLPARAMS("OP")="SELECTTYPES" D ALLTYPES^FMQLSCH(REPLY,.FMQLPARAMS) Q
 I FMQLPARAMS("OP")="SELECTTYPEREFS" D ALLREFERRERSTOTYPE^FMQLSCH(.REPLY,.FMQLPARAMS) Q
 I FMQLPARAMS("OP")="DESCRIBETYPE" D DESCRIBETYPE^FMQLSCH(REPLY,.FMQLPARAMS) Q
 ; Data
 I FMQLPARAMS("OP")="COUNTREFS" D CNTREFS^FMQLDATA(REPLY,.FMQLPARAMS) Q
 I ((FMQLPARAMS("OP")="DESCRIBE")&($D(FMQLPARAMS("ID")))) D DESONE^FMQLDATA(REPLY,.FMQLPARAMS) Q
 I ((FMQLPARAMS("OP")="SELECT")!(FMQLPARAMS("OP")="COUNT")!(FMQLPARAMS("OP")="DESCRIBE")) D ALL^FMQLDATA(REPLY,.FMQLPARAMS) Q
 S @REPLY@(0)="{""error"":""No Such Operation: "_FMQLPARAMS("OP")_"""}"
 Q
 ;
