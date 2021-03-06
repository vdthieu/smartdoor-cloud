from door.models import DeviceStates
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import export_graphviz
from sklearn.externals import joblib
from door.utils import binary_devices, on_control_predict_data
from sklearn import metrics
import shutil
import pydot
from door.models import TrainingLog,TrainingDeviceParameter,DoorState
from django.forms.models import model_to_dict

import datetime
import os

import asyncio
import threading
from door.utils import get_device_state

data_set_file = './door/output/dataset.csv'
tree_file = './door/output/tree/'
model_file = './door/output/modal'
training_result_file = './door/output/summary.csv'
# weekday
week_day = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


def make_train(progress_callback):
    def parse(callback):
        parse_data_from_local()
        threading.Thread(target=train_data, args=[progress_callback]).start()

    threading.Thread(target=parse, args=[progress_callback]).start()


# limit row for testing
def parse_data_from_local():
    print('start parse')
    date_formats = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S'
    ]
    # string value to parse in 1,0 data
    binary_values = [['OFF','ON'], ["CLOSE", "OPEN"], ["ABSENT", "PRESENT"], ['false', 'true']]

    input_file_name = './door/output/rawdata.txt'
    # limit row for testing
    limit = 500000

    column = ['weekDate', 'hour', 'min']
    value = [0, 0, 0]
    device_type = ['x', 'x', 'x']  # device is Classification = 'c', Regression = 'r'
    # get devices id
    input_file = open(input_file_name, 'r')
    line_count = 0
    previous_row_time = None

    for line in input_file:
        data_array = line.split(' ')
        line_count = line_count + 1
        # push devices to list
        if data_array[2] not in column:
            column.append(data_array[2])
            value.append(0)
            device_type.append('c')

    input_file = open(input_file_name, 'r')
    output_data = [column]
    index = 0
    for line in input_file:
        # counter for limit
        if index >= limit != 0:
            break

        data_array = line.split(' ')
        # convert time string
        time_string = ' '.join([data_array[0], data_array[1]])
        # device id
        device_id = data_array[2]
        # device state
        data_string = data_array[3].strip()

        device_time = None
        for date_format in date_formats:
            try:
                device_time = datetime.datetime.strptime(time_string, date_format)
                break
            except:
                continue
        if not device_time:
            continue

        device_state = None
        try:
            device_state = float(data_string)
            device_type[column.index(device_id)] = 'r'
        except ValueError:
            for state_pool in binary_values:
                if data_string in state_pool:
                    device_state = 1 if data_string == state_pool[1] else 0
        if not device_state and not device_state == 0:
            print('none')
            break

        # enrich row
        if previous_row_time:
            while previous_row_time < device_time:
                value[0:3] = [week_day[previous_row_time.weekday()], previous_row_time.hour, previous_row_time.minute]
                previous_row_time += datetime.timedelta(minutes=1)
                output_data.append(value.copy())
        previous_row_time = device_time + datetime.timedelta(minutes=1)
        # save
        value[column.index(device_id)] = device_state
        value[0:3] = [week_day[device_time.weekday()], device_time.hour, device_time.minute]
        output_data.append(value.copy())

        index = index + 1
    df = pd.DataFrame(output_data + [device_type])
    df.to_csv(data_set_file, index=False, header=False)
    pass


def parse_data(callback):
    column = ['weekDate', 'hour', 'min']
    value = [0, 0, 0, 0]
    for item in DeviceStates.objects.values('id').distinct():
        column.append(item['id'])
        value.append(0)

    values = []
    for row in DeviceStates.objects.all():
        value[column.index(row.id)] = row.state
        value[0:3] = [week_day[row.time.weekday()], row.time.hour, row.time.minute]
        values.append(value.copy())

    # write data set to csv
    df = pd.DataFrame([column] + values)
    df.to_csv(data_set_file, index=False, header=False)


