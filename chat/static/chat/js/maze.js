const canvas = document.getElementById('mazeCanvas');
const ctx = canvas.getContext('2d');
const rows = 50, cols = 50;
const cellSize = canvas.width / cols;

let maze = [];
let player1 = { x: 0, y: 0 }; // Red player
let player2 = { x: cols - 1, y: rows - 1 }; // Blue player
let playerColor = '';
let turn = 1; // 1 for Red's turn, 2 for Blue's turn

// Trail colors
let redTrailColor = 'rgba(255, 0, 0, 0.2)';
let blueTrailColor = 'rgba(0, 0, 255, 0.2)';

// WebSocket setup
const socket = new WebSocket('ws://' + window.location.host + '/ws/game/');

// Ensure the canvas fits the maze dimensions
canvas.width = cols * cellSize;
canvas.height = rows * cellSize;

// Initialize maze and players
function initMaze(data) {
    if (!data.maze || typeof data.maze !== 'string' || data.maze.length !== rows * cols) {
        alert("Error: Maze data is invalid.");
        return;
    }

    maze = [];
    // Convert the maze string into a 2D array of 0s and 1s
    for (let i = 0; i < rows; i++) {
        let row = [];
        for (let j = 0; j < cols; j++) {
            row.push(parseInt(data.maze[i * cols + j], 10));  // Parsing each cell
        }
        maze.push(row);
    }

    player1 = data.player_positions.Red;
    player2 = data.player_positions.Blue;
    playerColor = data.player_color;
    console.log(`Player Color: ${playerColor}, Current Turn: ${turn}`);

    updateTurnIndicator();
    drawMaze();
}

// Draw maze and players with trails
function drawMaze() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    maze.forEach((row, y) => {
        row.forEach((cell, x) => {
            if (cell === 1) {
                ctx.fillStyle = 'black'; // Wall
            } else if (cell === 2) {
                ctx.fillStyle = redTrailColor; // Red trail
            } else if (cell === 3) {
                ctx.fillStyle = blueTrailColor; // Blue trail
            } else {
                ctx.fillStyle = 'white'; // Empty space
            }
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        });
    });

    drawPlayer(player1, 'red');
    drawPlayer(player2, 'blue');
}

// Draw a player
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

// Move player and handle trail/turn-switching
function movePlayer(dx, dy) {
    // Ensure it's the player's turn
    if ((playerColor === 'Red' && turn !== 1) || (playerColor === 'Blue' && turn !== 2)) {
        alert("It's not your turn.");
        return;
    }

    let player = playerColor === 'Red' ? player1 : player2;
    const newX = player.x + dx;
    const newY = player.y + dy;

    // Valid move within bounds and not a wall
    if (newX >= 0 && newY >= 0 && newX < cols && newY < rows && maze[newY][newX] !== 1) {
        player.x = newX;
        player.y = newY;

        // Send move to server
        socket.send(JSON.stringify({
            type: 'move',
            move: { color: playerColor, x: player.x, y: player.y }
        }));

        // Switch turn
        turn = (turn === 1) ? 2 : 1;
        updateTurnIndicator();
        drawMaze();
    }
}

// Listen for WebSocket messages
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    switch (data.type) {
        case 'maze':
            initMaze(data);
            break;
        case 'move':
            // Update the other player’s move
            if (data.move.color === 'Red') {
                player1 = data.move;
            } else {
                player2 = data.move;
            }
            drawMaze();
            break;
        case 'turn_update':
            turn = data.turn === 'Red' ? 1 : 2;
            updateTurnIndicator();
            break;
        case 'error':
            alert(data.message);
            break;
        case 'game_win':
            alert(`${data.winner} wins!`);
            break;
    }
};

// Update turn indicator
function updateTurnIndicator() {
    const turnIndicator = document.getElementById("turn-indicator");
    if (turn === 1) {
        turnIndicator.textContent = "Red's Turn";
    } else {
        turnIndicator.textContent = "Blue's Turn";
    }
}

// Add event listeners for player movement
document.addEventListener('keydown', function(event) {
    switch (event.key) {
        case 'ArrowUp': movePlayer(0, -1); break;
        case 'ArrowDown': movePlayer(0, 1); break;
        case 'ArrowLeft': movePlayer(-1, 0); break;
        case 'ArrowRight': movePlayer(1, 0); break;
    }
});
