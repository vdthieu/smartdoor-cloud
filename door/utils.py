from door.models import DoorDevices, DeviceStates

binary_type = 1
multiple_type = 2

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

default_device_state = {
    'LLIV': {
        "default_value": False,
        "type": binary_type
    },
    'LKIT': {
        "default_value": False,
        "type": binary_type
    },
    'LBED': {
        "default_value": False,
        "type": binary_type
    },
    'LBAT': {
        "default_value": False,
        "type": binary_type
    },
    'THOM': {
        "default_value": 50,
        "type": multiple_type
    },
    'TOFF': {
        "default_value": 50,
        "type": multiple_type
    },
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
                "id": device.id,
                "status": device.status
            }
        )
    return {
        "type": "BOARD STATUS",
        "device_status": device_status
    }


def get_devices_logs_from_times(time):
    queries = DeviceStates.objects.filter(time__lte=time).order_by('-time').values()
    queries = list(queries)[:100]
    return queries
    pass


def get_devices_state_ws_message():
    device_states = []
    for device_id in default_device_state.keys():
        queries = DeviceStates.objects.filter(id=device_id).order_by('-time')
        if queries.exists():
            a = queries[0]
            device_states.append({
                "id": device_id,
                "state":
                    queries[0].state == 1
                    if default_device_state[device_id]['type'] == binary_type
                    else queries[0].state
            })
        else:
            print(device_id, 'defautl')
            device_states.append({
                "id": device_id,
                "state": default_device_state[device_id]['default_value']
            })
    return {
        "type": "DEVICE STATUS",
        "device_states": device_states
    }
