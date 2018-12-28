import paho.mqtt.client as mqtt
from door.models import DoorPassword, DoorHistory, DoorDevices, DoorState, DeviceStates
from django.core.signals import request_finished
from channels.layers import get_channel_layer
import arrow
from datetime import datetime
from asgiref.sync import async_to_sync
import json
from pytz import timezone
import threading
import ssl
from door.utils import bind_mq_to_ws_message, get_online_devices_ws_message, on_control_predict_data as control_predict_data
from door.learning import predict_data, make_predict

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

# rfid_uid = '78f2dab9'
rfid_uid = ['856c5628','78f2dab9']

ledIds = ['LLIV', 'LKIT', 'LBED', 'LBAT']
tempIds = ['TOFF', 'THOM']


def start_job():
    def on_message(client, userdata, msg):
        arrow_now = arrow.now().format()
        now = datetime.now(local_timezone)
        print(msg.payload)
        if msg.topic == "DOOR_UP":
            mq_message = msg.payload.decode('utf-8')
            if mq_message == 'open':
                device_state = DeviceStates.objects.create(
                    id="DOOR",
                    state=True,
                    time=datetime.now()
                )
                device_state.save()
            if mq_message == 'close':
                device_state = DeviceStates.objects.create(
                    id= 'DOOR',
                    state=False,
                    time=datetime.now()
                )
                device_state.save()
            pass

        if msg.topic == "UUID":
            input_uid = msg.payload.hex()
            print(input_uid)
            next_state = 0
            if input_uid in rfid_uid:
                query = DeviceStates.objects.filter(id='RFID').order_by('-time')
                if query.exists():
                    if query[0].state :
                        print('change true')
                        device_state = DeviceStates.objects.create(
                            id= 'RFID',
                            state=False,
                            time=datetime.now()
                        )
                        device_state.save()
                        mqtt_client.publish('RFID', 'off')
                    else:
                        print('change false')
                        device_state = DeviceStates.objects.create(
                            id= 'RFID',
                            state=True,
                            time=datetime.now()
                        )
                        device_state.save()
                        mqtt_client.publish('RFID', 'on')
                        next_state = 1
                else:
                    print('new')
                    device_state = DeviceStates.objects.create(
                        id='RFID',
                        state=True,
                        time=datetime.now()
                    )
                    device_state.save()
                    mqtt_client.publish('RFID', 'on')
                    next_state = 1

                async_to_sync(channel_layer.group_send)(
                    room_group_name, {
                        'type': 'led_control',
                        'message': json.dumps({
                            'id' : 'RFID',
                            'state'  : next_state,
                        })
                    }
                )
            pass
        if msg.topic == "LED_CONTROL":
            mq_message = msg.payload.decode('utf-8')
            ws_message = bind_mq_to_ws_message(msg.topic, mq_message)
            async_to_sync(channel_layer.group_send)(
                room_group_name, {
                    'type': 'led_control',
                    'message': json.dumps(ws_message)
                }
            )
            device_state = DeviceStates.objects.create(
                id=ws_message['id'],
                state=mq_message.isupper(),
                time=datetime.now()
            )
            device_state.save()
            pass
        if msg.topic == "RES_STAT":
            device_id = msg.payload.decode('ascii')[:len(msg.payload)]
            if not DoorDevices.objects.filter(id=device_id).exists():
                devices_data = DoorDevices.objects.create(
                    id=device_id,
                    status=True,
                    last_check=now
                )
                devices_data.save()
                on_interval_timeout()
            else:
                device = DoorDevices.objects.filter(id=device_id)[0]
                device.status = True
                device.last_check = now
                device.save()
            pass
        if msg.topic in tempIds:
            async_to_sync(channel_layer.group_send)(
                room_group_name, {
                    'type': 'temp_control',
                    'message': json.dumps({
                        'id': msg.topic,
                        'state': int(float(msg.payload.decode('utf-8'))),
                        'type': 'TEMP CONTROL',
                        'update': True
                    })
                }
            )
            print('receive', msg.payload.decode('ascii'))
            device_state = DeviceStates.objects.create(
                id=msg.topic,
                state= int(float(msg.payload.decode('utf-8'))),
                time=datetime.now()
            )
            device_state.save()
            pass

    def on_interval():
        mqtt_client.publish('REQ_STAT', '')
        DoorDevices.objects.all().update(status=False)
        set_timeout(on_interval_timeout, 5)

    def on_interval_timeout():
        async_to_sync(channel_layer.group_send)(
            room_group_name, {
                'type': 'update_devices_status',
                'message': json.dumps(get_online_devices_ws_message())
            }
        )

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            mqtt_client.subscribe('door-password')
            mqtt_client.subscribe('door-autoclose')
            mqtt_client.subscribe('door-identify')
            mqtt_client.subscribe('door-status')
            mqtt_client.subscribe('door-rfid')

            mqtt_client.subscribe('LED_CONTROL')
            mqtt_client.subscribe('RES_STAT')
            mqtt_client.subscribe('DOOR_UP')
            mqtt_client.subscribe('DOOR_DOWN')
            mqtt_client.subscribe('UUID')
            for ledId in ledIds:
                mqtt_client.subscribe(ledId)
            for tempId in tempIds:
                mqtt_client.subscribe(tempId)
            set_interval(on_interval, 20)

    def disconnect(sender, **kwargs):
        print("FINISH")
        mqtt_client.disconnect()

    def on_disconnect():
        print('DISCONNECT')

    def on_predict():
        def on_control_predict_data(dif):
            print('dif',dif)
            control_predict_data(dif,mqtt_client)
            pass
        make_predict(on_control_predict_data)
        pass

    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    #   mqtt_client.tls_set('hivemq-server-cert.pem', tls_version= ssl.PROTOCOL_TLSv1_2)
    mqtt_client.username_pw_set(username="admin", password="123QWE!@#")
    mqtt_client.connect('127.0.0.1', port=1883)
    mqtt_client.loop_start()
    request_finished.connect(disconnect)

    set_interval(on_predict,30)
    #   init database data
    if not DoorState.objects.filter(key='auto').exists():
        state = DoorState.objects.create(key='auto', value='off')
        state.save()
    DoorDevices.objects.all().delete()
