from door.models import DeviceStates
import pandas as pd

week_day = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


def parse_data():
    column = ['weekDate', 'hour', 'min', 'sec']
    value = [0, 0, 0, 0]
    for row in DeviceStates.objects.all():
        if row.id not in column:
            column.append(row.id)
            value.append(0)

    output_data = [column]
    for row in DeviceStates.objects.all():
        value[column.index(row.id)] = row.state
        value[0:4] = [week_day[row.time.weekday()], row.time.hour, row.time.minute, row.time.second]
        output_data.append(value.copy())

    df = pd.DataFrame(output_data)
    df.to_csv('./door/output/dataset.csv', index=False, header=False)
