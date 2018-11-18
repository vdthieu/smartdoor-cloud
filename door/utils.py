from door.models import DoorDevices, DeviceStates

led_ws_dict = {
    "LLIV": ['l', 'L'],
    "LKIT": ['k', 'K'],
    "LBED": ['b', 'B'],
    "LBAT": ['h', 'H'],
}

led_mq_id_dict = {
    'l': "LLIV",
    'L': "LLIV",
    'k': "LKIT",
    'K': "LKIT",
    'b': "LBED",
    'B': "LBED",
    'h': "LBAT",
    'H': "LBAT",
}


def bind_ws_to_mq_message(msg):
    if msg['type'] == 'LED CONTROL':
        return {
            "topic": "LED_CONTROL",
            "message": led_ws_dict[msg['id']][1 if msg['state'] else 0]
        }


def bind_mq_to_ws_message(topic, msg):
    if topic == 'LED_CONTROL':
        return {
            'type': 'LED CONTROL',
            'id': led_mq_id_dict[msg],
            'state': msg.isupper(),
            'update': False
        }
    return None


def get_online_devices_ws_message():
    online_devices = DoorDevices.objects.all()
    device_status = []
    for device in online_devices:
        device_status.append(
            {
                "id" : device.id,
                "status": device.status
            }
        )
    return {
        "type": "DEVICE STATUS",
        "device_status": device_status
    }


def get_devices_logs_from_times(time):
    queries = DeviceStates.objects.filter(time__lte=time).order_by('-time').values()
    queries = list(queries)
    return queries
    pass
