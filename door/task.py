import paho.mqtt.client as mqtt
from door.models import DoorPassword, DoorHistory, DoorDevices, DoorState
from django.core.signals import request_finished
from channels.layers import get_channel_layer
import arrow
from datetime import datetime
from asgiref.sync import async_to_sync
import json
from pytz import timezone
import threading
import ssl
import random

ssl.match_hostname = lambda cert, hostname: True


# code from http://stackoverflow.com/a/14035296/4592067
def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


def set_timeout(func, sec):
    t = threading.Timer(sec, func)
    t.start()


room_group_name = 'door-control'
channel_layer = get_channel_layer()
local_timezone = timezone('Asia/Ho_Chi_Minh')
pem_path = '/home/pyrus/SmartDoor/smartdoor/hivemq-server-cert.pem'

rfid_uid = '123456'
rfid_length = 6

def start_job():
    def on_message(client, userdata, msg):
        arrow_now = arrow.now().format()
        now = datetime.now(local_timezone)
        if msg.topic == 'door-password':
            input_password = msg.payload.decode('ascii')[:4]
            print(input_password)
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
                        'door_status': msg.payload.decode('utf-8')
                    })
                }
            )
            history_data.save()
            pass
        if msg.topic == 'door-identify':
            door_id = msg.payload.decode('ascii')[:10]
            print(door_id)
            if not DoorDevices.objects.filter(id=door_id).exists():
                devices_data = DoorDevices.objects.create(
                    id=door_id,
                    status=True,
                    last_check=now
                )
                devices_data.save()
            else:
                device = DoorDevices.objects.filter(id=door_id)[0]
                device.status = True
                device.last_check = now
                device.save()
                on_interval_timeout()
            pass
        if msg.topic == 'door-status':
            async_to_sync(channel_layer.group_send)(
                room_group_name, {
                    'type': 'update_door_state',
                    'message': json.dumps({
                        'door_status': msg.payload.decode('utf-8'),
                    })
                }
            )
            pass
        if msg.topic == 'door-rfid':
            input_uid = msg.payload.decode('ascii')[:rfid_length]
            if input_uid == rfid_uid:
                auto_state = DoorState.objects.filter(key='auto')[0]
                if auto_state.value == 'on':
                    async_to_sync(channel_layer.group_send)(
                        room_group_name, {
                            'type': 'update_auto',
                            'message': json.dumps({
                                'update_door_auto': 'off',
                            })
                        }
                    )
                    mqtt_client.publish('door-distance', 'off')
                    auto_state.value = 'off'
                else:
                    async_to_sync(channel_layer.group_send)(
                        room_group_name, {
                            'type': 'update_auto',
                            'message': json.dumps({
                                'update_door_auto': 'on',
                            })
                        }
                    )
                    mqtt_client.publish('door-distance', 'on')
                    auto_state.value = 'on'
                auto_state.save()
            pass

    def on_interval():
        mqtt_client.publish('door-announce', '___')
        DoorDevices.objects.all().update(status=False)
        set_timeout(on_interval_timeout, 3)

    def on_interval_timeout():
        online_devices = DoorDevices.objects.filter(status=True).count()
        async_to_sync(channel_layer.group_send)(
            room_group_name, {
                'type': 'update_devices_status',
                'message': online_devices
            }
        )

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            mqtt_client.subscribe('door-password')
            mqtt_client.subscribe('door-autoclose')
            mqtt_client.subscribe('door-identify')
            mqtt_client.subscribe('door-status')
            mqtt_client.subscribe('door-rfid')
            set_interval(on_interval, 10)

    def disconnect(sender, **kwargs):
        print("FINISH")
        mqtt_client.disconnect()

    def on_disconnect():
        print('DISCONNECT')

    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
#   mqtt_client.tls_set('hivemq-server-cert.pem', tls_version= ssl.PROTOCOL_TLSv1_2)
    mqtt_client.connect('127.0.0.1', port=1883)
    mqtt_client.loop_start()
    request_finished.connect(disconnect)
#   init database data
    if not DoorState.objects.filter(key='auto').exists():
        state = DoorState.objects.create(key='auto', value='off')
        state.save()
