from django.contrib.auth.hashers import make_password
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from user.models import User
import json
from msg.consumers import ChatConsumer
from asgiref.sync import sync_to_async


class ChatConsumerTestCase(TestCase):
    async def test_receive(self):
        # Create a test user
        await sync_to_async(User.objects.create)(name="testuser", password=make_password("testpass"))

        # Create a test WebSocket communicator
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/HELLO/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a test message
        message = {'message': 'Hello, world!'}
        await communicator.send_json_to(message)

        # Check that the message was received by the room group
        response = await communicator.receive_json_from()
        self.assertEqual(response, message)

        # Disconnect the communicator
        await communicator.disconnect()
