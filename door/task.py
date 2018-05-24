import paho.mqtt.client as mqtt
from door.models import DoorPassword, DoorHistory
from django.core.signals import request_finished
from channels.layers import get_channel_layer
import arrow
from datetime import datetime
from asgiref.sync import async_to_sync
import json
from pytz import timezone

room_group_name = 'door-control'
channel_layer = get_channel_layer()
local_timezone = timezone('Asia/Ho_Chi_Minh')


def start_job():
    def on_message(client, userdata, msg):
        input_password = msg.payload.decode('ascii')[:4]
        print(input_password)
        arrow_now = arrow.now().format()
        now = datetime.now(local_timezone)
        if msg.topic == 'door-password':
            querry = DoorPassword.objects.filter(password=input_password)
            if querry.count() > 0:
                mqtt_client.publish('door-control', 'open')
                history_data = DoorHistory.objects.create(
                    action='password open',
                    time=now
                )
                history_data.save()
                async_to_sync(channel_layer.group_send)(
                    room_group_name, {
                        'type': 'update_history_list',
                        'message': json.dumps({
                            'action': 'password open',
                            'time': arrow_now
                        })
                    }
                )
            else:
                mqtt_client.publish('door-control', 'close')
                history_data = DoorHistory.objects.create(
                    action='wrong password',
                    time=now
                )
                history_data.save()
                async_to_sync(channel_layer.group_send)(
                    room_group_name, {
                        'type': 'update_history_list',
                        'message': json.dumps({
                            'action': 'wrong password',
                            'time': arrow_now
                        })
                    }
                )
            pass
        if msg.topic == 'door-autoclose':
            history_data = DoorHistory.objects.create(
                action='auto close',
                time=now
            )
            async_to_sync(channel_layer.group_send)(
                room_group_name, {
                    'type': 'update_history_list',
                    'message': json.dumps({
                        'action': 'auto close',
                        'time': arrow_now
                    })
                }
            )
            history_data.save()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            mqtt_client.subscribe('door-password')
            mqtt_client.subscribe('door-autoclose')

    def disconnect(sender, **kwargs):
        print("FINISH")
        mqtt_client.disconnect()

    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect
    mqtt_client.connect('127.0.0.1', 1883, keepalive=10, bind_address="")
    mqtt_client.loop_start()
    request_finished.connect(disconnect)

