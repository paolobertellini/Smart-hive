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
char saved_id[6] = "none";
char new_id[6];
String id = String(saved_id);

#define NOTE_B0  31
#define NOTE_C1  33
#define NOTE_CS1 35
#define NOTE_D1  37
#define NOTE_DS1 39
#define NOTE_E1  41
#define NOTE_F1  44
#define NOTE_FS1 46
#define NOTE_G1  49
#define NOTE_GS1 52
#define NOTE_A1  55
#define NOTE_AS1 58
#define NOTE_B1  62
#define NOTE_C2  65
#define NOTE_CS2 69
#define NOTE_D2  73
#define NOTE_DS2 78
#define NOTE_E2  82
#define NOTE_F2  87
#define NOTE_FS2 93
#define NOTE_G2  98
#define NOTE_GS2 104
#define NOTE_A2  110
#define NOTE_AS2 117
#define NOTE_B2  123
#define NOTE_C3  131
#define NOTE_CS3 139
#define NOTE_D3  147
#define NOTE_DS3 156
#define NOTE_E3  165
#define NOTE_F3  175
#define NOTE_FS3 185
#define NOTE_G3  196
#define NOTE_GS3 208
#define NOTE_A3  220
#define NOTE_AS3 233
#define NOTE_B3  247
#define NOTE_C4  262
#define NOTE_CS4 277
#define NOTE_D4  294
#define NOTE_DS4 311
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_FS4 370
#define NOTE_G4  392
#define NOTE_GS4 415
#define NOTE_A4  440
#define NOTE_AS4 466
#define NOTE_B4  494
#define NOTE_C5  523
#define NOTE_CS5 554
#define NOTE_D5  587
#define NOTE_DS5 622
#define NOTE_E5  659
#define NOTE_F5  698
#define NOTE_FS5 740
#define NOTE_G5  784
#define NOTE_GS5 831
#define NOTE_A5  880
#define NOTE_AS5 932
#define NOTE_B5  988
#define NOTE_C6  1047
#define NOTE_CS6 1109
#define NOTE_D6  1175
#define NOTE_DS6 1245
#define NOTE_E6  1319
#define NOTE_F6  1397
#define NOTE_FS6 1480
#define NOTE_G6  1568
#define NOTE_GS6 1661
#define NOTE_A6  1760
#define NOTE_AS6 1865
#define NOTE_B6  1976
#define NOTE_C7  2093
#define NOTE_CS7 2217
#define NOTE_D7  2349
#define NOTE_DS7 2489
#define NOTE_E7  2637
#define NOTE_F7  2794
#define NOTE_FS7 2960
#define NOTE_G7  3136
#define NOTE_GS7 3322
#define NOTE_A7  3520
#define NOTE_AS7 3729
#define NOTE_B7  3951
#define NOTE_C8  4186
#define NOTE_CS8 4435
#define NOTE_D8  4699
#define NOTE_DS8 4978

int melody[] = {
  NOTE_AS4, NOTE_AS4, NOTE_AS4, NOTE_AS4,
  NOTE_AS4, NOTE_AS4, NOTE_AS4, NOTE_AS4,
  NOTE_AS4, NOTE_AS4, NOTE_AS4, NOTE_AS4,
  NOTE_AS4, NOTE_AS4, NOTE_AS4, NOTE_AS4,
  NOTE_AS4, NOTE_AS4, NOTE_AS4, NOTE_AS4,
  NOTE_D5, NOTE_D5, NOTE_D5, NOTE_D5,
  NOTE_C5, NOTE_C5, NOTE_C5, NOTE_C5, 
  NOTE_F5, NOTE_F5, NOTE_F5, NOTE_F5, 
  NOTE_G5, NOTE_G5, NOTE_G5, NOTE_G5,
  NOTE_G5, NOTE_G5, NOTE_G5, NOTE_G5, 
  NOTE_G5, NOTE_G5, NOTE_G5, NOTE_G5, 
  NOTE_C5, NOTE_AS4, NOTE_A4, NOTE_F4,
  NOTE_G4, 0, NOTE_G4, NOTE_D5,
  NOTE_C5, 0, NOTE_AS4, 0,
  NOTE_A4, 0, NOTE_A4, NOTE_A4,
  NOTE_C5, 0, NOTE_AS4, NOTE_A4, 
  NOTE_G4,0, NOTE_G4, NOTE_AS5,
  NOTE_A5, NOTE_AS5, NOTE_A5, NOTE_AS5,
  NOTE_G4,0, NOTE_G4, NOTE_AS5,
  NOTE_A5, NOTE_AS5, NOTE_A5, NOTE_AS5,
  NOTE_G4, 0, NOTE_G4, NOTE_D5,
  NOTE_C5, 0, NOTE_AS4, 0,
  NOTE_A4, 0, NOTE_A4, NOTE_A4,
  NOTE_C5, 0, NOTE_AS4, NOTE_A4, 
  NOTE_G4,0, NOTE_G4, NOTE_AS5,
  NOTE_A5, NOTE_AS5, NOTE_A5, NOTE_AS5,
  NOTE_G4,0, NOTE_G4, NOTE_AS5,
  NOTE_A5, NOTE_AS5, NOTE_A5, NOTE_AS5
 };

// note durations: 4 = quarter note, 8 = eighth note, etc.:
int noteDurations[] = {
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  4,4,4,4,
  };

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
  boolean _tare = true; //set this to false if you don't want tare to be performed in the next step
  EEPROM.get(eeAddressCal, calibrationValue);
  LoadCell.setCalFactor(calibrationValue);
  LoadCell.start(stabilizingtime, _tare);

  //servo
  myservo.attach(servoPin);
  myservo.write(pos);
  startMillis = millis();
}

void loop() { //0 IDLE
  //1 READ
  //2 CHECK
  //3 AUTHENTICATION
  //4 DATA
  //5 READ SENSORS


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
      output["association_code"] = 33333;
      output["id"] = "None";
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
    if (input["entrance"] == "True" && entrance == false) {
      openServo();
      entrance = true;
    }
    if (input["entrance"] == "False" && entrance == true) {
      closeServo();
      entrance = false;
    }
    if (input["alarm"] == "True") {
      duration = input["duration"];
      alarm = true;
    }
    if (input["alarm"] == "False") {
      alarm = false;
    }

    if (input["data"] == "True") {
      byte data[40] = {0};
      output["type"] = "D";
      output["id"] = id;
      if (dht11.read2(tempPin, &temp, &hum, data)) {
        output["humidity"] = "error";
        output["temperature"] = "error";
      }
      else {
        output["humidity"] = hum;
        output["temperature"] = temp;
      }
      if (!LoadCell.update()) {
        output["weight"] = "error";
      }
      else {
        output["weight"] = LoadCell.getData();
      }
      serializeJson(output, Serial);
      Serial.println();
    }
    iState = 0;
    in_buffer = "";
  }

  if (alarm) {
    for (int thisNote = 0; thisNote < 112; thisNote++) {

    int noteDuration = 750 / noteDurations[thisNote];
    tone(8, melody[thisNote], noteDuration);

    int pauseBetweenNotes = noteDuration * 1.30;
    delay(pauseBetweenNotes);
    
    noTone(8);
  }
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
