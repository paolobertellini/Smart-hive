import json
import time

import requests
import serial
import serial.tools.list_ports

online = 'http://smart-hive.ddns.net:8080'
local = 'http://127.0.0.1:8080'
davide = 'http://localhost'

server = local

updateInterval = 10
hiveFeedInterval = 120

class FBridge():
    def setup(self):
        self.ser = None
        self.portname = None
        try:
            # print("Available ports: ")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                # print("DEVICE: " + str(port.device))
                # print("DESCRIPTION: " + str(port.description))
                if 'usb' in port.description.lower():
                    self.portname = port.device
            # print("Trying to connect to: " + self.portname)
        except:
            print("BRIDGE UNABLE TO FIND SERIAL PORT")

        try:
            if self.portname is not None:
                self.ser = serial.Serial(self.portname, 9600, timeout=0)
                print("BRIDGE SUCCESSFULLY CONNECTED TO: " + str(self.portname))
        except:
            self.ser = None
            print("BRIDGE UNABLE TO CONNECT TO SERIAL PORT")

        try:
            r = requests.get(server + '/autentication')
            print("BRIDGE SUCCESSFULLY CONNECTED TO " + str(server))
            if r.text != "None":
                self.hive_id = r.text
                print("HIVE SUCCESSFULLY AUTENTICATED TO SERVER with id " + str(self.hive_id))
            else:
                print("BRIDGE UNABLE TO CONNECT TO SERVER")
        except:
            print("BRIDGE UNABLE TO CONNECT TO SERVER")

    def loop(self):

        hiveFeedTime = time.time()
        updateTime = time.time()
        self.inbuffer = ""
        self.data = None

        # self.ser.flush()

        print("Setting up bridge..")

        while (True):
            if self.ser is not None and self.ser.in_waiting > 0:
                lastchar = self.ser.read().decode('utf-8')
                if lastchar == '\n':
                    print("Bridge ready")
                    break

        while (True):
            if self.ser is not None and self.ser.in_waiting > 0:

                try:
                    lastchar = self.ser.read().decode('utf-8')

                    if lastchar == '\n':  # EOF
                        try:
                            # print("BRIDGE RICEVE RAW DATA: " + self.inbuffer)
                            self.data = json.loads(self.inbuffer)
                        except:
                            pass

                        # update hive status
                        if time.time() > updateTime + updateInterval and self.data is not None:
                            try:
                                if self.hive_id is not None:
                                    id = {"id": self.hive_id}
                                    r = requests.get(server + '/bridge-channel', json=id)
                                    ser_resp = json.loads(r.text)
                                    duration = 500
                                    json_comando = "{\"type\":\"C\"," \
                                                   "\"entrance\":\"" + str(ser_resp["entrance"]) + "\"," \
                                                   " \"alarm\":\"" + str(ser_resp["alarm"]) + "\", " \
                                                   "\"duration\":\"" + str(duration) + "\"}"
                                    print("B --> A: " + json_comando)
                                    hiveFeedInterval = ser_resp["update_freq"]
                                    self.ser.write(json_comando.encode())
                                    self.ser.write(b'\n')
                                    self.inbuffer = ""
                                    updateTime = time.time()

                            except:
                                print("ATTENTION! Bridge unable to receive data from server and update hive status")

                        # hive feed
                        if time.time() > hiveFeedTime + hiveFeedInterval and self.data is not None:
                            try:
                                if self.data["type"] == "D":
                                    print("A --> B [DATA]: " + str(self.data))
                                    r1 = requests.get(server + '/new-sensor-feed', json=self.data)
                                    ser_resp = json.loads(r1.text)
                                    if ser_resp["resp"] != 200:
                                        print("ATTENTION! Unable to save sensor feed on database")
                                    else:
                                        print("ATTENTION! Hive not autenticated on the server")
                                elif (self.data["type"] == "E"):
                                    print("ARDUINO --> BRIDGE [ERROR]: " + self.data["desc"])
                                else:
                                    print("ATTENTION! Communication error")

                                self.inbuffer = ""
                                hiveFeedTime = time.time()

                            except:
                                print("ATTENTION! Bridge unable to send hive feed data to the server")

                    else:
                        self.inbuffer = self.inbuffer + lastchar

                except:
                    pass

if __name__ == '__main__':
    br = FBridge()
    br.setup()
    br.loop()
