$(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    (function askForGains() {
        socket.emit('all gains');
        setTimeout(askForGains, 10000);
    })();

    socket.on('sipm gain', function(msg) {
        $('#sipm'.concat(msg.num)).text(msg.gain);
    });

    $('#setAllGains').keydown(function(e) {
        if (e.which == 13) {
            socket.emit('set all gains', { 'new_gain': $('#setAllGains').val() });
            $('#setAllGains').val('');
        }
    });

    $('#downloadGains').click(function() {
        console.log('test');
        var fileName = prompt('enter file name (leave out file extension)', '');
        fileName = fileName.replace(/ /g, '');
        //remove unfriendly characters
        fileName = fileName.replace(/[^a-zA-Z0-9-_.]/g, '');
        if (!fileName.length) {
            alert("bad filename!");
        } else {
            window.location.assign('/gainfile_' + fileName);
        }
    });


});


// from https://www.abeautifulsite.net/whipping-file-inputs-into-shape-with-bootstrap-3
$(document).on('change', ':file', function() {
    var input = $(this),
        numFiles = input.get(0).files ? input.get(0).files.length : 1,
        label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
});