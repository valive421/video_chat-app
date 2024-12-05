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






import random
import json
from channels.generic.websocket import AsyncWebsocketConsumer

# Maze dimensions
ROWS, COLS = 50, 50
maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]
directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

# Center of the maze
CENTER_X, CENTER_Y = COLS // 2, ROWS // 2  # 50x50 maze center (25, 25)

# Set maze boundaries for the players to start
def shuffle_array(array):
    random.shuffle(array)

def generate_maze(x=0, y=0):
    """Recursive backtracking maze generation."""
    maze[y][x] = 0
    shuffle_array(directions)
    for dx, dy in directions:
        nx, ny = x + dx * 2, y + dy * 2
        if 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] == 1:
            maze[y + dy][x + dx] = 0
            generate_maze(nx, ny)

generate_maze()

# Open spaces around Red's starting point (0, 0)
for i in range(3):
    for j in range(3):
        maze[i][j] = 0

# Open spaces around Blue's starting point (49, 49)
for i in range(47, 50):
    for j in range(47, 50):
        maze[i][j] = 0

# Create a 5x5 center area
for i in range(CENTER_Y - 2, CENTER_Y + 3):
    for j in range(CENTER_X - 2, CENTER_X + 3):
        maze[i][j] = 0

maze[0][0] = maze[49][49] = 0  # Ensure start and end points are open

players_connected = {"Red": None, "Blue": None}

def is_in_center(x, y):
    return (CENTER_X - 2 <= x <= CENTER_X + 2) and (CENTER_Y - 2 <= y <= CENTER_Y + 2)

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
                "player_positions": {"Red": {"x": 0, "y": 0}, "Blue": {"x": 49, "y": 49}},
                "player_color": self.player_color
        }))

        if self.player_color == "Blue":
            await self.channel_layer.group_send("game_room", {
                "type": "game_start",
                "message": "Game started!"
            })

    async def disconnect(self, close_code):
        global players_connected
        if players_connected[self.player_color] == self.channel_name:
            players_connected[self.player_color] = None
        await self.channel_layer.group_discard("game_room", self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if "move" in data:
                move = data["move"]
                if move["color"] != self.player_color:
                    await self.send_error("You cannot move the other player's piece.")
                    return
                if not self.is_valid_move(move['x'], move['y']):
                    await self.send_error("Invalid move.")
                    return
                await self.channel_layer.group_send("game_room", {
                    "type": "player_move",
                    "move": move
                })
        except (json.JSONDecodeError, KeyError) as e:
            await self.send_error(f"Error processing message: {str(e)}")

    async def player_move(self, event):
        await self.send(json.dumps({
            "type": "move",
            "move": event["move"]
        }))

    async def game_start(self, event):
        await self.send(json.dumps({
            "type": "game_start",
            "message": event["message"]
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

    def is_in_center(self, x, y):
        return (CENTER_X - 2 <= x <= CENTER_X + 2) and (CENTER_Y - 2 <= y <= CENTER_Y + 2)

    async def check_win(self, move):
        if self.is_in_center(move['x'], move['y']):
            await self.channel_layer.group_send("game_room", {
                "type": "game_win",
                "winner": move["color"]
            })
