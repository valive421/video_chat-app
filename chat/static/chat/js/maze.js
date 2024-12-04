var wsProtocol = "ws://";  // Renamed to avoid conflict
var loc = window.location;
var endpoint = wsProtocol + loc.host + loc.pathname;
console.log(endpoint);

var websocket = new WebSocket(endpoint);  // Use 'websocket' for the WebSocket instance

let maze = [];
let playerPos = [0, 0]; // Player's starting position

// DOM Elements
const mazeContainer = document.getElementById("maze-container");
const moveButtons = {
    up: document.getElementById("move-up"),
    down: document.getElementById("move-down"),
    left: document.getElementById("move-left"),
    right: document.getElementById("move-right"),
};

// Function to render the maze
function renderMaze() {
    mazeContainer.innerHTML = ""; // Clear previous maze
    maze.forEach((row, i) => {
        row.forEach((cell, j) => {
            const cellDiv = document.createElement("div");
            cellDiv.className = `cell ${cell === "W" ? "wall" : cell === "S" ? "start" : cell === "G" ? "goal" : "path"}`;
            if (i === playerPos[0] && j === playerPos[1]) {
                cellDiv.classList.add("player");
            }
            mazeContainer.appendChild(cellDiv);
        });
    });
}

// WebSocket message handler
websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.action === "initialize" || data.action === "move") {
        handleMazeMessage(data);
    } else {
        WebSocketonMessage(event);  // Ensure you define this function or remove it if not needed
    }
};

function handleMazeMessage(data) {
    if (data.action === "initialize") {
        maze = data.maze;
        playerPos = data.position;
        renderMaze();
    } else if (data.action === "move") {
        playerPos = data.message.new_position;
        renderMaze();
    }
}

// Movement button event listeners
Object.entries(moveButtons).forEach(([direction, button]) => {
    button.addEventListener("click", () => {
        websocket.send(JSON.stringify({
            action: "move",
            message: { direction },
        }));
    });
});
