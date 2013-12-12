FMQLEWD	;CPC - CPC Computer Solutions - FMQL EWD wrappers; 12/30/2013 12:42
	;;1.1;FMQLQP;;Oct 30th, 2013
	;
WRAP(pid,QUERY)
	N QUERYOUT
	s QUERYOUT=QUERY
	;s ^cpc=QUERY
	;S QUERYOUT="OP:"_$P(QUERY," ",1)_"^"_TYPE:"_$P($P(QUERY," ",2),"_",1)_"^"_$S(
	d FMQLRPC^FMQLQP("CPC",QUERYOUT)
	K ^%zewdTemp(pid)
	m ^%zewdTemp(pid)=^TMP($J,"FMQLJSON")
	Q ""