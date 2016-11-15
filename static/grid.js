$(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('sipm temp', function(msg) {
        $('#sipm'.concat(msg.num)).text(msg.temp + '°');
    });

    var newperiodbox = $('#newperiod');
    newperiodbox.keydown(function(e) {
        if (e.which == 13) {
            socket.emit('new period', newperiodbox.val());
            newperiodbox.val('');
            return false;
        }
    });
});
