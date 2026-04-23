#include <Servo.h>

// --- Pin Definitions ---
const int TRIG_PIN  = 5;
const int ECHO_PIN  = 8; // Moved from D6 to D8 to rule out faulty pin
const int SERVO_PIN = 7;

// --- Constants ---
const int STEP_SIZE = 5;
const int MIN_ANGLE = 0;
const int MAX_ANGLE = 180;
const int NUM_READINGS = 3;

Servo scanServo;

// --- State Variables ---
int currentAngle = 0;
int stepDirection = 1;
int readings[NUM_READINGS];
int readingIdx = 0;

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT); // Heartbeat LED
  
  scanServo.attach(SERVO_PIN);
  scanServo.write(90); // Start at center
  
  for (int i = 0; i < NUM_READINGS; i++) readings[i] = 0;
  delay(1000);
}

void loop() {
  scanServo.write(currentAngle);
  delay(120); // Slightly longer for servo stability
  
  // --- Median Filter (Take 5 readings, pick the middle) ---
  int filterBuffer[5];
  for(int i=0; i<5; i++) {
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duration = pulseIn(ECHO_PIN, HIGH, 30000);
    filterBuffer[i] = (duration == 0) ? 400 : (int)(duration * 0.034 / 2);
    delay(10);
  }
  
  // Simple Sort for Median
  for(int i=0; i<4; i++) {
    for(int j=i+1; j<5; j++) {
      if(filterBuffer[i] > filterBuffer[j]) {
        int temp = filterBuffer[i];
        filterBuffer[i] = filterBuffer[j];
        filterBuffer[j] = temp;
      }
    }
  }
  int medianDist = filterBuffer[2];

  // Output
  Serial.print(currentAngle);
  Serial.print(",");
  Serial.println(medianDist);
  
  // Update Angle
  currentAngle += (STEP_SIZE * stepDirection);
  if (currentAngle >= MAX_ANGLE) { currentAngle = MAX_ANGLE; stepDirection = -1; }
  else if (currentAngle <= MIN_ANGLE) { currentAngle = MIN_ANGLE; stepDirection = 1; }
  
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
}

// takeReading removed for simplicity

