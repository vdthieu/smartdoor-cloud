from door.models import DoorDevices, DeviceStates, TrainingDeviceParameter, TrainingLog, DoorState
from django.forms.models import model_to_dict

binary_type = 1
multiple_type = 2

binary_devices = ["LLIV", "LKIT", 'LBED', 'LBAT']

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
    "RFID": {
        "default_value": False,
        "type": binary_type
    }
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
    queries = list(queries)[:10]
    return queries
    pass


def get_devices_state_ws_message():
    device_states = []
    for device_id in default_device_state.keys():
        queries = DeviceStates.objects.filter(id=device_id).order_by('-time')
        if queries.exists():
            device_states.append({
                "id": device_id,
                "state":
                    queries[0].state == 1
                    if default_device_state[device_id]['type'] == binary_type
                    else queries[0].state
            })
        else:
            print(device_id, 'default')
            device_states.append({
                "id": device_id,
                "state": default_device_state[device_id]['default_value']
            })
    return {
        "type": "DEVICE STATUS",
        "device_states": device_states
    }


def get_training_summary_ws_message():
    train_log = TrainingLog.objects.order_by('-created_at')
    if train_log.exists():
        train_log = train_log[0]
    else:
        return {}
    devices = TrainingDeviceParameter.objects.filter(train_session=train_log)
    devices = [model_to_dict(device, fields=[field.name for field in device._meta.fields ])
               for device in devices if device.device_name not in ["DOOR","RFID"]]
    data = {
        'created_at': train_log.created_at,
        'train_time': train_log.train_time,
        'row_count': train_log.row_count,
        'devices': devices
    }
    return {
        'type' : "TRAINING SUMMARY",
        'data' : data
    }


# get latest devices status
def get_device_state():
    device_states = []
    for device_id in default_device_state.keys():
        queries = DeviceStates.objects.filter(id=device_id).order_by('-time')
        if queries.exists():
            device_states.append({
                "id": device_id,
                "state":
                    queries[0].state == 1
                    if default_device_state[device_id]['type'] == binary_type
                    else queries[0].state
            })
        else:
            device_states.append({
                "id": device_id,
                "state": default_device_state[device_id]['default_value']
            })
    return device_states


def on_control_predict_data(data, mqtt_instance):
    for key in data:
        if key == 'RFID':
            mqtt_instance.publish(
                'RFID',
                'on' if data[key] > 0.5 else 'off'
            )
            continue

        if key in binary_devices:
            mqtt_message = bind_ws_to_mq_message({
                'type': 'LED CONTROL',
                'id': key,
                'state': data[key] > 0.5
            })
            mqtt_instance.publish(mqtt_message['topic'], mqtt_message['message'])
            continue
        mqtt_instance.publish(key, str(data[key]))


def get_training_status():
    """
        return true if is traing
    """
    try:
        query = DoorState.objects.get(key='training')
        return query.value == 'on'
    except DoorState.DoesNotExist:
        return False


def toggle_training_status(value = None):
    try:
        query = DoorState.objects.get(key='training')
        if value is None:
            query.value = 'on' if query.value == 'off' else 'off'
        else:
            query.value = 'on' if value else 'off'
        query.save()
        return query.value == 'on'
    except DoorState.DoesNotExist:
        instance = DoorState.objects.create(key='training', value='on')
        instance.save()
        return True
