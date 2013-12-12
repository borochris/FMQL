var jsonld = require('jsonld');
module.exports = {
 
  onSocketMessage: function(ewd) {

    var wsMsg = ewd.webSocketMessage;
    var type = wsMsg.type;
    var params = wsMsg.params;
    var sessid = ewd.session.$('ewd_sessid')._value;
    
    if (type === 'EWD.form.login') {
      console.log('login: ' + JSON.stringify(params));
      if (params.username === '') return 'You must enter a username';
      if (params.password === '') return 'You must enter a password';
      //if (params.username !== 'rob' && params.username !== 'Rob') return 'Invalid login';
      //if (params.password !== 'secret') return 'Invalid login';

      ewd.session.setAuthenticated();

      ewd.sendWebSocketMsg({
        type: 'loggedInAs',
        message: {
          fullName: params.username,
        }
      });
      return ''; 
    };

    if (!ewd.session.isAuthenticated) return;
	if (type === 'EWD.form.queryText' || type==='FMQL.subquery') {
		if (params.queryText === '') return 'no query entered';
		var result = ewd.mumps.function('WRAP^FMQLEWD', sessid, params.queryText);
		var qresult = new ewd.mumps.GlobalNode('%zewdTemp', [sessid]);
		var array = qresult._getDocument();
		//for (var i=0;i<array.length;i++){
		//}
		var bquery=array.join('');
		var jdata=JSON.parse(bquery);
		ewd.sendWebSocketMsg({
			type: 'FMQLJData',
			message: {
				data: jdata
			}
		});
		jsonld.toRDF(jdata, {format: 'application/nquads'}, function(err,nquads) {
			ewd.sendWebSocketMsg({
				type: 'testld',
				message: {
					err:err,
					nquads:nquads
					}
			});
		});
		return 'got '+array.length;
	};
  }
};
