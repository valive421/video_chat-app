import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "room"
        websocket_url = self.scope['path']
        print(f"Incoming WebSocket URL: {websocket_url}")

        # Check if the URL is for the video chat
        if '/ws/chat/' not in websocket_url:
            # Reject the connection if it's not a video chat request
            print("This WebSocket is not for video chat, closing connection.")
            await self.close()
            return
        # Add the WebSocket to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Remove the WebSocket from the group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("Disconnected")

    async def receive(self, text_data):
        # Parse the received message
        try:
            receive_dict = json.loads(text_data)

            # Ensure the message is not related to the maze
            if receive_dict.get('type') == 'maze':
                return

            # Check if the message key exists
            message = receive_dict.get('message')
            if message is None:
                return  # Or handle the error if needed

            action = receive_dict.get('action')

            if action in ['new-offer', 'new-answer']:
                receiver_channel_name = message.get('receiver_channel_name')
                # Send the message to the specific receiver
                await self.channel_layer.send(
                    receiver_channel_name,
                    {
                        "type": 'send.sdp',
                        "receive_dict": receive_dict
                    }
                )

            # Include the sender's channel name in the message if message exists
            message['receiver_channel_name'] = self.channel_name

            # Send the message to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": 'send.sdp',
                    "receive_dict": receive_dict
                }
            )
        except json.JSONDecodeError:
            print("Error decoding JSON message.")
        except KeyError as e:
            print(f"Missing key in message: {e}")

    async def send_sdp(self, event):
        receive_dict = event['receive_dict']
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps(receive_dict))



import json
from channels.generic.websocket import AsyncWebsocketConsumer
import random

ROWS, COLS = 80, 80
CENTER_X, CENTER_Y = COLS // 2, ROWS // 2
maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]  # Start with all walls
players_connected = {"Red": None, "Blue": None}
player_positions = {"Red": {"x": 0, "y": 0}, "Blue": {"x": COLS - 1, "y": ROWS - 1}}
current_turn = "Red"
# Directions for carving paths
directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]  # Move by 2 cells for walls


def is_within_bounds(x, y):
    """Check if a cell is within the maze bounds."""
    return 0 <= x < COLS and 0 <= y < ROWS


def generate_maze_recursive(x, y):
    """Generate the maze using recursive backtracking."""
    maze[y][x] = 0  # Mark the current cell as a path
    shuffle_array(directions)

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if is_within_bounds(nx, ny) and maze[ny][nx] == 1:
            # Check the cell two steps ahead
            wx, wy = x + dx // 2, y + dy // 2
            if is_within_bounds(wx, wy):
                maze[wy][wx] = 0  # Remove the wall
                maze[ny][nx] = 0  # Carve the path
                generate_maze_recursive(nx, ny)  # Recurse into the new cell


def ensure_paths_to_center():
    """Ensure paths exist to the maze's center."""
    for i in range(CENTER_Y - 1, CENTER_Y + 2):
        for j in range(CENTER_X - 1, CENTER_X + 2):
            maze[i][j] = 0  # Clear a small area around the center


def shuffle_array(array):
    """Shuffle the directions array."""
    random.shuffle(array)


# Generate the maze
start_x, start_y = random.choice(range(0, COLS, 2)), random.choice(range(0, ROWS, 2))
generate_maze_recursive(start_x, start_y)
ensure_paths_to_center()

# Open paths at player positions
for i in range(3):
    for j in range(3):
        maze[i][j] = 0  # Red player start
        maze[ROWS - 1 - i][COLS - 1 - j] = 0  # Blue player start

# Optional: Add some random openings for variety
for _ in range(100):  # Adjust this number for more/less openings
    rx, ry = random.randint(0, COLS - 1), random.randint(0, ROWS - 1)
    maze[ry][rx] = 0

print('the maze is printed')


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.player_color = await self.assign_player_color()

        if not self.player_color:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add("game_room", self.channel_name)
        await self.send(json.dumps({
            "type": "maze",
            "maze": ''.join(''.join(str(cell) for cell in row) for row in maze),
            "player_positions": player_positions,
            "player_color": self.player_color,
            "current_turn": current_turn
        }))

        if self.player_color == "Blue":
            await self.channel_layer.group_send("game_room", {
                "type": "game_start",
                "message": "Game started!"
            })

    async def disconnect(self, close_code):
        global players_connected
        players_connected[self.player_color] = None
        await self.channel_layer.group_discard("game_room", self.channel_name)

    async def receive(self, text_data):
      try:
        data = json.loads(text_data)
        if "move" in data:
            await self.handle_move(data["move"])
      except (json.JSONDecodeError, KeyError) as e:
        await self.send_error(f"Error processing message: {str(e)}")

    async def handle_move(self, move):
      global player_positions
    # Validate the move (check boundaries and walls)
      if not self.is_valid_move(move['x'], move['y']):
        await self.send_error("Invalid move.")
        return

    # Update player position
      player_positions[move["color"]] = {"x": move["x"], "y": move["y"]}

    # Broadcast the move to all connected clients
      await self.channel_layer.group_send("game_room", {
        "type": "move_broadcast",
        "move": move
    })
      

    async def move_broadcast(self, event):
        await self.send(json.dumps({
            "type": "move",
            "move": event["move"]
        }))

    async def turn_update(self, event):
        await self.send(json.dumps({
            "type": "turn_update",
            "turn": event["new_turn"]
        }))

    async def game_start(self, event):
        await self.send(json.dumps({
            "type": "game_start",
            "message": event["message"]
        }))

    async def game_win(self, event):
        await self.send(json.dumps({
            "type": "game_win",
            "winner": event["winner"]
        }))

    async def send_error(self, message):
        await self.send(json.dumps({
            "type": "error",
            "message": message
        }))

    async def assign_player_color(self):
        global players_connected
        if players_connected["Red"] is None:
            players_connected["Red"] = self.channel_name
            return "Red"
        elif players_connected["Blue"] is None:
            players_connected["Blue"] = self.channel_name
            return "Blue"
        return None

    def is_valid_move(self, x, y):
        return 0 <= x < COLS and 0 <= y < ROWS and maze[y][x] == 0