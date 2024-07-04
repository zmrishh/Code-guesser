// Connect to the Socket.IO server
var socket = io();

// Function to join the game room and initialize game
function joinGame(username) {
    socket.emit('join_game', username);
}

// Handle receiving the code from server and display
socket.on('code', function(code) {
    document.getElementById('codeDisplay').innerText = code;
    document.getElementById('chat').innerHTML = '';
});

// Handle receiving feedback messages from server
socket.on('feedback', function(feedback) {
    document.getElementById('feedback').innerText = feedback;
});

// Handle receiving chat messages from server
socket.on('message', function(msg) {
    var chat = document.getElementById('chat');
    chat.innerHTML += '<p>' + msg + '</p>';
    chat.scrollTop = chat.scrollHeight;
});

// Function to send a guess to the server
function sendGuess() {
    var message = document.getElementById('message').value;
    socket.emit('guess', message);
    document.getElementById('message').value = '';
}

// Handle new round initialization from server (reset UI, timer, etc.)
socket.on('new_round', function() {
    document.getElementById('feedback').innerText = '';
    document.getElementById('message').value = '';
    startTimer();
});

// Countdown timer functionality
var timer = null;

function startTimer() {
    var timeLeft = 60; // seconds for each round

    timer = setInterval(function() {
        timeLeft--;
        document.getElementById('timer').innerText = "Time Left: " + timeLeft + "s";

        if (timeLeft <= 0) {
            clearInterval(timer);
            socket.emit('time_up');
        }
    }, 1000);
}
