$(document).ready(function() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	(function askForPlot() {
		socket.emit('all temps');
		setTimeout(askForPlot, 10000);
	})();

	socket.on('all temps ready', function(msg) {
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
			fontSize: 18
		};
		var traceplot = new google.visualization.LineChart(document.getElementById('plot'));
		traceplot.draw(plotdata, options);
	});
});