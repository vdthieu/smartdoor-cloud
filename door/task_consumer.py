# chat/consumers.py
from asgiref.sync import async_to_sync
from channels.generic.websocket import SyncConsumer
import json
from datetime import datetime
from pytz import timezone
import arrow
import ssl

local_timezone = timezone('Asia/Ho_Chi_Minh')
ssl.match_hostname = lambda cert, hostname: True
pem_path = 'hivemq-server-cert.pem'

print('hihi')


def led_control(self, event):
    print(event['message'])


class TaskConsumer(SyncConsumer):

    def connect(self):
       pass

    def disconnect(self, close_code):
        pass

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)

    def led_control(self, event):
        print(event['message'])

    # MQTT METHODS
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            pass
        else:
            print("Connection failed")

    def on_message(self, client, userdata, msg):
        self.mqtt.loop_start()
