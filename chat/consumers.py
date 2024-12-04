import json
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
