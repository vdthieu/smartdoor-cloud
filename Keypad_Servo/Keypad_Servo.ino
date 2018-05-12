#include <Servo.h>
#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <WiFiClientSecure.h>
#include <WiFiServer.h>
#include <WiFiUdp.h>
#include <Keypad.h> //thư viện Keypad

const byte n_rows = 4; //số hàng
const byte n_cols = 4; //số cột
//định nghĩa các trá trị trả về
char keys[n_rows][n_cols] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
//Cách kết nối chân với esp8266
byte colPins[n_rows] = {D3, D2, D1, D0};
byte rowPins[n_cols] = {D7, D6, D5, D4};

//const char* ssid = "UiTiOt-E3.1"; //"CRG Gaming F1";
//const char* password = "UiTiOtAP#"; //"crggaming@79";
const char* ssid = "UiTiOt-E3.1"; //"CRG Gaming F1";
const char* password = "UiTiOtAP#"; //"crggaming@79";
const char* mqtt_server = "10.71.2.217";

String offline_pwd = "1996";
String input = "";
String STATE = "CLOSE";

//thiết lập đối tượng Keypad
Keypad myKeypad = Keypad( makeKeymap(keys), rowPins, colPins, n_rows, n_cols);
Servo myservo;
WiFiClient espClient;
PubSubClient client(espClient);

//function variables 
bool is_connected_mqtt = false;
bool is_door_open = false;
unsigned long track_time = 0;
unsigned long last_open = 0;
unsigned long current_time = 0;
String CharToString(char * data);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  // kết nối đến mạng Wifi
  WiFi.begin(ssid, password);
  WiFi.mode(WIFI_STA);
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

void callback(char* _topic, byte* payload, int length) {
  String msg = "";
  String topic = String(_topic);
  for(int i=0;i<length;i++){
    msg = msg + (char)payload[i];
  }
  if(topic == "door-control"){
    if(msg == "close"){
      is_door_open = false;
      myservo.write(0);
      client.publish("door-status","close",true);
    }else{
      is_door_open = true;
      myservo.write(150);
      last_open = current_time;
      client.publish("door-status","open",true);
    }
  }
}

void reconnect() {
  if (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("hai-esp8266")) {
      is_connected_mqtt = true;
      Serial.println("connected");
      // publish gói tin "Connected!" đến topic ESP8266/connection/board
      client.publish("TEST_MQTT", "Connected!");
      // đăng kí nhận gói tin tại topic ESP8266/LED_GPIO16/status
      client.subscribe("door-control");
    } else {
      // in ra màn hình trạng thái của client khi không kết nối được với MQTT broker
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
    }
  }
}

void setup() {
  myservo.attach(15);
  myservo.write(0);
  Serial.begin(9600);
  // hàm thực hiện chức năng kết nối Wifi và in ra địa chỉ IP của ESP8266
  setup_wifi();
  // cài đặt server là broker.mqtt-dashboard.com và lắng nghe client ở port 1883
  client.setServer(mqtt_server, 1883);
  // gọi hàm callback để thực hiện các chức năng publish/subcribe
  client.setCallback(callback);
  // gọi hàm reconnect() để thực hiện kết nối lại với server khi bị mất kết nối
  reconnect();
}

void loop() {
  char myKey = myKeypad.getKey();
  current_time = millis();
  if (current_time - last_open >5000){
    myservo.write(0);
    is_door_open = false;
  }

  switch (myKey){
    case NULL:
      break;
    case 'A':
      if(is_connected_mqtt){
        byte bytes[5];
        input.getBytes(bytes,5);
        client.publish("door-password", bytes, 5);
      }
      else if (input == offline_pwd) {
        if (is_door_open) {
          myservo.write(0);
          is_door_open = false;
        }
        else {
         myservo.write(150);
         is_door_open = true;
         last_open = current_time;
        }
      }
      input="";
      break;
    default :
      Serial.print("Current Buffer: ");
      Serial.println(myKey);
      input = input + myKey;
      Serial.println(input);   
  }
  // kiểm tra nếu ESP8266 chưa kết nối được thì sẽ thực hiện kết nối lại
  if (current_time - track_time >5000){
      reconnect();
      track_time = current_time;
  }
  // if millis overflow
  if( current_time < track_time){
    track_time = current_time;
  }
  client.loop();
}
