int redPin= 14;
int greenPin = 12;
int bluePin = 13;
void setup() {
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
}
int counter = 0;
void loop() {
  counter = (counter + 1 % 11);
  setColor(counter * 25, counter * 25, counter * 25); // Red Color
  delay(1000);
}
void setColor(int redValue, int greenValue, int blueValue) {
  analogWrite(redPin, redValue);
  analogWrite(greenPin, greenValue);
  analogWrite(bluePin, blueValue);
}
