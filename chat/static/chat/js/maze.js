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

function log(message) {
   
}

function initMaze() {
    maze = Array.from({ length: rows }, () => Array(cols).fill(1)); // Initialize maze with walls
    log('Maze initialized with walls.');
}

const directions = [[0, -1], [1, 0], [0, 1], [-1, 0]]; // up, right, down, left

function generateMaze(x = 0, y = 0) {
    maze[y][x] = 0;
    shuffleArray(directions); // Shuffle directions before exploring

    directions.forEach(([dx, dy]) => {
        const nx = x + dx * 2, ny = y + dy * 2;
        if (nx >= 0 && nx < cols && ny >= 0 && ny < rows && maze[ny][nx] === 1) {
            maze[y + dy][x + dx] = 0;
            generateMaze(nx, ny);
        }
    });
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function drawMaze() {
    if (!maze || maze.length === 0) {
        log('Maze data is empty. Unable to draw.');
        return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    maze.forEach((row, y) => {
        row.forEach((cell, x) => {
            if (cell === 1) {
                ctx.fillStyle = 'black';
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
            }
        });
    });

    // Draw both players
    drawPlayer(player1, 'red');
    drawPlayer(player2, 'blue');
    log('Maze and players drawn on canvas.');
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

// Move player on button click
document.getElementById('move-up').addEventListener('click', () => movePlayer(playerColor, 0, -1));
document.getElementById('move-down').addEventListener('click', () => movePlayer(playerColor, 0, 1));
document.getElementById('move-left').addEventListener('click', () => movePlayer(playerColor, -1, 0));
document.getElementById('move-right').addEventListener('click', () => movePlayer(playerColor, 1, 0));

function movePlayer(color, dx, dy) {
    let player = color === 'Red' ? player1 : player2;
    const nx = player.x + dx, ny = player.y + dy;

    if (nx >= 0 && nx < cols && ny >= 0 && ny < rows && maze[ny][nx] === 0) {
        player.x = nx;
        player.y = ny;
        socket.send(JSON.stringify({ move: { color, x: nx, y: ny } }));
       
        drawMaze();
    } else {
       
    }
}

socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    if (data.type === 'maze') {
        maze = data.maze;
        player1 = data.player_positions.Red;
        player2 = data.player_positions.Blue;
        playerColor = data.playerColor;
               drawMaze();
    } else if (data.type === 'move') {
        if (data.move.color === 'Red') {
            player1 = { x: data.move.x, y: data.move.y };
        } else if (data.move.color === 'Blue') {
            player2 = { x: data.move.x, y: data.move.y };
        }
       
        drawMaze();
    }
};

initMaze();
generateMaze();
drawMaze();