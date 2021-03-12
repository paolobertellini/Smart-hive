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
int iState; //IDLE
//serial
unsigned long lasttime;
String error;
//buzzer
int duration = 500;  // 500 miliseconds
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
StaticJsonDocument<CAPACITY> jdata;
StaticJsonDocument<CAPACITY> jerr;
JsonObject jsonData = jdata.to<JsonObject>();
JsonObject jsonerr = jerr.to<JsonObject>();
//eeprom
int eeAddressId=0;
int eeAddressCal = 6;
char saved_id[6] = "none";
char new_id[6];
String old_id(saved_id);

void setup() {
  // initialize serial communications
  Serial.begin(9600);

  //id
  EEPROM.get(eeAddressId, saved_id);
  old_id= String(saved_id);
  
  //led
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  //fsm
  iState = 0;
  lasttime = millis();

  //temp e hum

  //weight
  LoadCell.begin();
  unsigned long stabilizingtime = 2000; // tare preciscion can be improved by adding a few seconds of stabilizing time
  boolean _tare = true; //set this to false if you don't want tare to be performed in the next step
  EEPROM.get(eeAddressCal, calibrationValue);
  LoadCell.setCalFactor(calibrationValue);
  LoadCell.start(stabilizingtime, _tare);

  //servo
  myservo.attach(servoPin);
  myservo.write(pos);
  startMillis = millis();
}

void loop() { //0 IDLE 1 WRITE-MES 2 WRITE-DATA 3 READ


  //3: read
  if (iState == 0 && Serial.available() > 0) {
    iState = 3;
    String received = Serial.readStringUntil('\n');

    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, received);
    if (error) {
      iState = 1;
      jerr["type"] = "E";
      jerr["desc"] = "Bridge communication error";
    }

    if (doc["type"] == "A") {
      String arrived_id = doc["id"];
      arrived_id.toCharArray(new_id, 6);
      if (arrived_id != old_id){
        EEPROM.put(eeAddressId, new_id);
        old_id = arrived_id;
      }
    }
    if (doc["type"] == "C") {
      if (doc["entrance"] == "True" && entrance == false) {
        openServo();
        entrance = true;
      }
      if (doc["entrance"] == "False" && entrance == true) {
        closeServo();
        entrance = false;
      }
      if (doc["alarm"] == "True") {
        int d = doc["duration"];
        tone(8, NOTE_C3, d);
        doc["alarm"] = "False";
      }
    }

    iState = 0;
  }

  //2: write data
  if (iState == 0 && (millis() - lasttime) > 2000) {
    lasttime = millis();

    //temp and hum
    byte data[40] = {0};
    if (dht11.read2(tempPin, &temp, &hum, data)) {
      iState = 1;
      jerr["type"] = "E";
      jerr["desc"] = "Temperature and humudity sensor error";
    }
    else {
      iState = 2;
    }
    if (!LoadCell.update()) {
      iState = 1;
      jerr["type"] = "E";
      jerr["desc"] = "Weight sensor error";
    }
    weight = LoadCell.getData();

    if (iState == 2) {
      jdata["type"] = "D";
      jdata["hive_id"] = old_id;
      jdata["humidity"] = hum;
      jdata["temperature"] = temp;
      jdata["weight"] = weight;
      jdata["association_code"] = 33333;
      iState = 0;
      serializeJson(jdata, Serial);
      Serial.println();

    }
  }

  if (iState == 1) {
    serializeJson(jerr, Serial);
    Serial.println();
    iState = 0;
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
