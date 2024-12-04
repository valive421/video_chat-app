import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "room"
        # Add the WebSocket to the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
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
        receive_dict = json.loads(text_data)
        message = receive_dict['message']
        action = receive_dict['action']

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

        # Include the sender's channel name in the message
        receive_dict['message']['receiver_channel_name'] = self.channel_name
        # Send the message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": 'send.sdp',
                "receive_dict": receive_dict
            }
        )

    async def send_sdp(self, event):
        receive_dict = event['receive_dict']
        # Send the message to the WebSocket
        await self.send(text_data=json.dumps(receive_dict))


class GameConsumer(AsyncWebsocketConsumer):
    connected_players = []
    maze = None
    player_positions = {}  # Tracks player positions

    async def connect(self):
        # Assign player color (Red or Blue)
        if len(self.connected_players) == 0:
            self.player_color = "Red"
        else:
            self.player_color = "Blue"

        self.room_name = "game_room"
        self.room_group_name = "game_room"

        # Generate the maze if it's not already generated
        if not GameConsumer.maze:
            GameConsumer.maze = await self.generate_maze()

        # Add player to connected players list
        GameConsumer.connected_players.append(self.player_color)
        GameConsumer.player_positions[self.player_color] = {
            'x': 0 if self.player_color == "Red" else 19,  # Starting positions
            'y': 0 if self.player_color == "Red" else 19
        }

        # Accept the WebSocket connection
        await self.accept()

        # Send the maze and player positions to the connected player
        await self.send(text_data=json.dumps({
            "type": "maze",
            "maze": GameConsumer.maze,
            "player_positions": GameConsumer.player_positions
        }))

        # Broadcast the player list to all players
        await self.broadcast_players()

    async def generate_maze(self):
        rows, cols = 20, 20
        maze = [[1 for _ in range(cols)] for _ in range(rows)]

        # Recursive Backtracker Algorithm (same as JavaScript)
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

    async def broadcast_players(self):
        await self.send(text_data=json.dumps({
            'type': 'players',
            'players': GameConsumer.connected_players
        }))