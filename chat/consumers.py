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
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Maze

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle player connection and assign colors."""
        await self.accept()
        print("Connection made.")
        
        # Assign player color atomically
        self.player_color = await self.assign_player_color()
        await self.channel_layer.group_add("game_room", self.channel_name)

        maze_instance = await self.get_or_create_maze()

        # Send maze and player color to the connecting player
        await self.send(text_data=json.dumps({
            "type": "maze",
            "maze": json.loads(maze_instance.maze_data),
            "player_positions": {"Red": {"x": 0, "y": 0}, "Blue": {"x": 19, "y": 19}},
            "player_color": self.player_color
        }))

    async def disconnect(self, close_code):
        """Handle player disconnection."""
        await self.channel_layer.group_discard("game_room", self.channel_name)
        # Check if the room is empty, then delete the maze
        if not self.channel_layer.groups.get("game_room"):
            await self.delete_maze()

    async def receive(self, text_data):
        """Handle moves only if the player controls the correct piece."""
        try:
            data = json.loads(text_data)
            print("Message received:", data)

            if "move" in data:
                move = data["move"]
                player_color = move["color"]

                # Validate that the player can move their own piece
                if player_color != self.player_color:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "You cannot move the other player's piece."
                    }))
                    return

                # Validate move position
                if not self.is_valid_move(move['x'], move['y']):
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Invalid move."
                    }))
                    return

                # Broadcast the move to all players
                await self.channel_layer.group_send("game_room", {
                    "type": "player_move",
                    "move": move
                })
        except (json.JSONDecodeError, KeyError) as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            }))

    async def player_move(self, event):
        """Send move update to all players."""
        move = event["move"]
        await self.send(text_data=json.dumps({
            "type": "move",
            "move": move
        }))

    @database_sync_to_async
    def assign_player_color(self):
        """Assign player color atomically."""
        if not Maze.objects.exists():
            return "Red"
        return "Blue"

    @database_sync_to_async
    def get_or_create_maze(self):
        """Fetch or create a maze."""
        maze_instance, created = Maze.objects.get_or_create(id=1, defaults={"maze_data": json.dumps(self.generate_maze())})
        return maze_instance

    @database_sync_to_async
    def delete_maze(self):
        """Delete the maze from the database."""
        Maze.objects.all().delete()

    def generate_maze(self):
        """Generate a new maze using recursive backtracking."""
        rows, cols = 20, 20
        maze = [[1 for _ in range(cols)] for _ in range(rows)]

        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

        def shuffle_array(array):
            random.shuffle(array)

        def generate(x=0, y=0):
            maze[y][x] = 0
            shuffle_array(directions)
            for dx, dy in directions:
                nx, ny = x + dx * 2, y + dy * 2
                if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] == 1:
                    maze[y + dy][x + dx] = 0
                    generate(nx, ny)

        generate()
        maze[0][0] = maze[19][19] = 0
        return maze

    def is_valid_move(self, x, y):
        """Check if the move is within bounds and on a valid path."""
        return 0 <= x < 20 and 0 <= y < 20 and self.generate_maze()[y][x] == 0
