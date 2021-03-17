import csv

import sqlite3

connection = sqlite3.connect("../database/db.sqlite3")
cursor = connection.cursor()

with open('../database/1819G.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        # print(f'Timestamp: {row[7]} ')
        cursor.execute(
            "INSERT INTO SensorFeed VALUES (\"" + row[0] + "\", \"" + row[1] + "\", \"" + row[2] + "\", \"" + row[
                3] + "\",\"" + row[4] + "\", \"" + row[5] + "\", \"" + row[6] + "\", \"" + row[
                7] + "\" )")  # clear table

        # cursor.execute("INSERT INTO Apiary VALUES ('100', 'vg')") # clear table

        # sensorFeed = SensorFeed(hive_id=row,
        #                         temperature=row[2],
        #                         humidity=row[1],
        #                         weight=row[1],
        #                         ext_temperature=row[1],
        #                         ext_humidity=row[1],
        #                         wind=row[1],
        #                         timestamp=row[0])
        line_count += 1
    print(f'Processed {line_count} lines.')

connection.commit()
cursor.close()
connection.close()
