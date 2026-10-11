const int laserPin  = 9;
const int buzzerPin = 8;
const int analogPin = A0;

const int numSamples = 550;

// 1000 us -> nominal 1 kHz sampling rate
const unsigned long sampleInterval = 1000;

int samples[numSamples];

void setup() {
  Serial.begin(115200);

  pinMode(laserPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  // Continuous optical beam during acquisition.
  digitalWrite(laserPin, HIGH);

  // Uncomment ONLY for the controlled 125 Hz piezo/buzzer validation test.
  // tone(buzzerPin, 125);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 's' || command == 'S') {
      // Dummy ADC reads to allow the analog input / detector circuit to settle.
      for (int i = 0; i < 50; i++) {
        analogRead(analogPin);
        delay(2);
      }

      captureData();
      dumpData();
    }
  }
}

void captureData() {
  unsigned long nextSampleTime = micros();

  for (int i = 0; i < numSamples; i++) {
    while (micros() - nextSampleTime < sampleInterval) {
      // Wait for the next scheduled sample.
    }

    nextSampleTime += sampleInterval;
    samples[i] = analogRead(analogPin);
  }
}

void dumpData() {
  for (int i = 0; i < numSamples; i++) {
    Serial.println(samples[i]);
  }
}
