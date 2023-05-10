from django.contrib.auth.hashers import make_password
from django.test import TestCase
from user.models import User
from msg.consumers import ChatConsumer
from asgiref.sync import sync_to_async
from channels.routing import URLRouter, ProtocolTypeRouter
import pytest
from django.urls import path
import json
import pytest
from channels.testing import ChannelsLiveServerTestCase, WebsocketCommunicator

# class TestChatConsumer(TestCase):
#     def setUp(self):
#         self.user = User.objects.create(
#             name='testuser', 
#             password=make_password('testpassword'),
#             user_email='testuser@example.com'
#         )

#     async def test_consumer_connection(self):
#         communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1/")
#         connected, _ = await communicator.connect()
#         assert connected

#         await communicator.send_json_to({"token": self.token, "message": "Hello!"})
#         response = await communicator.receive_json_from()
#         messages = response["messages"]

#         # Check the message was saved and returned
#         assert len(messages) == 1
#         assert messages[0]["msg_body"] == "Hello!"
#         assert messages[0]["sender_id"] == self.user.pk

#         # Test heartbeat
#         await communicator.send_json_to({"token": self.token, "heartbeat": True})
#         response = await communicator.receive_json_from()
#         messages = response["messages"]

#         # Check the message count remains the same
#         assert len(messages) == 1

#         await communicator.disconnect()

#     async def test_consumer_invalid_token(self):
#         communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1/")
#         connected, _ = await communicator.connect()
#         assert connected

#         await communicator.send_json_to({"token": "invalid_token", "message": "Hello!"})

#         # Expect the connection to be closed due to invalid token
#         with self.assertRaises(Exception):
#             await communicator.receive_json_from()

#         await communicator.disconnect()

#     async def test_consumer_no_token(self):
#         communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1/")
#         connected, _ = await communicator.connect()
#         assert connected

#         await communicator.send_json_to({"message": "Hello!"})

#         # Expect the connection to be closed due to missing token
#         with self.assertRaises(Exception):
#             await communicator.receive_json_from()

#         await communicator.disconnect()

# # class ChatConsumerTestCase(TestCase):
# #     application = ProtocolTypeRouter({
# #     "websocket": URLRouter([
# #         path("ws/chat/<int:conversation_id>/", ChatConsumer.as_asgi()),
# #     ])
# # })
    
# #     application = URLRouter([path('ws/chat/<int:conversation_id>/', ChatConsumer.as_asgi())])
    
# #     async def get_communicator(self):
# #         communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/1/")
# #         connected, _ = await communicator.connect()
# #         self.assertTrue(connected)
# #         return communicator

# #     async def close_communicator(self, communicator):
# #         await communicator.disconnect(2)
        
# #     async def test_connect(self):
# #         communicator = await self.get_communicator()
# #         self.assertIsNotNone(communicator.scope['path']['kwargs']['conversation_id'])
# #         await self.close_communicator(communicator)

# #     # async def test_receive_with_valid_token(self):
# #     #     communicator = await self.get_communicator()
# #     #     message = {"message": "Hello, World!", "token": "valid_token"}
# #     #     await communicator.send_json_to(message)
# #     #     response = await communicator.receive_json_from()
# #     #     self.assertEqual(response, {"type": "chat_message"})
# #     #     await self.close_communicator(communicator)

# #     # async def test_receive_with_invalid_token(self):
# #     #     communicator = await self.get_communicator()
# #     #     message = {"message": "Hello, World!", "token": "invalid_token"}
# #     #     await communicator.send_json_to(message)
# #     #     response = await communicator.receive_json_from()
# #     #     self.assertEqual(response, {"type": "websocket.close"})
# #     #     await self.close_communicator(communicator)

# #     # async def test_chat_message(self):
# #     #     communicator = await self.get_communicator()
# #     #     message = {"message": "Hello, World!", "token": "valid_token"}
# #     #     await communicator.send_json_to(message)
# #     #     response = await communicator.receive_json_from()
# #     #     self.assertEqual(response, {"type": "chat_message"})
# #     #     self.assertEqual(response["messages"][0]["msg_body"], "Hello, World!")
# #     #     await self.close_communicator(communicator)


# # class ChatConsumerTestCase(TestCase):
# #     @pytest.fixture
# #     async def connected_communicator(scope="module"):
# #         communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/1/")
# #         connected, _ = await communicator.connect()
# #         assert connected



# #     @pytest.mark.asyncio
# #     async def test_disconnect(connected_communicator):
# #         await connected_communicator.disconnect()
# #         assert connected_communicator.channel_name not in connected_communicator.channel_layer.groups['1']


# #     @pytest.mark.asyncio
# #     async def test_receive_with_valid_token(connected_communicator, mocker):
# #         mocker.patch('msg.consumers.async_get_user_by_token', return_value=MagicMock(user_id=1))
# #         message = {"message": "Hello, World!", "token": "valid_token"}
# #         await connected_communicator.send_json_to(message)
# #         response = await connected_communicator.receive_json_from()
# #         assert response == {"type": "chat_message"}


# #     @pytest.mark.asyncio
# #     async def test_receive_with_invalid_token(connected_communicator, mocker):
# #         mocker.patch('msg.consumers.async_get_user_by_token', return_value=None)
# #         message = {"message": "Hello, World!", "token": "invalid_token"}
# #         await connected_communicator.send_json_to(message)
# #         response = await connected_communicator.receive_json_from()
# #         assert response == {"type": "websocket.close"}


# #     @pytest.mark.asyncio
# #     async def test_chat_message(connected_communicator, mocker):
# #         async def mock_acreate(**kwargs):
# #             return MagicMock(msg_id=1, msg_body=kwargs['msg_body'], sender_id=1)

# #         mocker.patch('msg.consumers.async_get_user_by_token', return_value=MagicMock(user_id=1))
# #         mocker.patch('msg.consumers.Message.objects.acreate', mock_acreate)

# #         message = {"message": "Hello, World!", "token": "valid_token"}
# #         await connected_communicator.send_json_to(message)
# #         response = await connected_communicator.receive_json_from()
# #         assert response["messages"][0]["msg_body"] == "Hello, World!"



# # # class ChatConsumerTestCase(TestCase):
# # #     async def test_receive(self):
# # #         # Create a test user
# # #         await sync_to_async(User.objects.create)(name="testuser", password=make_password("testpass"))

# # #         # Create a test WebSocket communicator
# # #         communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/HELLO/")
# # #         connected, _ = await communicator.connect()
# # #         self.assertTrue(connected)

# # #         # Send a test message
# # #         message = {'message': 'Hello, world!'}
# # #         await communicator.send_json_to(message)

# # #         # Check that the message was received by the room group
# # #         response = await communicator.receive_json_from()
# # #         self.assertEqual(response, message)

# # #         # Disconnect the communicator
# # #         await communicator.disconnect()
