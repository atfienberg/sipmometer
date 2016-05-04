$(document).ready(function() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	var sipmNum = $('#sipmnum').text();

	(function askForPlot() {
		socket.emit('temp plot', {'num' : parseInt(sipmNum)});
		setTimeout(askForPlot, 10000);
	})();

	(function askForGain() {
		socket.emit('single gain', {"num" : sipmNum});
		setTimeout(askForGain, 2000);
	})();

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
			var traceplot = new google.visualization.LineChart(document.getElementById('plot'));
			traceplot.draw(plotdata, options);
		}
	});

	socket.on('sipm gain', function(msg) {
		if (msg.num == sipmNum){
			$('#gainSetting').text(msg.gain);
		}
	});
});