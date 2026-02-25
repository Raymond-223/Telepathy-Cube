#include <Servo.h>

Servo panServo;
Servo tiltServo;
Servo breathServo;

const int PAN_PIN = 9;
const int TILT_PIN = 10;
const int BREATH_PIN = 11;
const int LASER_PIN = 6;

String lineBuffer = "";

float clampf(float value, float minV, float maxV) {
  if (value < minV) return minV;
  if (value > maxV) return maxV;
  return value;
}

int toServoAngle(float value, float inMin, float inMax) {
  float ratio = (value - inMin) / (inMax - inMin);
  ratio = clampf(ratio, 0.0, 1.0);
  return (int)(ratio * 180.0);
}

void handleMode(String value) {
  value.trim();
  if (value == "ambient") {
    digitalWrite(LASER_PIN, LOW);
  }
}

void handleGimbal(float pan, float tilt) {
  pan = clampf(pan, -90.0, 90.0);
  tilt = clampf(tilt, -45.0, 45.0);
  panServo.write(toServoAngle(pan, -90.0, 90.0));
  tiltServo.write(toServoAngle(tilt, -45.0, 45.0));
}

void handleBreath(float angle) {
  angle = clampf(angle, 0.0, 180.0);
  breathServo.write((int)angle);
}

void handleLaser(int state) {
  digitalWrite(LASER_PIN, state > 0 ? HIGH : LOW);
}

void processLine(String line) {
  line.trim();
  if (line.length() == 0) return;

  int firstComma = line.indexOf(',');
  if (firstComma < 0) return;

  String cmd = line.substring(0, firstComma);
  String payload = line.substring(firstComma + 1);

  if (cmd == "MODE") {
    handleMode(payload);
    return;
  }

  if (cmd == "GIMBAL") {
    int comma2 = payload.indexOf(',');
    if (comma2 < 0) return;
    float pan = payload.substring(0, comma2).toFloat();
    float tilt = payload.substring(comma2 + 1).toFloat();
    handleGimbal(pan, tilt);
    return;
  }

  if (cmd == "BREATH") {
    int comma2 = payload.indexOf(',');
    String angleText = comma2 > 0 ? payload.substring(0, comma2) : payload;
    float angle = angleText.toFloat();
    handleBreath(angle);
    return;
  }

  if (cmd == "LASER") {
    handleLaser(payload.toInt());
    return;
  }
}

void setup() {
  Serial.begin(115200);
  panServo.attach(PAN_PIN);
  tiltServo.attach(TILT_PIN);
  breathServo.attach(BREATH_PIN);
  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);
  handleGimbal(0.0, 0.0);
  handleBreath(30.0);
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      processLine(lineBuffer);
      lineBuffer = "";
    } else if (c != '\r') {
      lineBuffer += c;
    }
  }
}

