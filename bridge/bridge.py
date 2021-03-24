import csv
import datetime
import json
import time

import requests
import serial
import serial.tools.list_ports

peppe = 'http://smart-hive.ddns.net:8080'
local = 'http://127.0.0.1:8080'
davide = 'http://localhost'

online = "https://smarthive.pythonanywhere.com"

server = peppe
save_csv = True
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
    buffer = ""

    try:
        command = "{\"type\":\"A\",\"a_c\":\"None\",\"id\":\"None\"}"
        serial_port.write(command.encode())
        serial_port.write(b'\n')
        print("B  --> MC : association code request")


    except Exception as e:
        print("ERROR: bridge unable to ask association code to the microcontroller")
        print(e)
        return False, None

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
                return False, None
    try:
        # print("BRIDGE RICEVE RAW DATA: " + self.inbuffer)
        received = json.loads(buffer)
        serial_port.flushInput()
        print("MC --> B  : association code answer")

    except Exception as e:
        print("ERROR: bridge unable to read json")
        print(e)
        return False, None

    try:
        association_code = {"association_code": received["a_c"]}
        r = requests.get(server + '/authentication', json=association_code)
        if r.text != "None":
            id = r.text
            print("C  --> B  : received id " + id)
        else:
            print("ERROR: bridge unable to receive id from server")
    except Exception as e:
        print("ERROR: bridge unable to connect to " + server)
        print(e)
        return False, None

    try:
        command = "{\"type\":\"A\",\"a_c\":\"" + str(received["a_c"]) + "\",\"id\":\"" + str(id) + "\"}"
        serial_port.write(command.encode())
        serial_port.write(b'\n')
        print("B  --> MC : authentication id " + id)
    except Exception as e:
        print("ERROR: bridge unable to ask association code to the microcontroller")
        print(e)
        return False, None

    return True, id


def loop(threadName, port, updateInterval=10):
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
    while not result:
        result, id = configuration(serial_port)
        print("Waiting a response from: " + str(server))
    print("HIVE SUCCESFULLY AUTHENTICATED ON SERVER")


    updateTime = time.time()
    hiveFeedTime = time.time()
    buffer = ""

    while (True):
        if time.time() > updateTime + updateInterval:
            try:
                r = requests.get(server + '/bridge-channel', json={"id": id})
                ser_resp = json.loads(r.text)
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
                                                                                                              "\"d\":\"" + str(
                    data) + "\"}"

                print("B  --> MC : " + json_comando)

                serial_port.write(json_comando.encode())
                serial_port.write(b'\n')
                updateTime = time.time()

            except Exception as e:
                print("ERROR: bridge unable to update hive state")
                print(e)

        if serial_port.in_waiting > 0:
            try:
                lastchar = serial_port.read().decode('utf-8')
            except Exception as e:
                print("ERROR: bridge unable read on serial")
                print(e)
            if lastchar != '\n':  # EOF
                buffer += lastchar
            else:
                try:
                    received = json.loads(buffer)
                except Exception as e:
                    print("ERROR: bridge unable interpret json")
                    print(e)
                try:
                    if received['type'] == "D":
                        print("MC --> B  : " + str(buffer))
                        hiveFeed = {'hive_id': received['id'],
                                    'temperature': received['t'],
                                    'humidity': received['h'],
                                    'weight': received['w']}
                        r1 = requests.get(server + '/new-sensor-feed', json=hiveFeed)
                        print("B  --> C  : " + str(hiveFeed))
                        if r1.text == "200":
                            print("C  --> B  : hive feed saved to database")

                except Exception as e:
                    print("ERROR: bridge unable to send data to server")
                    print(e)
                try:
                    if save_csv:
                        with open(str(threadName) + '_hiveFeed_data.csv', mode='a', newline='') as csv_file:
                            csv_writer = csv.writer(csv_file)
                            csv_writer.writerow(
                                [datetime.datetime.now(), received['t'], received['h'], received['w']])
                            print("B  --> CSV  : hive feed succesfully saved to csv file")
                except Exception as e:
                    print("ERROR: bridge unable to save data to csv")
                    print(e)
                if received['type'] == "E":
                    print("MC --> B  : sensor error " + str(buffer))

                buffer = ""




if __name__ == '__main__':
    ports = setup()

    loop("test", ports[0], 10)  # testing without threads

    # for i, port in enumerate(ports):
    #     name = "Hive-" + str(i)
    #     try:
    #         _thread.start_new_thread(loop, (name, port))
    #         print("Started thread " + name + " on port " + str(port)) # insert breakpoint here
    #     except:
    #         print("Unable to start thread " + name + " on port " + str(port))
