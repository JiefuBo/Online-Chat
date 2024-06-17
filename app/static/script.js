$(document).ready(function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    socket.on('message', function(data) {
        $('#messages').append('<p>' + data.user + ': ' + data.msg + '</p>');
    });

    window.sendMessage = function() {
        var msg = $('#message').val();
        socket.emit('message', {msg: msg});
        $('#message').val('');
    };
});
