const canvas = document.getElementById('mazeCanvas');
const ctx = canvas.getContext('2d');
const rows = 50, cols = 50;
const cellSize = canvas.width / cols;


let maze = [];
let player1 = { x: 0, y: 0 }; // Red player
let player2 = { x: cols - 1, y: rows - 1 }; // Blue player
let playerColor = '';
let turn = 1; // 1 for Red's turn, 2 for Blue's turn
const socket = new WebSocket('ws://' + window.location.host + '/ws/game/');

// Initialize maze and players
function initMaze(data) {
    if (!data.maze || typeof data.maze !== 'string' || data.maze.length !== rows * cols) {
        console.error("Invalid maze data received:", data.maze);
        alert("Error: Maze data is invalid.");
        return;
    }

    maze = [];
    for (let i = 0; i < rows; i++) {
        maze.push(data.maze.slice(i * cols, (i + 1) * cols).split('').map(Number));
    }

    player1 = data.player_positions.Red;
    player2 = data.player_positions.Blue;
    playerColor = data.player_color;

    console.log("Maze initialized:", maze);
    console.log("Player positions initialized:", { player1, player2 });
    console.log(`You are playing as: ${playerColor}`);

    updateTurnIndicator();
    drawMaze();
}


// Draw the maze and players
function drawMaze() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    maze.forEach((row, y) => {
        row.forEach((cell, x) => {
            if (cell === 1) {
                ctx.fillStyle = 'black';
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
            }
        });
    });
    drawPlayer(player1, 'red');
    drawPlayer(player2, 'blue');
}


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

// Move player based on button clicks
function movePlayer(dx, dy) {
    if ((playerColor === 'Red' && turn !== 1) || (playerColor === 'Blue' && turn !== 2)) {
        alert("It's not your turn.");
        return;
    }

    let player = playerColor === 'Red' ? player1 : player2;
    const nx = player.x + dx, ny = player.y + dy;

    console.log(`${playerColor} player is attempting to move to: (${nx}, ${ny})`);

    // Boundary and maze existence check
    if (nx >= 0 && nx < cols && ny >= 0 && ny < rows && maze[ny] && maze[ny][nx] === 0) {
        player.x = nx;
        player.y = ny;

        console.log(`${playerColor} player moved successfully to: (${nx}, ${ny})`);
        socket.send(JSON.stringify({ move: { color: playerColor, x: nx, y: ny } }));
    } else {
        console.warn(`${playerColor} player attempted an invalid move to: (${nx}, ${ny})`);
        alert("Invalid move.");
    }
}

// WebSocket events
socket.onopen = function () {
    console.log("WebSocket connection established.");
    socket.send(JSON.stringify({ type: 'getPlayerColor' }));
};

socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    console.log("Message received from server:", data);

    if (data.type === 'maze') {
        initMaze(data);
    } else if (data.type === 'move') {
        console.log(`${data.move.color} player moved to: (${data.move.x}, ${data.move.y})`);
        if (data.move.color === 'Red') {
            player1 = { x: data.move.x, y: data.move.y };
        } else if (data.move.color === 'Blue') {
            player2 = { x: data.move.x, y: data.move.y };
        }
        drawMaze();
        updateTurnIndicator();
    } else if (data.type === 'error') {
        console.error("Error from server:", data.message);
        alert(data.message);
    }
};

socket.onerror = function (error) {
    console.error("WebSocket error:", error);
    alert("An error occurred with the connection.");
};

socket.onclose = function () {
    console.warn("WebSocket connection closed.");
    alert("The game has ended or the connection was lost.");
};

// Button event listeners for movement
document.getElementById('move-up').addEventListener('click', () => movePlayer(0, -1));
document.getElementById('move-down').addEventListener('click', () => movePlayer(0, 1));
document.getElementById('move-left').addEventListener('click', () => movePlayer(-1, 0));
document.getElementById('move-right').addEventListener('click', () => movePlayer(1, 0));

// Turn indicator
function updateTurnIndicator() {
    const turnPlayer = turn === 1 ? 'Red' : 'Blue';
    document.getElementById('turnIndicator').textContent = `It's ${turnPlayer}'s turn`;
    console.log(`Turn updated: It's ${turnPlayer}'s turn.`);
}
