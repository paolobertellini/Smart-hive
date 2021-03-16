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


def configuration(serial_port):

    buffer=""

    try:
        command = "{\"type\":\"A\",\"a_c\":\"None\",\"id\":\"None\"}"
        serial_port.write(command.encode())
        serial_port.write(b'\n')
        print("B  --> MC : association code request")


    except Exception as e:
        print("ERROR: bridge unable to ask association code to the microcontroller")
        print(e)
        return False

    while (True):
        if serial_port.in_waiting > 0:
            try:
                lastchar = serial_port.read().decode('utf-8')
                if lastchar != '\n':  # EOF
                    buffer += lastchar
                else:
                    break
            except Exception as e:
                print("ERROR: bridge unable to read character from serial")
                print(e)
                return False
    try:
        # print("BRIDGE RICEVE RAW DATA: " + self.inbuffer)
        received = json.loads(buffer)
        serial_port.flushInput()
        print("MC --> B  : association code answer")

    except Exception as e:
        print("ERROR: bridge unable to read json")
        print(e)
        return False

    try:
        association_code = {"association_code":received["a_c"]}
        r = requests.get(server + '/authentication', json=association_code)
        if r.text != "None":
            id = r.text
            print("C  --> B  : received id " + id)
        else:
            print("ERROR: bridge unable to receive id from server")
    except Exception as e:
        print("ERROR: bridge unable to connect to " + server)
        print(e)
        return False

    try:
        command = "{\"type\":\"A\",\"a_c\":\"" + str(received["a_c"]) + "\",\"id\":\"" + str(id) + "\"}"
        serial_port.write(command.encode())
        serial_port.write(b'\n')
        print("B  --> MC : authentication id " + id)
    except Exception as e:
        print("ERROR: bridge unable to ask association code to the microcontroller")
        print(e)
        return False

    return True, id


def loop(threadName, port, updateInterval = 10):

    try:
        if port.device is not None:
            serial_port = serial.Serial(port.device, 9600, timeout=0)
            print("BRIDGE SUCCESSFULLY CONNECTED TO: " + str(port))
            time.sleep(2)
    except Exception as e:
        print("ERROR: bridge unable to connect to " + str(port.name))
        print(e)
        return False


    result, id = configuration(serial_port)
    if result:
        print("HIVE SUCCESFULLY AUTHENTICATED ON SERVER")
    else:
        print("ERROR: bridge unable to authenticate hive to " + str(server))

    updateTime = time.time()
    hiveFeedTime = time.time()
    buffer = ""
    data = False

    while(True):
        if time.time() > updateTime + updateInterval:
            try:
                r = requests.get(server + '/bridge-channel', json={"id":id})
                ser_resp = json.loads(r.text)
                duration = 500
                hiveFeedInterval = ser_resp["update_freq"]
                if time.time() > hiveFeedTime + hiveFeedInterval:
                    data = True
                    hiveFeedTime = time.time()
                else:
                    data = False
                print("Next hive feed in " + str(int(hiveFeedInterval - (time.time() - hiveFeedTime))) + " sec")
                json_comando = "{\"type\":\"D\"," \
                               "\"e\":\"" + str(ser_resp["entrance"]) + "\"," \
                               "\"a\":\"" + str(ser_resp["alarm"]) + "\"," \
                               "\"d\":\"" + str(data) + "\"}"

                print("B  --> MC : " + json_comando)

                serial_port.write(json_comando.encode())
                serial_port.write(b'\n')
                updateTime = time.time()

            except Exception as e:
                print("ERROR: bridge unable to update hive state")
                print(e)
                return False

        if serial_port.in_waiting > 0:
            try:
                lastchar = serial_port.read().decode('utf-8')
                if lastchar != '\n':  # EOF
                    buffer += lastchar
                else:
                    received = json.loads(buffer)
                    if received['type'] == "D":
                        print("MC --> B  : " + str(buffer))
                        hiveFeed = {'hive_id':received['id'],
                                    'temperature':received['t'],
                                    'humidity':received['h'],
                                    'weight':received['w']}
                        r1 = requests.get(server + '/new-sensor-feed', json=hiveFeed)
                        print("B  --> C  : " + str(hiveFeed))
                        if r1.text == "200":
                            print("C  --> B  : hive feed saved to database")
                    buffer = ""
            except Exception as e:
                print("ERROR: bridge unable to read character from serial")
                print(e)
                return False



if __name__ == '__main__':

    ports = setup()
    # for port in ports:
    #     _thread.start_new_thread(loop, ("Hive-1", port))
    #     print("ERROR: unable to start thread")
    loop("paolo", ports[0])