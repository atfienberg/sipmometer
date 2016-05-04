$(document).ready(function() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	(function askForPlot() {
		socket.emit('all temps');
		setTimeout(askForPlot, 10000);
	})();

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
		var traceplot = new google.visualization.LineChart(document.getElementById('plot'));
		traceplot.draw(plotdata, options);

		var avgplotdata = google.visualization.arrayToDataTable(msg.avgdata);
		var avgoptions = {
			curveType: 'function',
			legend: 'none',
			hAxis: {
				title: "time"
			},
			vAxis: {
				title: "avg temp"
			},
			fontSize: 18,
			title: 'average, max, min'
		};
		var avgtraceplot = new google.visualization.LineChart(document.getElementById('avgplot'));
		avgtraceplot.draw(avgplotdata, avgoptions);
	});
});