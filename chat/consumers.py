import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer

# Global variables for maze and player positions
maze = None
player_positions = {}

# Maze generation function
def generate_maze(rows=5, cols=5):
    """Generate a random maze with walls ('W'), paths (' '), and a start ('S') and goal ('G')."""
    maze = [[" " for _ in range(cols)] for _ in range(rows)]
    # Add walls randomly
    for i in range(rows):
        for j in range(cols):
            if random.random() < 0.3:
                maze[i][j] = "W"

    # Define start and goal
    maze[0][0] = "S"
    maze[rows - 1][cols - 1] = "G"
    return maze

# Generate maze globally before WebSocket connection is made
if maze is None:
    maze = generate_maze()
    print("Maze generated:", maze)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "room"
        self.channel_name_key = None

        # Add WebSocket to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Set initial player position in the global dictionary
        player_positions[self.channel_name] = (0, 0)

        # Send the generated maze to the client
        await self.send(json.dumps({"action": "initialize", "maze": maze, "position": (0, 0)}))

    async def disconnect(self, close_code):
        # Remove WebSocket from group and cleanup
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Remove the player from global player_positions
        if self.channel_name in player_positions:
            del player_positions[self.channel_name]

        print("Disconnected")

    async def receive(self, text_data):
        # Parse the received message
        receive_dict = json.loads(text_data)
        message = receive_dict['message']
        action = receive_dict['action']

        if action == 'move':
            direction = message.get('direction')
            current_pos = player_positions.get(self.channel_name, (0, 0))
            new_pos = self.calculate_new_position(current_pos, direction)
            # Validate the new position
            if self.is_valid_move(new_pos):
                player_positions[self.channel_name] = new_pos
                message['new_position'] = new_pos
            else:
                message['new_position'] = current_pos

        # Send the message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": 'send.sdp',
                "receive_dict": receive_dict
            }
        )

    def calculate_new_position(self, current_pos, direction):
        """Calculate new position based on the direction."""
        row, col = current_pos
        if direction == "up":
            return (row - 1, col)
        elif direction == "down":
            return (row + 1, col)
        elif direction == "left":
            return (row, col - 1)
        elif direction == "right":
            return (row, col + 1)
        return current_pos

    def is_valid_move(self, position):
        """Check if the move is valid."""
        row, col = position
        if 0 <= row < len(maze) and 0 <= col < len(maze[0]):
            return maze[row][col] != "W"
        return False

    async def send_sdp(self, event):
        receive_dict = event['receive_dict']
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps(receive_dict))
