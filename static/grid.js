$(function() {
    var calonum = parseInt($('calonum').text());

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('sipm temp', function(msg) {
        if (msg.calo == calonum) {
            $('#sipm'.concat(msg.num)).text(msg.temp + '°');
        }
    });

    (function askForTemps() {
        socket.emit('all temps', { 'calo': calonum });
        setTimeout(askForTemps, 10000);
    })();
});
