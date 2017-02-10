$(function() {
    var calonum = parseInt($('calonum').text());

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    var gains = {};

    for (var i = 0; i < 54; ++i) {
        var sipmkey = 'sipm' + i;
        if ($('#' + sipmkey).length) {
            gains[sipmkey] = $('#' + sipmkey).text();
        }
    }

    $('#accept').click(function() {
        socket.emit('set these gains', { 'gains': gains, 'calo': calonum });
        window.location.assign('/calo' + calonum + '/gaingrid');
    });

});
