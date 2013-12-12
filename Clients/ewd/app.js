EWD.application = {
  name: 'fmql',
  previous: '',
  current: ''
};

$(document).ready(function() {
  EWD.isReady();
});

EWD.onSocketsReady = function() {
  EWD.application.framework = 'bootstrap';

  $('#loginPanel').on('show.bs.modal', function() {
    setTimeout(function() {
      document.getElementById('username').focus();
    },1000);
  });
  $('#loginPanel').modal({show: true, backdrop: 'static'});

  $('#loginForm').keydown(function(event){
    if (event.keyCode === 13) {
      document.getElementById('loginBtn').click();
    }
  });


  // Login form button handler

  $('body').on( 'click', '#loginBtn', function(event) {
    event.preventDefault();
	event.stopPropagation(); // prevent default bootstrap behavior
    EWD.sockets.submitForm({
      fields: {
        username: $('#username').val(),
        password: $('#password').val()
      },
      messageType: 'EWD.form.login'
    }); 
  });
  $('body').on('click','#FMQLpage', function(event) {
	event.preventDefault();
	event.stopPropagation(); // prevent default bootstrap behavior
	EWD.sockets.submitForm({
      fields: {
        queryText: event.target.attributes['value'].value
      },
      messageType: 'EWD.form.queryText'
    });
	EWD.application.previous = EWD.application.current;
	EWD.application.current = event.target.attributes['value'].value;
  });
  $('body').on('click','#results', function(event) {
	event.preventDefault();
	event.stopPropagation(); // prevent default bootstrap behavior
	var msgValue=event.target.attributes['value'].value;
	console.log('sending: '+msgValue);
	EWD.sockets.sendMessage({
      params: {
        queryText: msgValue
      },
      type: 'FMQL.subquery'
    });
	EWD.application.previous = EWD.application.current;
	EWD.application.current = msgValue;

  });
  $('body').on('click','#previousBtn', function(event) {
	event.preventDefault();
	event.stopPropagation(); // prevent default bootstrap behavior
	if (EWD.application.previous == '') {toastr.error('Nowhere to go back to'); return;}
	if (EWD.application.previous == EWD.application.current) {toastr.error('Can only go back one level. Press submit to restart from top'); return;}
	var msgValue=EWD.application.previous;
	console.log('sending: '+msgValue);
	EWD.sockets.sendMessage({
      params: {
        queryText: msgValue
      },
      type: 'FMQL.subquery'
    });
	EWD.application.current = EWD.application.previous;
  });
  $('body').on('click','#querySub', function(event) {
	event.preventDefault(); // prevent default bootstrap behavior
    event.stopPropagation(); 
    EWD.sockets.submitForm({
      fields: {
        queryText: $('#queryText').val()
      },
      messageType: 'EWD.form.queryText'
    });
	EWD.application.current=$('#queryText').val();
  });
  
  // everything is ready to go:
  // activate login button and the user can start interacting

  document.getElementById('loginBtn').style.display = '';
};

EWD.onSocketMessage = function(messageObj) {
  if (messageObj.type === 'EWD.form.login') {
    // logged in OK - hide login panel
    if (messageObj.ok) $('#loginPanel').modal('hide');
    return;
  }

  if (messageObj.type === 'loggedInAs') {
    $('#loggedInAs').text('Logged in as ' + messageObj.message.fullName);
    return;
  }

	if (messageObj.type === 'FMQLJData') {
	var data=messageObj.message.data;
	console.log('rESULTS RETURNED - '+JSON.stringify(data,'',2));
		if (data.fmql.OP=='SELECT') {markup=selectResultToHTML(data,false,'')}
		else if (data.fmql.OP=='DESCRIBE') {markup=describeResultToHTML(data,false,'')}
		else if (data.fmql.OP=='COUNT REFS') {markup=countRefsResultToHTML(data,false,'',100)}
		else if (data.fmql.OP=='COUNT') {markup='<p>'+data.count+'<p>'}
		else {markup='<p>Cannot display</P>'};
		//markup=describeResultToHTML(data,false);
		$('#resultsTable').html(markup);
		return;
	};
	console.log('other results - '+JSON.stringify(messageObj.message,'',2));
};
