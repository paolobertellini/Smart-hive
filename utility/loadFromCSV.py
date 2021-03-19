import csv
from datetime import datetime

from database.models import SensorFeed
from server import db


# connection = sqlite3.connect("../database/db.sqlite3")
# cursor = connection.cursor()

def loadDataFromCSV(filename):
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            # print(f'Timestamp: {row[7]} ')
            # cursor.execute(
            #     "INSERT INTO SensorFeed VALUES (\"" + row[0] + "\", \"" + row[1] + "\", \"" + row[2] + "\", \"" + row[
            #         3] + "\",\"" + row[4] + "\", \"" + row[5] + "\", \"" + row[6] + "\", \"" + row[
            #         7] + "\" )")  # clear table

            sensorFeed = SensorFeed(hive_id=row[0],
                                    temperature=row[1],
                                    humidity=row[2],
                                    weight=row[3],
                                    ext_temperature=row[4],
                                    ext_humidity=row[5],
                                    wind=row[6],
                                    timestamp=datetime.strptime(row[7], '%Y-%m-%d %H:%M:%S'))
            db.session.add(sensorFeed)

            line_count += 1
        print(f'Processed {line_count} lines.')
        db.session.commit()

    # connection.commit()
    # cursor.close()
    # connection.close()
