$(function() {
    var calonum = parseInt($('calonum').text());
    if (isNaN(calonum)) {
	calonum = 25;
    }

    var numBKS = calonum == 25 ? 1 : 4;

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    (function getBkStatus() {
        socket.emit('bk status', { 'calo': calonum });
        setTimeout(getBkStatus, 5000);
    })();

    socket.on('bk status', function(msg) {
        if (msg.calo == calonum) {
            var num = msg.num;
            if (msg.outstat == '1') {
                $('#bk_output'.concat(num)).text('ON');
                $('#bk_power_button'.concat(num)).text('switch OFF');
            } else {
                $('#bk_output'.concat(num)).text('OFF');
                $('#bk_power_button'.concat(num)).text('switch ON');
            }
            $('#bk_output'.concat(num)).show();
            $('#bk_power_button'.concat(num)).show();

            $('#bk_set_pt'.concat(num)).text(msg.voltage + ' V');
            $('#bk_set_pt'.concat(num)).show();
            $('#bk_i_limit'.concat(num)).text(msg.current + ' A');
            $('#bk_i_limit'.concat(num)).show();

            $('#bk_i_output'.concat(num)).text(msg.meascurr + ' A');
            $('#bk_i_output'.concat(num)).show();

            $('#bk_measured'.concat(num)).text(msg.measvolt + ' V');
            $('#bk_measured'.concat(num)).show();
        }
    });

    function getPowerToggleFun(num, box) {
        return function() {
            socket.emit('toggle bk power', { 'num': num, 'calo': calonum, 'on': box.text() === 'switch ON' });
        };
    }

    function getNewSetPtFun(num, box) {
        return function(e) {
            if (e.which == 13) {
                socket.emit('new voltage pt', { 'new setting': box.val(), 'num': num, 'calo': calonum });
                box.val('');
            }
        };
    }

    for (var i = 1; i <= numBKS; ++i) {
        var toggleBox = $('#bk_power_button'.concat(i.toString()));
        var pToggleFunction = getPowerToggleFun(i, toggleBox);
        toggleBox.click(pToggleFunction);

        var newSetPtBox = $('#new_set_pt'.concat(i.toString()));
        var newSetPtFunction = getNewSetPtFun(i, newSetPtBox);
        newSetPtBox.keydown(newSetPtFunction);
    }

    // T0 specific functions for caen
    if (calonum == 25) {
	(function getCaenStatus() {
	    socket.emit('caen status');
	    setTimeout(getCaenStatus, 3333);
	})();
	

	function caenNewSetPtFun(num, box) {
	    return function(e) {
		if (e.which == 13) {
		    socket.emit('new caen voltage', { 'new setting': box.val(), 'chan': num});
		    box.val('');
		}
	    };
	}


	function caenPowerToggleFunction(num, box) {
	    return function() {
		socket.emit('toggle caen power', { 'chan': num, 'on': box.text() === 'switch ON' });
	    };
	}
	
	for (var chan = 0; chan < 4; ++chan) {
	    var setbox = $('#caen_new_set_pt' + chan);
	    setbox.keydown(caenNewSetPtFun(chan, setbox));

	    var togglebox = $('#caen_power_button' + chan);
	    togglebox.click(caenPowerToggleFunction(chan, togglebox));
	}

	socket.on('caen status', function(data) {
		for (var chan_num = 0; chan_num < data.length; ++chan_num) {
		    var msg = data[chan_num];
		    if (msg.outstat == '1') {
			$('#caen_output'.concat(chan_num)).text('ON');
			$('#caen_power_button'.concat(chan_num)).text('switch OFF');
		    } else {
			$('#caen_output'.concat(chan_num)).text('OFF');
			$('#caen_power_button'.concat(chan_num)).text('switch ON');
		    }
		    $('#caen_output'.concat(chan_num)).show();
		    $('#caen_power_button'.concat(chan_num)).show();

		    $('#caen_set_pt'.concat(chan_num)).text(msg.voltage + ' V');
		    $('#caen_set_pt'.concat(chan_num)).show();

		    $('#caen_i_output'.concat(chan_num)).text(msg.meascurr + '  µA');
		    $('#caen_i_output'.concat(chan_num)).show();
		}
	    });
    }
});
