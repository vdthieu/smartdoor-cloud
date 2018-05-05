import paho.mqtt.client as mqtt
from door.models import DoorPassword
from django.core.signals import request_finished


def start_job():

    def on_message(client, userdata, msg):
        input_password = msg.payload.decode('ascii')[:4]
        print(input_password)
        if msg.topic == 'door-password':
            querry = DoorPassword.objects.filter(password=input_password)
            if querry.count() > 0:
                mqtt_client.publish('door-control', 'open')
            else:
                mqtt_client.publish('door-control', 'close')

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            mqtt_client.subscribe('door-password')

    def disconnect(sender, **kwargs):
        print("FINISH")
        mqtt_client.disconnect()

    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect
    mqtt_client.connect('127.0.0.1', 1883, keepalive=10, bind_address="")
    mqtt_client.loop_start()
    request_finished.connect(disconnect)

