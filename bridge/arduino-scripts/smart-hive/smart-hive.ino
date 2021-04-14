#include "pitches.h" //buzzer
#include <HX711_ADC.h> //weight
#include <Servo.h> //servo
#include <EEPROM.h> //EEPROM
#include <SimpleDHT.h> //temp
#include <ArduinoJson.h> //json

//pins
const int weight_dataPin = 12; //dati bilancia
const int weight_sckPin = 13; //clock bilancia
const int ledPin = 4; //led ??
const int servoPin = 9;
const int tempPin = 2;
const int buzzerPin = 8;

//fsm
int iState;
//serial
String in_buffer;
//buzzer
int duration = 500;  //miliseconds
bool alarm = false;
//weight
HX711_ADC LoadCell(weight_dataPin, weight_sckPin);
float calibrationValue;
float weight;
//servo
Servo myservo;
bool entrance = false;
unsigned long currentMillis;
unsigned long startMillis;
int pos = 0;
//temperature and humidity
SimpleDHT11 dht11;
float hum = 0.0;
float temp = 0.0;
//json
const size_t CAPACITY = JSON_OBJECT_SIZE(7);
StaticJsonDocument<CAPACITY> output;
JsonObject jsonData = output.to<JsonObject>();
StaticJsonDocument<200> input;
//eeprom
int eeAddressId = 0;
int eeAddressCal = 6;
int eeAddrressOff = 15;
char saved_id[6] = "none";
char new_id[6];
String id = String(saved_id);
unsigned long tareoffset = 0;


void setup() {
  // initialize serial communications
  Serial.begin(9600);

  //id
  EEPROM.get(eeAddressId, saved_id);
  id = String(saved_id);

  //led
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  //fsm
  iState = 0;

  //temp e hum

  //weight
  LoadCell.begin();
  unsigned long stabilizingtime = 2000; // tare preciscion can be improved by adding a few seconds of stabilizing time
  EEPROM.get(eeAddressCal, calibrationValue);
  LoadCell.setCalFactor(calibrationValue);
  EEPROM.get(eeAddrressOff, tareoffset);
  LoadCell.setTareOffset(tareoffset);

  //servo
  myservo.attach(servoPin);
  myservo.write(pos);
  startMillis = millis();
}
float i;
void loop() { //0 IDLE
  //1 READ
  //2 CHECK
  //3 AUTHENTICATION
  //4 DATA
  //5 READ SENSORS
  if (LoadCell.update()) {
      i = LoadCell.getData();
      output["w"] = i;
  }
  //IDLE --> READ
  if (iState == 0 && Serial.available() > 0) {
    iState = 1;
    char received = Serial.read();
    if (received == '\n') {
      iState = 2;
    }
    else {
      in_buffer += received;
      iState = 0;
    }
  }

  //READ --> CHECK
  if (iState == 2) {
    if (in_buffer.endsWith("}") && in_buffer.startsWith("{")) {

      DeserializationError error = deserializeJson(input, in_buffer);
      if (error) {
        in_buffer = "";
        iState = 0;
      }
      else if (input["type"] == "A") {
        iState = 3;
      }
      else if (input["type"] == "D") {
        iState = 4;
      }
      else {
        in_buffer = "";
        iState = 0;
      }
    }
    else {
      in_buffer = "";
      iState = 0;
    }
  }

  //CHECK --> AUTHENTICATION
  if (iState == 3) {
    if (input["id"] == "None") {
      output["type"] = "A";
      output["a_c"] = 33333;
      output["id"] = input["id"];
      serializeJson(output, Serial);
      Serial.println();
    }
    else {
      String arrived_id = input["id"];
      arrived_id.toCharArray(new_id, 6);
      EEPROM.put(eeAddressId, new_id);
    }
    iState = 0;
    in_buffer = "";
  }

  //CHECK --> DATA
  if (iState == 4) {
    if (input["e"] == "True" && entrance == false) {
      openServo();
      entrance = true;
    }
    if (input["e"] == "False" && entrance == true) {
      closeServo();
      entrance = false;
    }
    if (input["a"] == "True") {
      duration = input["duration"];
      alarm = true;
    }
    if (input["a"] == "False") {
      alarm = false;
    }

    if (input["d"] == "True") {
      byte data[40] = {0};
      output["type"] = "D";
      output["id"] = id;
      if (dht11.read2(tempPin, &temp, &hum, data)) {
        output["type"] = "E";
      }
      else {
        output["h"] = hum;
        output["t"] = temp;
      }


      serializeJson(output, Serial);
      Serial.println();
    }
    iState = 0;
    in_buffer = "";
  }

  if (alarm) {
    tone(8, NOTE_C3, 500);
  }
}

void openServo() {
  currentMillis = millis();
  if (currentMillis - startMillis >= 15) {
    for (pos = 0; pos <= 90; pos += 1) // goes from 0 degrees to 180 degrees
    {
      myservo.write(pos);
    }
  }
  startMillis = currentMillis;
}
void closeServo() {
  currentMillis = millis();
  if (currentMillis - startMillis >= 15) {
    for (pos = 90; pos >= 1; pos -= 1) // goes from 0 degrees to 180 degrees
    {
      myservo.write(pos);
    }
  }
  startMillis = currentMillis;
}
