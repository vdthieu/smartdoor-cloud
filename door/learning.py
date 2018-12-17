from door.models import DeviceStates
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import export_graphviz
from sklearn import metrics
from sklearn.externals import joblib
from door.utils import binary_devices
from sklearn import metrics
import shutil
import pydot

from datetime import datetime
import os

data_set_file = './door/output/dataset.csv'
tree_file = './door/output/tree/'
model_file = './door/output/modal'
training_result_file = './door/output/summary.csv'
# weekday
week_day = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


# limit row for testing

def parse_data():
    column = ['weekDate', 'hour', 'min', 'sec']
    value = [0, 0, 0, 0]
    for item in DeviceStates.objects.values('id').distinct():
        column.append(item['id'])
        value.append(0)

    values = []
    for row in DeviceStates.objects.all():
        value[column.index(row.id)] = row.state
        value[0:4] = [week_day[row.time.weekday()], row.time.hour, row.time.minute, row.time.second]
        values.append(value.copy())

    # write data set to csv
    df = pd.DataFrame([column] + values)
    df.to_csv(data_set_file, index=False, header=False)
    # data = np.array([column] + values)
    # data_set = pd.DataFrame(data=data[1:, 0:], columns=data[0, 0:])
    # data_set.to_csv('./door/output/dataset.csv', index=False, header=False)

    # data_set = pd.get_dummies(data_set, columns=['weekDate'])
    #
    # for device_name in column[4: len(column)]:
    #     print('train ', device_name)
    #     labels = np.array(data_set[device_name])
    #     features = np.array(data_set.drop(device_name, axis=1))
    #
    #     train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size=0.25, random_state=42)
    #
    #     rf = RandomForestRegressor(n_estimators=10, random_state=99999)
    #     rf.fit(train_features, train_labels)
    #     predictions = rf.predict(test_features)
    #
    #     print('Mean Absolute Error ' + device_name + ':', round(mean_absolute_error(test_labels, predictions), 2), 'degrees.')
    #     print('Mean Square Error ' + device_name + ':', round(mean_squared_error(test_labels, predictions), 2), 'degrees.')


def train_data():
    data_set = pd.read_csv(data_set_file)
    device_type = data_set.tail(n=1)
    data_set.drop(device_type.index, inplace=True)

    device_list = list(data_set.columns)[4:]

    data_set = pd.get_dummies(data_set, columns=['weekDate'])

    tracked_time = datetime.now()

    result_header = ['Device', 'Training Type', "Mean Absolute Error", "Mean Squared Error", "Accuracy", "F1", "R^2", "Training Time(ms)"]
    result_data = [result_header]
    # create file for modal train
    try:
        os.mkdir(model_file)
    except FileExistsError:
        shutil.rmtree(model_file)
        os.mkdir(model_file)

    for index, device_name in enumerate(device_list):

        device_time = datetime.now().timestamp()
        labels = np.array(data_set[device_name])
        features = data_set.drop(device_name, axis=1)

        feature_list = list(features.columns)
        features = np.array(features)

        train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size=0.25, random_state=42)

        test_labels = test_labels.astype('float')
        test_features = test_features.astype('float')
        train_labels = train_labels.astype('float')
        train_features = train_features.astype('float')

        if device_name in binary_devices:
            print(device_name + ': classification')
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(train_features, train_labels)
        else:
            print(device_name + ': regression')
            rf = RandomForestRegressor(n_estimators=10, random_state=42)
            rf.fit(train_features, train_labels)

        joblib.dump(rf,"{}/{}.pkl".format(model_file,device_name))

        # rf.predic

        # predict
        predictions = rf.predict(test_features)

        train_time = datetime.now().timestamp() - device_time

        if device_name in binary_devices:
            mean_absolute_error = round(metrics.mean_absolute_error(test_labels, predictions), 2)
            mean_squared_error = round(metrics.mean_squared_error(test_labels, predictions), 2)
            accuracy = round(metrics.accuracy_score(test_labels, predictions), 2)
            f1 = round(metrics.f1_score(test_labels, predictions), 2)
            # print('Mean Absolute Error ', device_name, ':', mean_absolute_error)
            # print('Mean Squared Error ', device_name, ':', mean_squared_error)
            # print('Accuracy ', device_name, ':', accuracy)
            # print('F1 ', device_name, ':', f1)

            result_data.append([device_name, 'Classification', mean_absolute_error, mean_squared_error, accuracy, f1, '-', train_time])
        else:
            mean_absolute_error = round(metrics.mean_absolute_error(test_labels, predictions), 2)
            mean_squared_error = round(metrics.mean_squared_error(test_labels, predictions), 2)
            r2 = round(metrics.r2_score(test_labels, predictions), 2)
            # print('Mean Absolute Error ', device_name, ':', mean_absolute_error)
            # print('Mean Squared Error ', device_name, ':', mean_squared_error)
            # print('R^2', device_name, ':', r2)

            result_data.append([device_name, 'Regression', mean_absolute_error, mean_squared_error, '-', '-', r2, train_time])
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
    print('total training time: ' + str(datetime.now() - tracked_time))
    df = pd.DataFrame(result_data)
    df.to_csv(training_result_file, index=False, header=False)
    pass


def predict_data():
    pass
