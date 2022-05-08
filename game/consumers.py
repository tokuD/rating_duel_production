import json, string, secrets, time, random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from django.utils import timezone

from . import models

class RoomConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = ''
        self.group_name = ''
        self.user_name = ''

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = 'chat_%s' % self.room_name
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None):
        text_data_json = json.loads(text_data)
        data_type = text_data_json.get('data_type')
        self.user_name = text_data_json.get('user_name')

        if 'join' == data_type:
            await self.channel_layer.group_add(self.group_name, self.channel_name)

        elif 'leave' == data_type:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        else:
            await self.save_message(text_data_json)
            message = text_data_json.get('message')
            data = {
                'type': 'chat_message',
                'message': message,
                'user_name': self.user_name,
                'datetime': timezone.now().strftime('%Y/%m/%d %H:%M:%S')
            }
            await self.channel_layer.group_send(self.group_name, data)

    async def chat_message(self, data):
        data = {
            'message': data.get('message'),
            'user_name': data.get('user_name'),
            'datetime': data.get('datetime')
        }
        await self.send(text_data=json.dumps(data))

    @database_sync_to_async
    def save_message(self, data):
        models.ChatMessage.objects.create(
            content=data.get('message'),
            game=models.Game.objects.get(room=self.room_name),
            posted_by=self.scope['user']
        )