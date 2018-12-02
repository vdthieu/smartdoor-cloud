#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <WiFiServer.h>
#include <WiFiUdp.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

WiFiClient espClient;
PubSubClient mqttclient(espClient);
//-------------------------------------------------
//const char* ssid = "UiTiOt-E3.1";
//const char* password = "UiTiOtAP";
//const char* mqtt_server = "10.71.2.217";
const char* ssid = "Hieu-2";
const char* password = "trunghieu196";
const char* mqtt_server = "192.168.100.100";
//---------------RFID-----------------------------

#define SS_PIN 15
#define RST_PIN 2
MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance.

const char* username = "admin";
const char* pwd = "123QWE!@#";

void onReceiveMQTT(char* _topic, byte* payload, unsigned int length);

const char* req_stat_topic = "REQ_STAT";
const char* res_stat_topic = "RES_STAT";
const char* board_id = "RFID";
const char* uuid_topic = "UUID";

void setup() 
{
  Serial.begin(115200);   // Initiate a serial communication
  setup_wifi(); 
  
  mqttclient.setServer(mqtt_server, 1883);
  mqttclient.setCallback(onReceiveMQTT); 
  SPI.begin();      // Initiate  SPI bus
  mfrc522.PCD_Init();   // Initiate MFRC522
  Serial.println("Approximate your card to the reader...");
  reconnect();
  
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  // kết nối đến mạng Wifi
  WiFi.begin(ssid, password);
  // in ra dấu . nếu chưa kết nối được đến mạng Wifi
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // in ra thông báo đã kết nối và địa chỉ IP của ESP8266
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // lặp cho đến khi được kết nối trở lại
  while (!mqttclient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttclient.connect("smartdoor-rfid",username,pwd)) {
      Serial.println("connected");
      mqttclient.publish(res_stat_topic,board_id);
      mqttclient.subscribe(req_stat_topic);
    } else {
      // in ra màn hình trạng thái của client khi không kết nối được với MQTT broker
      Serial.print(mqttclient.state());
      Serial.println(" try again in 5 seconds");
      // delay 5s trước khi thử lại
      delay(5000);
    }
  }
}

void loop() 
{ 
  mqttclient.loop();
  // Look for new cards
  if ( ! mfrc522.PICC_IsNewCardPresent()) 
  {
    return;
  }
  // Select one of the cards
  if ( ! mfrc522.PICC_ReadCardSerial()) 
  {
    return;
  }
  //Show UID on serial monitor
  
  for (byte i = 0; i < mfrc522.uid.size; i++) 
  {
     Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
     Serial.print(mfrc522.uid.uidByte[i], HEX);
  }
  mqttclient.publish(uuid_topic,(char*) mfrc522.uid.uidByte);
  if (!mqttclient.connected()) {
    reconnect();
  }
  delay(3000);
} 

void onReceiveMQTT(char* _topic, byte* payload, unsigned int length)
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
  if(topic.equals(req_stat_topic)){
    mqttclient.publish(res_stat_topic,board_id);
  }
}
