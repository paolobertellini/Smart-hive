import sqlite3

connection = sqlite3.connect("../database/db.sqlite3")
cursor = connection.cursor()
# cursor.execute("INSERT INTO Apiary VALUES ('100', 'vg')") # clear table
cursor.execute("SELECT * FROM Hive")  # clear table
results = cursor.fetchall()
for r in results:
    print(r)
cursor.close()
connection.close()
