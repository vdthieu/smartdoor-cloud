#include <ESP8266WiFi.h>
#include<PubSubClient.h>
#include <WiFiClient.h>
#include <WiFiServer.h>
#include <WiFiClientSecure.h>
#include "FS.h"

// CONNECTION INFO                            
//const char* mqtt_server=IP_MQTT;          
//const char* ssid = SSID;
//const char* password = WPA_KEY;

//const char* mqtt_server="10.71.2.217";
//const char* ssid = "UIT-GUEST";
//const char* password = "Uit05012017";

const char* mqtt_server="192.168.100.111";
const char* ssid = "Hieu-2";
const char* password = "trunghieu196";

// PIN
const int led_bath = 5;
const int led_bed1 = 4;
const int led_bed2 = 14;
const int led_kitchen = 12;
const int led_living =  13;
const int led_r = 1;
const int led_g = 10;
const int led_b = 3;

void onReceiveMQTT(char* topic,byte* payload,unsigned int lengthPayload);
void setColor(int value);
WiFiClientSecure espClient;                                                
PubSubClient client(mqtt_server,8883,onReceiveMQTT,espClient);   

const char* req_stat_topic = "REQ_STAT";
const char* res_stat_topic = "RES_STAT";
const char* led_control_topic = "LED_CONTROL";
const char* board_id = "LIGHT";
const char* rgb_topic = "TOFF";

int rgb_color = 0;

//SETUP()
void setup() {
  // Set pinMode 
  pinMode(led_bath,OUTPUT);                                               
  pinMode(led_bed1,OUTPUT);    
  pinMode(led_bed2,OUTPUT);    
  pinMode(led_kitchen,OUTPUT);    
  pinMode(led_living,OUTPUT);    
  pinMode(led_r,OUTPUT);    
  pinMode(led_g,OUTPUT);    
  pinMode(led_b,OUTPUT);    

  //Set Baurate
  Serial.begin(115200);                                                   //Baurate 115200 

  //Setup wifi
  setup_wifi();
  //Setup SSL

  if (!SPIFFS.begin()) {
    Serial.println("Failed to mount file system");
    return;
  }
  File ca = SPIFFS.open("/hivemq-server-cert.pem", "r"); //replace ca.crt eith your uploaded file name
  if (!ca) {
    Serial.println("Failed to open ca file");
  }
  else
    Serial.println("Success to open ca file");
  if(espClient.loadCertificate(ca))
    Serial.println("loaded");
  else
    Serial.println("not loaded");
  // cài đặt server và lắng nghe client ở port 8883
  client.setServer(mqtt_server, 8883);
  client.setCallback(onReceiveMQTT);                                           //Setup callback funtion of client  

  //Subcribe Topic from MQTT Server
  listenMQTT();     
  //Subcribe Topic from MQTT Server
}

//LOOP()
void loop() {
  setColor(rgb_color);
  if(!client.connected()){       
     listenMQTT();
  }
  else{
    client.loop();
  }    
//  delay(500);
}

