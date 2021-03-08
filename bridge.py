import json
import time

import requests
import serial
import serial.tools.list_ports


class FBridge():
    def setup(self):
        self.ser = None
        # print("Available ports: ")
        ports = serial.tools.list_ports.comports()
        self.portname = None
        for port in ports:
            # print("DEVICE: " + str(port.device))
            # print("DESCRIPTION: " + str(port.description))
            if 'arduino' in port.description.lower():
                self.portname = port.device

        print("Trying to connect to: " + self.portname)
        try:
            if self.portname is not None:
                self.ser = serial.Serial(self.portname, 9600, timeout=0)
                print("SUCCESSFULLY CONNECTED TO: " + str(self.portname))
        except:
            self.ser = None
            print("UNABLE TO CONNECT TO SERIAL PORT")

        self.inbuffer = []

    def loop(self):

        startTimeServ = time.time()
        startTimeArd = time.time()
        self.inbuffer = ""
        self.data = None

        print("Waiting for data..")

        while (True):
            if self.ser is not None and self.ser.in_waiting > 0:

                lastchar = self.ser.read().decode('utf-8')
                if lastchar == '\n':  # EOF
                    try:
                        # print("BRIDGE RICEVE RAW DATA: " + self.inbuffer)
                        self.data = json.loads(self.inbuffer)
                    except:
                        pass

                    # server communication
                    if time.time() > startTimeServ + 2 and self.data is not None:
                        if self.data["type"] == "D":
                            print("[DATA]: " + str(self.data))
                            try:
                                r1 = requests.get('http://localhost:80/new-sensor-feed', json=self.data)
                                ser_resp = json.loads(r1.text)
                                if ser_resp["hive_id"] is not None:
                                    json_id = "{\"type\":\"A\",\"id\":\"" + str(ser_resp["hive_id"]) + "\"}"
                                    self.ser.write(json_id.encode())
                                    self.ser.write(b'\n')
                                    # print("RECEIVED HIVE ID: " + json_id)
                                else:
                                    print("ATTENTION! Hive not autenticated on the server")
                            except:
                                print("ATTENTION! Bridge unable to send data to the server")
                        elif (self.data["type"] == "E"):
                            print("[ERROR]: " + self.data["desc"])
                        else:
                            print("ATTENTION! Communication error")

                        self.inbuffer = ""
                        startTimeServ = time.time()

                    # arduino communication
                    if time.time() > startTimeArd + 60 and self.data is not None:
                        json_comando = "{\"type\":\"C\",\"description\":\"sound\"}"
                        print("BRIDGE SENDS COMMAND: " + json_comando)
                        self.ser.write(json_comando.encode())
                        self.ser.write(b'\n')
                        self.inbuffer = ""
                        startTimeArd = time.time()

                else:
                    self.inbuffer = self.inbuffer + lastchar


if __name__ == '__main__':
    br = FBridge()
    br.setup()
    br.loop()
