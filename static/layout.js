$(function() {
    var url = $(location).attr('href');
    var re = /([ \w \d : / ])(calo)(\d+)(.+)/;

    function get_link_callback(calo_num) {
        return function() {
            window.location.replace(url.replace(re, '$1$2' + calo_num + '$4'));
        };
    } 

    for (var i = 1; i < 25; ++i) {
        $('#calo' + i).click(get_link_callback(i));
    }
});