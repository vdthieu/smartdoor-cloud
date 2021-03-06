# chat/consumers.py
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import paho.mqtt.client as mqtt
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import datetime
from pytz import timezone
import arrow
import ssl
from door.utils import \
    bind_ws_to_mq_message, \
    get_online_devices_ws_message, get_devices_logs_from_times, \
    get_devices_state_ws_message, binary_devices, \
    on_control_predict_data, get_training_summary_ws_message, \
    get_training_status, toggle_training_status
from door.learning import make_predict, make_train
from door.models import DoorPassword, DoorHistory, DoorState

import threading

local_timezone = timezone('Asia/Ho_Chi_Minh')
ssl.match_hostname = lambda cert, hostname: True
pem_path = 'hivemq-server-cert.pem'


class DoorConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = 'door-control'
        # init mqttt
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = self.on_message
        mqtt_client.on_connect = self.on_connect
        # mqtt_client.tls_set(pem_path, tls_version=ssl.PROTOCOL_TLSv1_2)
        mqtt_client.username_pw_set(username="admin", password="123QWE!@#")
        mqtt_client.connect('127.0.0.1', port=1883)
        mqtt_client.loop_start()
        self.mqtt = mqtt_client

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        # get board status
        self.send(json.dumps(get_online_devices_ws_message()))
        self.send(json.dumps(get_devices_state_ws_message()))
        self.send(json.dumps(get_training_summary_ws_message(),cls=DjangoJSONEncoder))

        prediction_query = DoorState.objects.filter(key='prediction')
        self.send(json.dumps({
            "type" : "PREDICTION STATE",
            "value" : False if (prediction_query.exists() and prediction_query[0].value == 'off') else True
        }))
        self.send(json.dumps({
            "type" : "TRAINING STATUS",
            "state" : "training" if get_training_status() else "free"
        }))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        self.mqtt.disconnect()

    def on_control_predict_data(self, data):
        on_control_predict_data(data, self.mqtt)

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if text_data_json['type'] == 'LED CONTROL':
            if not text_data_json['update']:
                mqtt_message = bind_ws_to_mq_message(text_data_json)
                self.mqtt.publish(mqtt_message["topic"], mqtt_message['message'])
                threading.Thread(target=make_predict, args=[self.on_control_predict_data,text_data_json['id']]).start()
            pass

        if text_data_json['type'] == 'TEMP CONTROL':
            if not text_data_json['update']:
                self.mqtt.publish(text_data_json['id'], text_data_json['state'])
                threading.Thread(target=make_predict, args=[self.on_control_predict_data,text_data_json['id']]).start()
            pass

        if text_data_json['type'] == 'TRAINING CONTROL':
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    'type': 'update_training_status',
                    'message': toggle_training_status(True)
                    })

            if text_data_json['state']:
                def progress_callback(result):
                    self.send(
                        json.dumps({
                            "type": "TRAINING SUMMARY",
                            "data": result
                        }, cls=DjangoJSONEncoder))
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name, {
                            'type': 'update_training_status',
                            'message': toggle_training_status(False)
                        })
                    # self.send(json.dumps({
                    #     'train_time' : result['']
                    # }))
                    # self.send(json.dumps(result))
                    pass

                make_train(progress_callback)
            pass

        if text_data_json['type'] == 'GET TABLE':
            time = datetime.strptime(text_data_json['time'], "%a, %d %b %Y %H:%M:%S %Z")
            data = get_devices_logs_from_times(time)
            self.send(json.dumps({
                "type": "DATA TABLE",
                "data": data
            },
                cls=DjangoJSONEncoder
            ))
            pass

        if text_data_json['type'] == 'TOGGLE PREDICT':
            query = DoorState.objects.filter(key='prediction')
            if query.exists():
                instance = query[0]
                instance.value = 'on' if text_data_json['state'] else 'off'
                instance.save()
            else:
                instance = DoorState.objects.create(
                    key='prediction',
                    value='on' if text_data_json['state'] else 'off'
                )
                instance.save()
            pass

        if 'door_control' in text_data_json:
            data = text_data_json['door_control']
            now = datetime.now(local_timezone)
            arrow_now = arrow.now().format()
            if data == 'close':
                history_data = DoorHistory.objects.create(
                    action='manual close',
                    time=now
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {
                        'type': 'update_history_list',
                        'message': json.dumps({
                            'action': 'manual close',
                            'time': arrow_now
                        })
                    }
                )

            else:
                history_data = DoorHistory.objects.create(
                    action='manual open',
                    time=now
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {
                        'type': 'update_history_list',
                        'message': json.dumps({
                            'action': 'manual open',
                            'time': arrow_now
                        })
                    }
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {
                        'type': 'update_door_state',
                        'message': json.dumps({
                            'door_status': 'open'
                        })
                    }
                )
            history_data.save()
            self.mqtt.publish("door-control", data)
            pass

        if 'door_save_pwd' in text_data_json:
            data = text_data_json['door_save_pwd']
            if not DoorPassword.objects.filter(password=data['pwd']).exists():
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
                data['ok'] = True
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {
                        'type': 'update_pwd_list',
                        'message': json.dumps({
                            'add_pwd_list': data
                        })
                    }
                )
            else:
                self.send(json.dumps({
                    'update_pwd_list': {
                        'ok': False,
                        'message': 'Mật khẩu đã tồn tại'
                    }
                }))
            pass

        if 'delete_password' in text_data_json:
            password = text_data_json['delete_password']
            if DoorPassword.objects.filter(password=password).exists():
                item = DoorPassword.objects.filter(password=password)[0]
                item.delete()
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {
                        'type': 'remove_pwd_list',
                        'message': json.dumps({
                            'remove_pwd_list': password
                        })
                    }
                )
            pass

        if 'local_pwd' in text_data_json:
            data = text_data_json['local_pwd']
            self.mqtt.publish('door-local', data[:4])
            pass

        if 'door_auto' in text_data_json:
            data = text_data_json['door_auto']
            db_state = DoorState.objects.filter(key='auto')[0]
            db_state.value = data
            db_state.save()
            message = json.dumps({
                'update_door_auto': data
            })
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    'type': 'update_auto',
                    'message': message
                }
            )

    def update_training_status(self, event):
        data = event['message']
        self.send(json.dumps({
            "type" : "TRAINING STATUS",
            "state" : "training" if data else "free"
        }))

    def update_history_list(self, event):
        data = json.loads(event['message'])
        self.send(json.dumps({'update_hty_list': data}))

    def update_devices_status(self, event):
        self.send(event['message'])

    def update_door_state(self, event):
        self.send(event['message'])

    def update_auto(self, event):
        self.send(event['message'])

    def update_pwd_list(self, event):
        self.send(event['message'])

    def remove_pwd_list(self, event):
        self.send(event['message'])

    def led_control(self, event):
        self.send(event['message'])
        message = json.loads(event['message'])
        self.send(json.dumps({
            "type": "UNSHIFT DATA TABLE",
            'id': message['id'],
            'state': message['state'],
            'time': datetime.now()
        },
            cls=DjangoJSONEncoder
        ))

    def temp_control(self, event):
        self.send(event['message'])
        message = json.loads(event['message'])
        self.send(json.dumps({
            "type": "UNSHIFT DATA TABLE",
            'id': message['id'],
            'state': message['state'],
            'time': datetime.now()
        },
            cls=DjangoJSONEncoder
        ))

    def rfid_control(self, event):
        self.send(event['message'])
        message = json.loads(event['message'])
        self.send(json.dumps({
            "type": "UNSHIFT DATA TABLE",
            'id': message['id'],
            'state': message['state'],
            'time': datetime.now()
        },
            cls=DjangoJSONEncoder
        ))

    # Receive message from room group
    def post_socket(self, event):
        message = event['door_status']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'door_status': message
        }))

    # MQTT METHODS
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            pass
        else:
            print("Connection failed")

    def on_message(self, client, userdata, msg):
        self.mqtt.loop_start()
