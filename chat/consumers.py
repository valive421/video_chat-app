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

class GameConsumer(AsyncWebsocketConsumer):
    maze = []  # Initialize maze here, so it’s shared across connections
    player_positions = {'Red': {'x': 0, 'y': 0}, 'Blue': {'x': 19, 'y': 19}}  # Initial positions
    player_color = 'Red'  # Red goes first

    async def connect(self):
        # If maze is not yet generated, generate it
        websocket_url = self.scope['path']
        print(f"Incoming WebSocket URL: {websocket_url}")

        # Check if the URL is for the game
        if '/ws/game/' not in websocket_url:
            # Reject the connection if it's not a game-related request
            print("This WebSocket is not for the game, closing connection.")
            await self.close()
            return
        if not self.maze:
            self.maze = await self.generate_maze()
        await self.accept()

        # Send the generated maze to the client
        await self.send(text_data=json.dumps({
            "type": "maze",
            "maze": self.maze,
            "player_positions": self.player_positions,
            "player_color": self.player_color
        }))
        # Accept the WebSocket connection after sending maze data
        

    async def generate_maze(self):
        rows, cols = 20, 20
        maze = [[1 for _ in range(cols)] for _ in range(rows)]  # Initialize maze with walls

        def shuffle_array(array):
            random.shuffle(array)
            return array

        directions = [[0, -1], [1, 0], [0, 1], [-1, 0]]  # up, right, down, left

        def generate(x=0, y=0):
            maze[y][x] = 0  # Mark the current cell as open
            shuffled_directions = shuffle_array(directions)
            for dx, dy in shuffled_directions:
                nx, ny = x + dx * 2, y + dy * 2
                if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] == 1:
                    maze[y + dy][x + dx] = 0
                    generate(nx, ny)

        generate()
        maze[0][0] = maze[19][19] = 0  # Ensure start positions are open
        return maze

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"Received data: {data}")  # Debugging line
        move = data.get("move", None)

        if move:
            # Update player position
            await self.update_player_position(move)

            # Broadcast the new player position to all players
            await self.send_move_to_players(move)

    async def update_player_position(self, move):
        color = move.get('color')
        direction = move.get('direction')

        # Get current player position and make the move
        player_pos = GameConsumer.player_positions.get(color)
        if player_pos:
            print(f"Current position of {color}: {player_pos}")  # Debugging line
            if direction == 'up': player_pos['y'] -= 1
            elif direction == 'down': player_pos['y'] += 1
            elif direction == 'left': player_pos['x'] -= 1
            elif direction == 'right': player_pos['x'] += 1

            # Ensure the move is within bounds and on an open path
            if GameConsumer.maze[player_pos['y']][player_pos['x']] != 0:
                # Revert move if invalid
                if direction == 'up': player_pos['y'] += 1
                elif direction == 'down': player_pos['y'] -= 1
                elif direction == 'left': player_pos['x'] += 1
                elif direction == 'right': player_pos['x'] -= 1
                print(f"Invalid move for {color}, reverting position.")  # Debugging line

            print(f"Updated position of {color}: {player_pos}")  # Debugging line

    async def send_move_to_players(self, move):
        print(f"Sending move to players: {move}")  # Debugging line
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_move',
                'move': move,
            }
        )

    async def player_move(self, event):
        move = event['move']

        # Send move data to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'move',
            'move': move,
        }))
