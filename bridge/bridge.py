import json
import time

import requests
import serial
import serial.tools.list_ports

import _thread
import sys

online = 'http://smart-hive.ddns.net:8080'
local = 'http://127.0.0.1:8080'
davide = 'http://localhost'

server = online
ports_descriptions = ["arduino", "usb", "tty"]


def setup():

    try:
        print("Setting up bridge..")
        ports = []
        print("Available ports: ")
        available_ports = serial.tools.list_ports.comports()
        for port in available_ports:
            print("Device: " + str(port.device) + " Description: " + str(port.description))
            for desc in ports_descriptions:
                if desc in port.description.lower():
                    ports.append(port)
        # print("Trying to connect to: " + self.portname)
        return ports
    except:
        print("BRIDGE UNABLE TO FIND SERIAL PORTS")


def loop(threadName, port, updateInterval = 10):

    buffer=""

    try:
        if port.device is not None:
            serial_port = serial.Serial(port.device, 9600, timeout=0)
            print("BRIDGE SUCCESSFULLY CONNECTED TO: " + str(port))

    except Exception as e:
        print("ERROR: bridge unable to connect to " + str(port.name))
        print(e)
        raise

    try:
        command = "{\"type\":\"A\",\"association_code\":\"None\",\"id\":\"None\"}"
        serial_port.write(command.encode())
        serial_port.write(b'\n')
        print(serial_port.read().decode('utf-8'))
        print("B-->MC: association code request")


    except Exception as e:
        print("ERROR: bridge unable to ask association code to the microcontroller")
        print(e)
        raise

    while (True):
        if serial_port.is_open:
            try:
                lastchar = serial_port.read().decode('utf-8')
                if lastchar != '\n':  # EOF
                    buffer += lastchar
                else:
                    break
            except Exception as e:
                print("ERROR: bridge unable to read character from serial")
                print(e)
                raise
    try:
        # print("BRIDGE RICEVE RAW DATA: " + self.inbuffer)
        received = json.loads(buffer)
        print("MC-->B: association code answer")
        buffer = ""
    except Exception as e:
        print("ERROR: bridge unable to read json")
        print(e)
        raise

    try:
        association_code = {"association_code":received["association_code"]}
        r = requests.get(server + '/authentication', json=association_code)
        if r.text != "None":
            id = r.text
            print("C-->B: received id " + id)
        else:
            print("ERROR: bridge unable to receive id from server")
    except Exception as e:
        print("ERROR: bridge unable to connect to " + server)
        print(e)
        raise

    try:
        command = "{\"type\":\"A\",\"association_code\":\"" + str(received["association_code"]) + "\",\"id\":\"" + str(id) + "\"}"
        serial_port.write(command.encode())
        serial_port.write(b'\n')
        print("B-->MC: authentication id " + id)
    except Exception as e:
        print("ERROR: bridge unable to ask association code to the microcontroller")
        print(e)
        raise

    #
    #
    #     hiveFeedTime = time.time()
    #     updateTime = time.time()
    #
    #     self.inbuffer = ""
    #     self.data = None
    #     self.hive_id = None
    #     # self.ser.flush()
    #
    #     print("Setting up bridge..")
    #
    #     while (True):
    #         if self.ser is not None and self.ser.in_waiting > 0:
    #             lastchar = self.ser.read().decode('utf-8')
    #             if lastchar == '\n':
    #                 print("Bridge ready")
    #                 break
    #
    #     while (True):
    #         if self.ser is not None and self.ser.in_waiting > 0:
    #
    #             try:
    #                 lastchar = self.ser.read().decode('utf-8')
    #
    #                 if lastchar == '\n':  # EOF
    #                     try:
    #                         # print("BRIDGE RICEVE RAW DATA: " + self.inbuffer)
    #                         self.data = json.loads(self.inbuffer)
    #                         self.inbuffer = ""
    #                     except:
    #                         print("ATTENTION! bridge unable to interpret json")
    #
    #                     # update hive status
    #                     if time.time() > updateTime + updateInterval and self.data is not None:
    #                         try:
    #                             if self.hive_id is not None:
    #                                 id = {"id": self.hive_id}
    #                                 r = requests.get(server + '/bridge-channel', json=id)
    #                                 ser_resp = json.loads(r.text)
    #                                 duration = 500
    #                                 hiveFeedInterval = ser_resp["update_freq"]
    #                                 print(hiveFeedInterval)
    #                                 json_comando = "{\"type\":\"C\",\"entrance\":\"" + str(
    #                                     ser_resp["entrance"]) + "\", \"alarm\":\"" + str(
    #                                     ser_resp["alarm"]) + "\", \"duration\":\"" + str(duration) + "\"}"
    #                                 print("B --> A: " + json_comando)
    #
    #                                 self.ser.write(json_comando.encode())
    #                                 self.ser.write(b'\n')
    #                                 updateTime = time.time()
    #
    #                         except:
    #                             print("ATTENTION! Bridge unable to receive data from server and update hive status")
    #
    #                     # hive feed
    #                     if time.time() > hiveFeedTime + hiveFeedInterval and self.data is not None:
    #                         try:
    #                             if self.data["type"] == "D":
    #                                 print("A --> B [DATA]: " + str(self.data))
    #                                 r1 = requests.get(server + '/new-sensor-feed', json=self.data)
    #                                 ser_resp = json.loads(r1.text)
    #                                 if ser_resp["hive_id"] is not None:
    #                                     json_id = "{\"type\":\"A\",\"id\":\"" + str(ser_resp["hive_id"]) + "\"}"
    #                                     self.hive_id = str(ser_resp["hive_id"])
    #                                     self.ser.write(json_id.encode())
    #                                     self.ser.write(b'\n')
    #                                     # print("RECEIVED HIVE ID: " + json_id)
    #                                 else:
    #                                     print("ATTENTION! Hive not autenticated on the server")
    #                             elif (self.data["type"] == "E"):
    #                                 print("A --> B [ERROR]: " + self.data["desc"])
    #                             else:
    #                                 print("ATTENTION! Communication error")
    #
    #                             hiveFeedTime = time.time()
    #
    #                         except:
    #                             print("ATTENTION! Bridge unable to send hive feed data to the server")
    #
    #                 else:
    #                     self.inbuffer = self.inbuffer + lastchar
    #
    #             except:
    #                 pass

if __name__ == '__main__':

    ports = setup()
    # for port in ports:
    #     _thread.start_new_thread(loop, ("Hive-1", port))
    #     print("ERROR: unable to start thread")
    print('ciao'+ str(ports[0]))
    loop("paolo", ports[0])