import paho.mqtt.client as mqtt
from door.models import DoorPassword, DoorHistory
from django.core.signals import request_finished
import datetime


def start_job():
    def on_message(client, userdata, msg):
        input_password = msg.payload.decode('ascii')[:4]
        print(input_password)
        if msg.topic == 'door-password':
            querry = DoorPassword.objects.filter(password=input_password)
            if querry.count() > 0:
                mqtt_client.publish('door-control', 'open')
                history_data = DoorHistory.objects.create(
                    action='password open',
                    time=datetime.datetime.now()
                )
                history_data.save()
            else:
                mqtt_client.publish('door-control', 'close')
                history_data = DoorHistory.objects.create(
                    action='wrong password',
                    time=datetime.datetime.now()
                )
                history_data.save()
            pass
        if msg.topic == 'door-autoclose':
            history_data = DoorHistory.objects.create(
                action='auto close',
                time=datetime.datetime.now()
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

