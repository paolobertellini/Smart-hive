#include <EEPROM.h> //EEPROM

char id[6]="none";
void setup() {
  // put your setup code here, to run once:
          EEPROM.put(0, id);


}

void loop() {
  
  // put your main code here, to run repeatedly:

}
