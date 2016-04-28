$(document).ready(function() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	(function askForGains() {
		socket.emit('all gains');
		setTimeout(askForGains, 2000);
	})();

	socket.on('sipm gain', function(msg) {
		$('#sipm'.concat(msg.num)).text(msg.gain);	
	});
});