def train_data(callback):
    data_set = pd.read_csv(data_set_file)
    device_type = data_set.tail(n=1)
    data_set.drop(device_type.index, inplace=True)

    device_list = list(data_set.columns)[3:]
    print(device_list)

    data_set = pd.get_dummies(data_set, columns=['weekDate'])

    tracked_time = datetime.datetime.now()

    result_header = ['Device', 'Training Type', "Mean Absolute Error", "Mean Squared Error", "Accuracy", "F1", "R^2", "Training Time(ms)"]
    result_data = [result_header]
    # create file for modal train
    try:
        os.mkdir(model_file)
    except FileExistsError:
        shutil.rmtree(model_file)
        os.mkdir(model_file)

    device_train_parameter_logs = []
    for index, device_name in enumerate(device_list):

        device_file_dir = "{}/{}".format(model_file, device_name)
        try:
            os.mkdir(device_file_dir)
        except FileExistsError:
            shutil.rmtree(device_file_dir)
            os.mkdir(device_file_dir)

        device_time = datetime.datetime.now().timestamp()
        labels = np.array(data_set[device_name])
        features = data_set.drop(device_name, axis=1)

        feature_list = list(features.columns)
        f = open(device_file_dir + '/feature.txt', "w")
        f.write(",".join(feature_list))
        f.close()

        features = np.array(features)

        train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size=0.25, random_state=42)

        test_labels = test_labels.astype('float')
        test_features = test_features.astype('float')
        train_labels = train_labels.astype('float')
        train_features = train_features.astype('float')

        if device_name in binary_devices:
            rf = RandomForestClassifier(n_estimators=100, random_state=25)
            rf.fit(train_features, train_labels)
        else:
            rf = RandomForestRegressor(n_estimators=10, random_state=25)
            rf.fit(train_features, train_labels)

        # save modal
        joblib.dump(rf, "{}/{}.pkl".format(device_file_dir, 'modal'))

        # predict
        predictions = rf.predict(test_features)

        train_time = datetime.datetime.now().timestamp() - device_time

        if device_name in binary_devices:
            mean_absolute_error = round(metrics.mean_absolute_error(test_labels, predictions), 4)
            mean_squared_error = round(metrics.mean_squared_error(test_labels, predictions), 4)
            accuracy = metrics.accuracy_score(test_labels, predictions)
            accuracy = round(accuracy,4)
            f1 = round(metrics.f1_score(test_labels, predictions), 2)
            result_data.append([device_name, 'Classification', mean_absolute_error, mean_squared_error, accuracy, f1, '-', train_time])
            device_parameter_instance = TrainingDeviceParameter.objects.create(
                device_name=device_name,
                type='C',
                f1=f1,
                accuracy=accuracy,
                mean_squared_error=mean_squared_error,
                mean_absolute_error=mean_absolute_error,
            )
            device_train_parameter_logs.append(device_parameter_instance)
        else:
            mean_absolute_error = round(metrics.mean_absolute_error(test_labels, predictions), 4)
            mean_squared_error = round(metrics.mean_squared_error(test_labels, predictions), 4)
            r2 = round(metrics.r2_score(test_labels, predictions), 2)
            result_data.append([device_name, 'Regression', mean_absolute_error, mean_squared_error, '-', '-', r2, train_time])
            device_parameter_instance = TrainingDeviceParameter.objects.create(
                device_name=device_name,
                type='R',
                r2=r2,
                mean_squared_error=mean_squared_error,
                mean_absolute_error=mean_absolute_error,
            )
            device_train_parameter_logs.append(device_parameter_instance)

        # save logs
        continue

        # Print tree
        try:
            os.mkdir(tree_file + device_name)
        except FileExistsError:
            shutil.rmtree(tree_file + device_name)
            os.mkdir(tree_file + device_name)
        tree_index = 0
        # for tree in rf.estimators_:
        for tree in rf.estimators_:
            export_graphviz(tree, out_file='tree.dot', feature_names=feature_list, rounded=True, precision=1)
            # Use dot file to create a graph
            (graph,) = pydot.graph_from_dot_file('tree.dot')
            # Write graph to a png file
            graph.write_png(tree_file + device_name + '/' + str(tree_index) + '.png')
            tree_index += 1
    total_time = datetime.datetime.now().timestamp() - tracked_time.timestamp()

    # save log
    train_log = TrainingLog.objects.create(
        created_at=datetime.datetime.now(),
        train_time=total_time,
        row_count=data_set.shape[0],
    )
    train_log.save()
    for log in device_train_parameter_logs:
        log.train_session = train_log
        log.save()

    callback({
        'created_at': train_log.created_at,
        'train_time': train_log.train_time,
        'row_count': train_log.row_count,
        'devices' : [model_to_dict(device,fields=[field.name for field in device._meta.fields]) for device in device_train_parameter_logs if device.device_name not in ["DOOR","RFID"]]
    })

    df = pd.DataFrame(result_data)
    df.to_csv(training_result_file, index=False, header=False)


def make_predict(callback,excepted=None):
    query = DoorState.objects.filter(key='prediction')
    if query.exists() and query[0].value == 'off':
        return
    # return
    predict = predict_data(excepted)
    current_array = get_device_state()
    dif = {}
    for device in current_array:
        try:
            if int(device['state']) != int(predict[device['id']]):
                dif[device['id']] = predict[device['id']]
        except Exception:
            continue
    callback(dif)
    pass


def predict_data(excepted= None):
    devices_state = get_device_state()
    now = datetime.datetime.now()
    [weekDate, hour, min] = [week_day[now.weekday()], now.hour, now.minute]
    # [weekDate, hour, min] = [week_day[now.weekday()], 17, 59]
    result = {}
    for folder_name in os.listdir(model_file):
        if folder_name in ['DOOR','RFID'] or (excepted and excepted == folder_name):
            continue
        folder_path = os.path.join(model_file, folder_name)
        if os.path.isdir(folder_path):
            feature_file = open(folder_path + '/feature.txt')
            feature_list = feature_file.read().split(',')
            rf = joblib.load(folder_path + '/modal.pkl')
            feature_file.close()

            value_vector = [0 for _ in range(len(feature_list))]
            for index, feature in enumerate(feature_list):
                if 'weekDate' in feature:
                    continue
                finder = [i for i in devices_state if i["id"] == feature]
                value_vector[index] = int(finder[0]['state']) if finder else 0
            try:
                value_vector[feature_list.index("weekDate_{}".format(weekDate))] = 1
                value_vector[feature_list.index("hour")] = hour
                value_vector[feature_list.index("min")] = min
            except ValueError:
                continue

            predict = rf.predict([value_vector])[0]
            result[folder_name] = int(predict)

            for index,item in enumerate(devices_state):
                if item['id'] == folder_name:
                    item['state'] = int(predict)
                    break
            print(folder_name, ": ",int(predict))
            print(' '.join(feature_list))
            print(' '.join([display_string_in_gap(value,len(feature_list[index])) for index, value in enumerate(value_vector)]))
    #
    # input_string = []
    # output_string = []
    # for device in devices_state:
    #     input_string.append(device['id'] + ":" + str(int(device['state'])))
    #     try:
    #         output_string.append(device['id'] + ":" + str(int(result[device['id']])))
    #     except Exception:
    #         output_string.append(device['id'] + ":--")
    # print(' '.join(input_string))
    # print(' '.join(output_string))
    return result


def display_string_in_gap(string, gap):
    string = str(string)
    while len(string) < gap:
        string += ' '

    return string
