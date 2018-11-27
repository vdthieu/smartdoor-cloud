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
SSD1306  display(0x3c, 0, 16);

const char* ssid     = "UiTiOt-E3.1";
const char* password = "UiTiOtAP";
const char* server = "10.71.2.217";
const char* username = "admin";
const char* pwd = "123QWE!@#";
void connect_wifi();
void reconnect();

const char* TOPIC_CONTROL = "door-control";
const char* TOPIC_STATUS = "door-status";
const char* TOPIC_AUTO = "door-auto";
const char* TOPIC_ANNOUNCE = "door-announce"; 

const char* TOPIC_SET_DISTANCE = "door-set-distance";
const char* TOPIC_SET_CLOSE = "door-set-close";
const char* TOPIC_SET_OPEN = "door-set-open";

const char* req_stat_topic = "REQ_STAT";
const char* res_stat_topic = "RES_STAT";
const char* board_id = "SERVO";
const char* temp_topic = "THOM";

//---------------DISTANCE-------------------------
const int trig = 4;     
const int echo = 5;    
unsigned long duration;
int distance;  
int f;

// runtime variables
unsigned long current_time = 0;
unsigned long track_time = 0;
unsigned long last_open_time = 0;
bool is_connected_mqtt = false;
bool is_door_open = false;
bool is_auto = false;

int open_deg = 183;
int close_deg = 8;
int distance_threshold = 8;

void setup() {
  Serial.begin(115200);
  myservo.attach(10);
  myservo.write(8);
  connect_wifi();
  pinMode(trig, OUTPUT);  //Initiate  trig
  pinMode(echo, INPUT);  // Initiate  echo
  f = 0;
  mqttclient.setServer(server,1883); // set server info mation
  mqttclient.setCallback(callback); 
  reconnect();

  display.init();
  display.setFont(ArialMT_Plain_16);
  display.drawString(15, 22, "Device started");
  display.display();
} 
void loop()
{
  current_time = millis();
  if( is_auto || is_door_open ) {
    digitalWrite(trig, 0);  
    delayMicroseconds(2);
    digitalWrite(trig, 1);  
    delayMicroseconds(5);   
    digitalWrite(trig, 0);  
  
    duration = pulseIn(echo, HIGH);
    distance = int(duration / 58.824);
    Serial.print(distance);
    if( distance < distance_threshold) {
      open_door();
    }
    if(current_time - last_open_time > 5000 ){
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
          mqttclient.publish("door-identify","servo");
          is_connected_mqtt = true;
          Serial.println("connected");
            mqttclient.subscribe(TOPIC_ANNOUNCE); 
            mqttclient.subscribe(TOPIC_CONTROL); 
            mqttclient.subscribe(TOPIC_CONTROL);
            mqttclient.subscribe(TOPIC_AUTO);
            mqttclient.subscribe(TOPIC_SET_DISTANCE);
            mqttclient.subscribe(TOPIC_SET_CLOSE);
            mqttclient.subscribe(TOPIC_SET_OPEN);
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
void close_door(){
  if(!is_door_open) {
    Serial.print("IS CLOSING");
    return;
  }
  is_door_open = false;
  mqttclient.publish(TOPIC_STATUS,"close"); 
  myservo.write(close_deg);
  Serial.println("close");
}
  
void open_door() {
  if(is_door_open) {
    Serial.print("IS OPENING");
    return;
  }
  last_open_time = current_time;
  is_door_open = true;
  myservo.write(open_deg);
  mqttclient.publish(TOPIC_STATUS,"open");
  Serial.println("open"); 
}    
void callback(char* _topic, byte* payload, unsigned int length)
{
  String msg = "";
  String topic = String(_topic);
  Serial.println(topic);
  for (int i = 0; i < length; i++) {
    msg = msg + (char)payload[i];
  }
  Serial.print("topic:");
  Serial.println(topic);
  Serial.print("message:");
  Serial.println(msg);
  if (topic == TOPIC_CONTROL) {
    if (msg == "close") {
      close_door();
    } else if (msg == "open") {
      open_door();
    }
  }  
  else if (topic == TOPIC_AUTO) {
    if(msg == "on"){
      is_auto = true;
    }else{
      is_auto = false;
    }
  }
  //thay đổi độ quay offline20
  else if (topic == TOPIC_SET_DISTANCE) {
    distance_threshold = msg.toInt();
  }
  else if (topic == TOPIC_SET_CLOSE) {
    close_deg = msg.toInt();
  }
  else if (topic == TOPIC_SET_OPEN) {
    open_deg = msg.toInt();
  }
  else if (topic == TOPIC_ANNOUNCE) {
    mqttclient.publish("door-identify", "servo");
  }else if(topic.equals(req_stat_topic)){
    mqttclient.publish(res_stat_topic,board_id);
  }else if(topic.equals(temp_topic)){
    display.clear();
    display.drawString(17,0,"Temperature");
    display.drawString(53,16, msg);
    display.display();
  }
}
