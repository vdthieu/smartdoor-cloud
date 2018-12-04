///servo pin 
///distance echo pin 4
///distance trig pin 5
#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <WiFiServer.h>
#include <WiFiUdp.h>
#include <Servo.h>
#include <stdlib.h>
#include "SSD1306.h"

WiFiClient espClient;
PubSubClient mqttclient(espClient);
Servo myservo;
SSD1306  display(0x3c, 4, 5);
void onReceiveMQTT(char* _topic, byte* payload, unsigned int length);
void close_door();
void open_door();
const char* ssid     = "UiTiOt-E3.1";
const char* password = "UiTiOtAP";
const char* server = "10.71.2.217";
//
//const char* ssid     = "Hieu-2";
//const char* password = "trunghieu196";
//const char* server = "192.168.100.100";

const char* username = "admin";
const char* pwd = "123QWE!@#";
void connect_wifi();
void reconnect();

const char* TOPIC_CONTROL = "door-control";
const char* TOPIC_STATUS = "door-status";
const char* TOPIC_AUTO = "door-auto";

const char* rfid_topic = "RFID";
const char* door_up_topic = "DOOR_UP";
const char* door_down_topic = "DOOR_DOWN";
const char* req_stat_topic = "REQ_STAT";
const char* res_stat_topic = "RES_STAT";
const char* board_id = "SERVO";
const char* temp_topic = "THOM";

//---------------DISTANCE-------------------------
const int trig = 12;     
const int echo = 13;    
const int servo_pin = 2;
unsigned long duration;
int distance;  
int f;

// runtime variables
unsigned long current_time = 0;
unsigned long track_time = 0;
unsigned long last_open_time = 0;
bool is_connected_mqtt = false;
bool is_door_open = false;
bool is_auto = true;

int open_deg = 183; // servo open degree
int close_deg = 8; // servo close degree
int distance_threshold = 8;

void setup() {
  Serial.begin(115200);
  myservo.attach(servo_pin);
  myservo.write(8);
  connect_wifi();
  pinMode(trig, OUTPUT);  //Initiate  trig
  pinMode(echo, INPUT);  // Initiate  echo
  f = 0;
  mqttclient.setServer(server,1883); // set server info mation
  mqttclient.setCallback(onReceiveMQTT); 
  reconnect();

  display.init();
  display.setFont(ArialMT_Plain_16);
  display.drawString(15, 22, "Device started");
  display.display();
} 
bool a = true,b=true;
void loop(){
  current_time = millis();
  digitalWrite(trig, 0);  
  delayMicroseconds(2);
  digitalWrite(trig, 1);  
  delayMicroseconds(5);   
  digitalWrite(trig, 0);  

  duration = pulseIn(echo, HIGH);
  distance = int(duration / 58.824);
  Serial.println(distance);
  if( is_auto || is_door_open ) {
    if( distance < distance_threshold) {
      open_door();
    } else if(current_time - last_open_time > 5000 ){
      close_door();
    }
  }
  if (current_time - track_time > 5000) {
    reconnect();
    track_time = current_time;
  }
  mqttclient.loop();
}

void connect_wifi(){
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  // kết nối đến mạng Wifi
  WiFi.begin(ssid, password);
  WiFi.mode(WIFI_STA);
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttclient.connected()) {
      is_connected_mqtt = false;
        Serial.print("Attempting MQTT connection...");
        if (mqttclient.connect("door-servo",username,pwd)) {
          mqttclient.publish(res_stat_topic,board_id);
          is_connected_mqtt = true;
          Serial.println("connected");
            mqttclient.subscribe(door_down_topic);
            mqttclient.subscribe(rfid_topic);
            mqttclient.subscribe(req_stat_topic);
            mqttclient.subscribe(temp_topic);
        } else {
          Serial.print("failed, rc=");
          Serial.print(mqttclient.state());
          Serial.println(" try again in 5 seconds");
        }
      }
    }
  else{
    Serial.println("Attempting Wifi connection...");
  }
}
void onReceiveMQTT(char* _topic, byte* payload, unsigned int length)
{
  String msg = "";
  String topic = String(_topic);
  for (int i = 0; i < length; i++) {
    msg = msg + (char)payload[i];
  }
  Serial.println("mqtt ["+topic + "]:" + msg);
  if (topic == door_down_topic) {
    if (msg == "close") {
      close_door();
    } else if (msg == "open") {
      open_door();
    }
  }  
  if (topic == rfid_topic) {
    if(msg == "on"){
      is_auto = false;
    }
    if(msg == "off"){
      is_auto = true;
    }
  }
  if(topic.equals(req_stat_topic)){
    mqttclient.publish(res_stat_topic,board_id);
  }
  if(topic.equals(temp_topic)){
    display.clear();
    display.drawString(17,0,"Temperature");
    display.drawString(53,16, msg);
    display.display();
  }
}
void close_door(){
  if(!is_door_open) {
    return;
  }
  is_door_open = false;
  myservo.write(close_deg);
  Serial.println("close");
  mqttclient.publish(door_up_topic,"close");
  a=true;
}
  
void open_door() {
  if(is_door_open) {
    return;
  }
  last_open_time = current_time;
  is_door_open = true;
  myservo.write(open_deg);
  Serial.println("open"); 
  mqttclient.publish(door_up_topic,"open");
  b=true;
}    
