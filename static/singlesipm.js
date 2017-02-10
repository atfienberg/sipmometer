$(document).ready(function() {
    var calonum = parseInt($('calonum').text());

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    var sipmNum = parseInt($('#sipmnum').text());

    (function askForGain() {
        socket.emit('single gain', { 'calo': calonum, 'num': sipmNum });
        setTimeout(askForGain, 10000);
    })();

    socket.on('sipm values', function(msg) {
        if (msg.num == sipmNum && msg.calo == calonum) {
            $('#gainSetting').text(msg.gain);
            $('#temp').text(msg.temp + '°');
        }
    });

    $('#newSetting').keydown(function(e) {
        if (e.which == 13) {
            socket.emit('set gain', { 'calo': calonum, 'num': sipmNum, 'new_gain': $('#newSetting').val() });
            $('#newSetting').val('');
        }
    });
});
