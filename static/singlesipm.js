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
            line: { color: 'red' }
        };
    }

    var plot = document.getElementById('plot');
    Plotly.newPlot('plot', [
        { y: [] }
    ], {
        titlefont: { size: 20 },
        yaxis: { title: 'temperature' },
    });
    socket.on('plot ready', function(msg) {
        if (msg.num == sipmNum) {
            Plotly.deleteTraces(plot, 0);
            Plotly.addTraces(plot, { x: data.x, y: data.y, type: 'line' });

            var newlayout = { shapes: [data.plus, data.minus].map(makeHorizontalLine) };
            Plotly.relayout(newlayout);
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
