# from database.models import SensorFeed, User, HiveModel, ApiaryModel
import sqlite3
from datetime import datetime

from utility.SmartHive_bot import sendMessage


def checkStatus():
    print("Checking hive status...")
    conn = sqlite3.connect("sqlite:////../database/db.sqlite3")
    cur = conn.cursor()
    hives = cur.execute('''SELECT * FROM Hive''').fetchall()
    for hive in hives:
        last_sf = cur.execute('''SELECT timestamp FROM SensorFeed WHERE hive_id = (?)''', ((hive[0]),)).fetchall()[-1][0]
        min = (datetime.now() - datetime.strptime(last_sf, "%Y-%m-%d %H:%M:%S.%f")).total_seconds() / 60.0
        if int(min) > 30:
            user_id = cur.execute('''SELECT user_id FROM Apiary WHERE apiary_id = (?)''', ((hive[1]),)).fetchone()[0]
            idTelegram = cur.execute('''SELECT idTelegram FROM User WHERE id = (?)''', ((user_id),)).fetchone()[0]
            msg = "Attention! The hive with id " + str(hive[0]) + " is offline. \n" \
                                                                  "Last message received " + str(int(min)) + " min ago"
            sendMessage(msg=msg, chatID=idTelegram)
    conn.commit()
    conn.close()
