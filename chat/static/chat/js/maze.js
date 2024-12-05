const canvas = document.getElementById('mazeCanvas');
const ctx = canvas.getContext('2d');
const rows = 20, cols = 20;
const cellSize = canvas.width / cols;

let maze = [];
let player1 = { x: 0, y: 0 }; // Starting position for player 1 (Red)
let player2 = { x: cols - 1, y: rows - 1 }; // Starting position for player 2 (Blue)
let playerColor = '';
let turn = 1;

const socket = new WebSocket('ws://' + window.location.host + '/ws/game/');
console.log('ws://' + window.location.host + '/ws/game/')
// Logging function
function log(message) {
    console.log(message);
}

// Draw maze on the canvas
function drawMaze() {
    if (!maze || maze.length === 0) {
        log('Maze data is empty. Unable to draw.');
        return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear previous canvas content
    maze.forEach((row, y) => {
        row.forEach((cell, x) => {
            if (cell === 1) {
                ctx.fillStyle = 'black'; // Walls are black
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
            } else {
                ctx.fillStyle = 'white'; // Empty space is white
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
            }
        });
    });

    // Draw both players
    drawPlayer(player1, 'red');
    drawPlayer(player2, 'blue');
    log('Maze and players drawn on canvas.');
}

// Draw a player on the canvas
function drawPlayer(player, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(
        player.x * cellSize + cellSize / 2,
        player.y * cellSize + cellSize / 2,
        cellSize / 3,
        0,
        Math.PI * 2
    );
    ctx.fill();
}

// Handle WebSocket messages
socket.onopen = function () {
    socket.send(JSON.stringify({ type: 'getPlayerColor' }));
};

socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    console.log("Received data:", data);  // Debugging line to check the data being received

    if (data.type === 'maze') {
        maze = data.maze; // Assign maze data
        player1 = data.player_positions.Red; // Assign initial player positions
        player2 = data.player_positions.Blue;
        playerColor = data.player_color; // Set player's starting color

        updateTurnIndicator(); // Update the turn indicator
        drawMaze(); // Draw the maze after receiving it
    } else if (data.type === 'move') {
        if (data.move.color === 'Red') {
            player1 = { x: data.move.x, y: data.move.y };
        } else if (data.move.color === 'Blue') {
            player2 = { x: data.move.x, y: data.move.y };
        }
        updateTurnIndicator();  // Update the turn indicator
        drawMaze();  // Redraw the maze after the move
    }
};

// Update turn indicator
function updateTurnIndicator() {
    document.getElementById('turnIndicator').textContent = `It's ${playerColor}'s turn`;
}

// WebSocket error handling
socket.onerror = function (error) {
    console.error("WebSocket error:", error);
    alert("An error occurred with the connection.");
};

// WebSocket close handling
socket.onclose = function () {
    console.log("WebSocket connection closed.");
    alert("The game has ended or the connection was lost.");
};
