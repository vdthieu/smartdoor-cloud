# chat/consumers.py
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import paho.mqtt.client as mqtt
from door.models import DoorPassword, DoorHistory
import json
import datetime

class DoorConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = 'door'
        self.room_group_name = 'door-control'

        mqtt_client = mqtt.Client()
        mqtt_client.on_publish = self.on_publish
        mqtt_client.on_message = self.on_message
        mqtt_client.on_connect = self.on_connect
        mqtt_client.connect('127.0.0.1', 1883, keepalive=10)
        mqtt_client.loop_start()
        self.mqtt = mqtt_client

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        self.mqtt.disconnect()

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if 'door_control' in text_data_json:
            data = text_data_json['door_control']
            if data == 'close':
                history_data = DoorHistory.objects.create(
                    action='manual close',
                    time=datetime.datetime.now()
                )
            else:
                history_data = DoorHistory.objects.create(
                    action='manual open',
                    time=datetime.datetime.now()
                )
            history_data.save()
            self.mqtt.publish("door-control", data)

        if 'door_save_pwd' in text_data_json:
            data = text_data_json['door_save_pwd']
            if not data['type']:
                pwd_data = DoorPassword.objects.create(
                    password=data['pwd'],
                    is_hard=not data['type'],
                    description=data['note'],
                    create_time=data['create'],
                )
                pwd_data.save()
            else:
                pwd_data = DoorPassword.objects.create(
                    password=data['pwd'],
                    is_hard=not data['type'],
                    create_time=data['create'],
                    description=data['note'],
                    apply_time=data['apply'],
                    due_time=data['due'],
                )
                pwd_data.save()
            self.send(json.dumps({
                'update_pwd_list': data
            }))

        # # Send message to room group
        # async_to_sync(self.channel_layer.group_send)(
        #     self.room_group_name,
        #     {
        #         'type': 'post_socket',
        #         'message': message
        #     }
        # )

    # Receive message from room group
    def post_socket(self, event):
        message = event['door_status']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'door_status': message
        }))

    # MQTT METHODS
    def on_publish(self, client, data, mid):
        print("Sent")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.mqtt.subscribe('door-status')
        else:
            print("Connection failed")

    def on_message(self, client, userdata, msg):
        if msg.topic == 'door-status':
            self.send(text_data=json.dumps({
                'door_status': msg.payload.decode('utf-8')
            }))
        self.mqtt.loop_start()
