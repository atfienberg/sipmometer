$(document).ready(function() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	(function askForPlot() {
		socket.emit('all temps', {'hours': $('#howManyHours').val()});
		setTimeout(askForPlot, 10000);
	})();

	var traceplot = new google.visualization.LineChart(document.getElementById('plot'));
	var avgtraceplot = new google.visualization.LineChart(document.getElementById('avgplot'));
	socket.on('all temps ready', function(msg) {
		var plotdata = google.visualization.arrayToDataTable(msg.data);
		var options = {
			title: 'all',
			curveType: 'function',
			legend: 'none',
			hAxis: {
				title: "time"
			},
			vAxis: {
				title: "temp"
			},
			fontSize: 18
		};
		traceplot.draw(plotdata, options);

		var avgplotdata = google.visualization.arrayToDataTable(msg.avgdata);
		var avgoptions = {
			curveType: 'function',
			legend: 'none',
			hAxis: {
				title: "time"
			},
			vAxis: {
				title: "temp"
			},
			fontSize: 18,
			title: 'average, max, min'
		};
		avgtraceplot.draw(avgplotdata, avgoptions);
	});

	$('#howManyHours').keydown(function(e) {
		if (e.which == 13) {
			socket.emit('all temps', {'hours': $('#howManyHours').val()});
		}
	});
});