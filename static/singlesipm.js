$(document).ready(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    var sipmNum = parseInt($('#sipmnum').text());

    (function askForPlot() {
        socket.emit('temp plot', { 'num': sipmNum, 'hours': $('#howManyHours').val() });
        setTimeout(askForPlot, 20000);
    })();

    (function askForGain() {
        socket.emit('single gain', { "num": sipmNum });
        setTimeout(askForGain, 10000);
    })();

    function makeHorizontalLine(y) {
        return {
            type: 'line',
            xref: 'paper',
            yref: 'y',
            x0: 0,
            y0: y,
            x1: 1,
            y1: y,
	    line: { color: 'red', dash: 'dash' }
        };
    }

    var plot = document.getElementById('plot');
    Plotly.newPlot('plot', [
    ], {
        yaxis: { title: 'temperature', titlefont: {size: 20}},
    });
    var madePlot = false;
    socket.on('plot ready', function(data) {
        if (data.num == sipmNum) {
	    if (madePlot) {
		Plotly.deleteTraces(plot, 0);
	    } else {
		madePlot = true;
	    }
            Plotly.addTraces(plot, { x: data.x, y: data.y, mode: 'lines' });
            var newlayout = { shapes: [data.plus, data.minus].map(makeHorizontalLine) };
            Plotly.relayout(plot, newlayout);
        }
    });

    socket.on('sipm gain', function(msg) {
        if (msg.num == sipmNum) {
            $('#gainSetting').text(msg.gain);
        }
    });

    $('#howManyHours').keydown(function(e) {
        if (e.which == 13) {
            socket.emit('temp plot', { 'num': sipmNum, 'hours': $('#howManyHours').val() });
        }
    });

    $('#newSetting').keydown(function(e) {
        if (e.which == 13) {
            socket.emit('set gain', { 'num': sipmNum, 'new_gain': $('#newSetting').val() });
            $('#newSetting').val('');
        }
    });
});
