from door.models import DeviceStates
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import export_graphviz
from sklearn.metrics import mean_squared_error, mean_absolute_error

week_day = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


def parse_data():
    column = ['weekDate', 'hour', 'min', 'sec']
    value = [0, 0, 0, 0]
    for row in DeviceStates.objects.all():
        if row.id not in column:
            column.append(row.id)
            value.append(0)

    values = []
    for row in DeviceStates.objects.all():
        value[column.index(row.id)] = row.state
        value[0:4] = [week_day[row.time.weekday()], row.time.hour, row.time.minute, row.time.second]
        values.append(value.copy())

    # write data set to csv
    data = np.array([column] + values)
    data_set = pd.DataFrame(data=data[1:, 0:], columns=data[0, 0:])
    data_set.to_csv('./door/output/dataset.csv', index=False, header=False)

    data_set = pd.get_dummies(data_set, columns=['weekDate'])

    for device_name in column[4: len(column)]:
        print('train ',device_name)
        labels = np.array(data_set[device_name])
        features = np.array(data_set.drop(device_name, axis=1))

        train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size=0.25, random_state=42)

        rf = RandomForestRegressor(n_estimators=10, random_state=99999)
        rf.fit(train_features, train_labels)
        predictions = rf.predict(test_features)

        print('Mean Absolute Error ' + device_name + ':', round(mean_absolute_error(test_labels,predictions), 2), 'degrees.')
        print('Mean Square Error ' + device_name + ':', round(mean_squared_error(test_labels, predictions), 2), 'degrees.')
