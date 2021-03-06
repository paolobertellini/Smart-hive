import sqlite3
from app import db, login_manager
from app.base.models import ApiaryModel


connection = sqlite3.connect("db.sqlite3")
cursor = connection.cursor()
# cursor.execute("INSERT INTO Apiary VALUES ('100', 'vg')") # clear table
cursor.execute("SELECT * FROM Apiary") # clear table
results = cursor.fetchall()
for r in results:
    print(r)
cursor.close()
connection.close()