$(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    (function askForPlot() {
        socket.emit('all temps', { 'hours': $('#howManyHours').val() });
        setTimeout(askForPlot, 10000);
    })();

    var allplot = document.getElementById('plot');
    Plotly.newPlot('plot', [], {
        title: 'all SiPMs',
        hovermode: 'closest',
        titlefont: { size: 20 },
        yaxis: { title: 'temperature', titlefont: { size: 20 } },
        showlegend: false
    });
    var nallplottraces = 0;

    var avgplot = document.getElementById('avgplot');
    Plotly.newPlot('avgplot', [], {
        title: 'avg, max, min',
        hovermode: 'closest',
        titlefont: { size: 20 },
        yaxis: { title: 'temperature', titlefont: { size: 20 } },
        showlegend: false
    });
    var startedAvgPlot = false;
    socket.on('all temps ready', function(msg) {
        var alltracesindices = [];
        for (var i = 0; i < nallplottraces; ++i) {
            alltracesindices[i] = i;
        }
        nallplottraces = msg.data.length;
        Plotly.deleteTraces(plot, alltracesindices);
        Plotly.addTraces(plot, msg.data);

        if (startedAvgPlot) {
            Plotly.deleteTraces(avgplot, [0, 1, 2]);
        } else {
            startedAvgPlot = true;
        }
        Plotly.addTraces(avgplot, msg.avgdata);
    });

    $('#howManyHours').keydown(function(e) {
        if (e.which == 13) {
            socket.emit('all temps', { 'hours': $('#howManyHours').val() });
        }
    });
});