//SETUP WIFI
void setup_wifi(){
  Serial.println();
  Serial.print("Connecting to ");                                         //Print Serial monitoring
  Serial.println(ssid);
   
  //Connect to Wifi
  WiFi.begin(ssid,password);                                              //Connect to Wifi

  //Check if connect fail
  while(WiFi.status()!=WL_CONNECTED){                                     //Check if connect fail
    delay(100);
    Serial.println("Can't connect. Reconnecting...\n");
  }
  //If connect success
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());                                         //Show Local IP   
}
//RECEIVE MQTT MESSAGE
void onReceiveMQTT(char* _topic,byte* payload,unsigned int lengthPayload){
  const String topic = String(_topic);
  Serial.print("Receive topic : [");
  Serial.print(topic);
  Serial.println("]");

  //Print Length of payload  
  Serial.print("Length of payload : ");
  Serial.println(lengthPayload);  

  if(topic.equals(req_stat_topic)){
    client.publish(res_stat_topic,board_id);
  }
  if(topic.equals(led_control_topic)){
    char* charMESSAGE = handlePayload(payload,lengthPayload);  
    if(lengthPayload > 0){
      Serial.print("MESSAGE RECEIVED IS : ");
      Serial.println(charMESSAGE);
      switch(*charMESSAGE){
        case 'L' : 
          digitalWrite(led_living,HIGH);
          client.publish("ledState","Light's living room has been turned on");
          break;
        case 'l' : 
          digitalWrite(led_living,LOW);
          client.publish("ledState","Light's living room has been turned off");
          break;
        case 'B' : 
          digitalWrite(led_bed1,HIGH);
          client.publish("ledState","Light's bed room 1 has been turned on");
          break;
        case 'b' : 
          digitalWrite(led_bed1,LOW);
          client.publish("ledState","Light's bed room 1 has been turned off");
          break;
        case 'S' : 
          digitalWrite(led_bed2,HIGH);
          client.publish("ledState","Light's bed room 2 has been turned on");
          break;
        case 's' : 
          digitalWrite(led_bed2,LOW);
          client.publish("ledState","Light's bed room 2 has been turned off");
          break;
        case 'K' : 
          digitalWrite(led_kitchen,HIGH);
          client.publish("ledState","Light's kitchen has been turned on");
          break;
        case 'k' : 
          digitalWrite(led_kitchen,LOW);
          client.publish("ledState","Light's kitchen has been turned off");
          break;
        case 'H' : 
          digitalWrite(led_bath,HIGH);
          client.publish("ledState","Light's bathroom has been turned on");
          break;
        case 'h' : 
          digitalWrite(led_bath,LOW);
          client.publish("ledState","Light's bathroom has been turned off");
          break;      
        case 'A' : 
          All_led('A');
          client.publish("ledState","Light's all room has been turned on");
          break;
        case 'a' : 
          All_led('a');
          client.publish("ledState","Light's all room has been turned off");
          break; 
      }
    }
    else{
      Serial.print("Fail to receive payload !!! - payload : ");
      Serial.println(charMESSAGE);    
    };
  }

  if(topic.equals(rgb_topic)){
    //char *_message = handlePayload(payload,lengthPayload);
    String message = payloadToString(payload,lengthPayload);  
    rgb_color = message.toInt();
  }  
}
//ALL ON or OFF
void All_led(char c){
  if(c == 'A'){
    digitalWrite(led_living,HIGH);
    digitalWrite(led_bed1,HIGH);
    digitalWrite(led_bed2,HIGH);
    digitalWrite(led_kitchen,HIGH);
    digitalWrite(led_bath,HIGH);
  }
  else{
    digitalWrite(led_living,LOW);
    digitalWrite(led_bed1,LOW);
    digitalWrite(led_bed2,LOW);
    digitalWrite(led_kitchen,LOW);
    digitalWrite(led_bath,LOW);
  }
}

//HANDLEPAYLOAD()
char* handlePayload(byte* payload,unsigned int lengthPayload ){
  char* charMESSAGE = new char[lengthPayload];  
  for(int i=0;i<lengthPayload;i++){                                       //Read values from payload
      Serial.print("Value received : ");
      Serial.println(payload[i]);                                         //Print ASCII 
      charMESSAGE[i] = (char)payload[i];                                          
    }
  return charMESSAGE;
}

String payloadToString(byte* payload, unsigned int _length){
  String s= "";
  for (int i=0;i < _length;i++){
    s += (char)payload[i];
  }
  return s;
}

//LISTENMQTT()
void listenMQTT(){
  while(WiFi.status()!=WL_CONNECTED){
    Serial.print("Can't connect. Reconnecting...\n");
    setup_wifi();                                                             
  }
  while(!client.connected()){
    if(client.connect("LEDCONTROL","admin","123QWE!@#")){
      Serial.println("Connected to MQTT Server"); 
      client.subscribe("LED_CONTROL");
      client.subscribe(req_stat_topic);
      client.subscribe(rgb_topic );
      client.publish(res_stat_topic, board_id); 
   }
    else{
      Serial.print("Failed,Can't connect to MQTT Server , STATE = ");
      Serial.println(client.state());
      delay(100);
    }
  } 
}
//write color
void setColor(int value) {
  analogWrite(led_r, value);
  analogWrite(led_g, value);
  analogWrite(led_b, value);
}
