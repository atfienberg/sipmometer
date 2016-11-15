$(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    (function askIfLogging() {
        socket.emit('logging?');
        setTimeout(askIfLogging, 500);
    })();

    socket.on('logging status', function(msg) {
        if (msg.logging) {
            $('#stopLink').show();
            $('#loggingStopped').hide();
        } else {
            $('#stopLink').hide();
            $('#loggingStopped').show();
        }
    });
});
