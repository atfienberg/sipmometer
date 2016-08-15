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

	var traceplot = new google.visualization.LineChart(document.getElementById('plot'));
	socket.on('plot ready', function(msg) {
		if (msg.num == sipmNum){
			var plotdata = google.visualization.arrayToDataTable(msg.data);
			var options = {
				curveType: 'function',
				legend: 'none',
				hAxis: {
					title: "time"
				},
				vAxis: {
					title: "temp"
				},
				colors: ['blue', 'red', 'red'],
				series: {
					0: { lineDashStyle: [0, 0] },
					1: { lineDashStyle: [2, 2] },
					2: { lineDashStyle: [2, 2] }
				},
				fontSize: 18
			};
			traceplot.draw(plotdata, options);
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
