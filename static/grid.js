$(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('sipm temp', function(msg) {
        $('#sipm'.concat(msg.num)).text(msg.temp + '°');
    });
});
