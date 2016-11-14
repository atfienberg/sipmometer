$(document).ready(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    var sipmNum = parseInt($('#sipmnum').text());

    (function askForPlot() {
	socket.emit('temp plot', {'num' : sipmNum, 'hours': $('#howManyHours').val()});
	setTimeout(askForPlot, 20000);
    })();

    (function askForGain() {
	socket.emit('single gain', {"num" : sipmNum});
	setTimeout(askForGain, 10000);
    })();

    var traceplot = document.getElementById('plot');
    
    socket.on('plot ready', function(msg) {
	if (msg.num == sipmNum){

	}
    });

    socket.on('sipm gain', function(msg) {
	if (msg.num == sipmNum){
	    $('#gainSetting').text(msg.gain);
	}
    });

    $('#howManyHours').keydown(function(e) {
	if (e.which == 13) {
	    socket.emit('temp plot', {'num' : sipmNum, 'hours': $('#howManyHours').val()});	
	}
    });

    $('#newSetting').keydown(function(e) {
	if (e.which == 13) {
	    socket.emit('set gain', {'num' : sipmNum, 'new_gain' : $('#newSetting').val()});
	    $('#newSetting').val('');
	}
    });
});
