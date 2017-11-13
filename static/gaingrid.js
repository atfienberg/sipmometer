$(function() {
    var calonum = parseInt($('calonum').text());

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    (function askForGains() {
        socket.emit('all gains', { 'calo': calonum });
        setTimeout(askForGains, 10000);
    })();

    socket.on('sipm gain', function(msg) {
        if (msg.calo == calonum) {
            $('#sipm'.concat(msg.num)).text(msg.gain);
        }
    });

    $('#setAllGains').keydown(function(e) {
        if (e.which == 13) {
            socket.emit('set all gains', { 'calo': calonum, 'new_gain': $('#setAllGains').val() });
            $('#setAllGains').val('');
        }
    });

    $('#downloadGains').click(function() {
        var fileName = prompt('enter file name (leave out file extension)', '');
        fileName = fileName.replace(/ /g, '');
        //remove unfriendly characters
        fileName = fileName.replace(/[^a-zA-Z0-9-_.]/g, '');
        if (!fileName.length) {
            alert("bad filename!");
        } else {
            window.location.assign('/calo' + calonum + '/gainfile_' + fileName);
        }
    });

    $('#reloadSettings').click(function() {
        var runNum = prompt('enter desired run number (last for most recent)', '');
        if (runNum.length) {
            socket.emit('reload calo settings', { calo: calonum, run: runNum });
        }
    });


    socket.on('reload response', function(response) {
        alert(response);
    });
});