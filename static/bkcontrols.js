$(document).ready(function() {
	var socket = io.connect('http://' + document.domain + ':' + location.port);

	(function getBkStatus() {
		socket.emit('bk status');
		setTimeout(getBkStatus, 5000);
	})();

	socket.on('bk status', function(msg){
		var num = msg.num;
		console.log('#bk_output'.concat(num));
		if(msg.outstat == '1'){
			$('#bk_output'.concat(num)).text('ON');
			$('#bk_power_button'.concat(num)).text('switch OFF');
		}
		else{
			$('#bk_output'.concat(num)).text('OFF');
			$('#bk_power_button'.concat(num)).text('switch ON');
		}
		$('#bk_output'.concat(num)).show();
		$('#bk_power_button'.concat(num)).show();

		$('#bk_set_pt'.concat(num)).text(msg.voltage + ' V');
		$('#bk_set_pt'.concat(num)).show();
		$('#bk_i_limit'.concat(num)).text(msg.current + ' A');
		$('#bk_i_limit'.concat(num)).show();

		$('#bk_measured'.concat(num)).text(msg.measvolt + ' V');
		$('#bk_measured'.concat(num)).show();
	});

	function getPowerToggleFun(num) {
		return function() {
			socket.emit('toggle bk power', {'num': num});
		};
	}

	function getNewSetPtFun(num, box) {
		return function(e) {
			if(e.which == 13) {
				socket.emit('new voltage pt', {'new setting' : box.val(), 'num' : num });
				box.val('');
			}
		};
	} 

	for (var i = 0; i < 4; ++i){
		var pToggleFunction = getPowerToggleFun(i);
		$('#bk_power_button'.concat(i.toString())).click(pToggleFunction);

		var newSetPtBox = $('#new_set_pt'.concat(i.toString()));
		var newSetPtFunction = getNewSetPtFun(i, newSetPtBox);
		newSetPtBox.keydown(newSetPtFunction);
	}

});
