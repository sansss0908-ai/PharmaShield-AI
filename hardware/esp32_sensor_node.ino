#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <TinyGPSPlus.h>
#include <HardwareSerial.h>
#include <DHT.h>

// ---------- WiFi credentials ----------
const char* WIFI_SSID = "krishana4G";
const char* WIFI_PASSWORD = "9119023841";

// ---------- Backend endpoint ----------
const char* SERVER_URL = "http://192.168.29.144:5001/api/live-reading";

// ---------- DS18B20 setup ----------
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);

// ---------- GPS setup ----------
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// ---------- DHT22 setup ----------
#define DHT_PIN 26
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// ---------- Timing ----------
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL_MS = 5000;  // 5 seconds

// Track last known GPS fix (GPS doesn't update every cycle)
double lastLat = 0.0;
double lastLon = 0.0;
bool hasGpsFix = false;

void setup() {
  Serial.begin(115200);

  tempSensor.begin();
  gpsSerial.begin(9600, SERIAL_8N1, 16, 17);
  dht.begin();

  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Continuously feed GPS parser
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  if (gps.location.isUpdated()) {
    lastLat = gps.location.lat();
    lastLon = gps.location.lng();
    hasGpsFix = true;
  }

  // Send a reading every SEND_INTERVAL_MS
  if (millis() - lastSendTime >= SEND_INTERVAL_MS) {
    lastSendTime = millis();

    tempSensor.requestTemperatures();
    float temperature = tempSensor.getTempCByIndex(0);

    float humidity = dht.readHumidity();
    if (isnan(humidity)) {
      Serial.println("DHT22 read error - using last known value.");
      humidity = 50.0;  // fallback if a read fails
      }

    if (temperature == DEVICE_DISCONNECTED_C) {
      Serial.println("Temperature sensor error - skipping this reading.");
      return;
    }

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(SERVER_URL);
      http.addHeader("Content-Type", "application/json");

      StaticJsonDocument<200> doc;
      doc["temperature"] = temperature;
      doc["humidity"] = humidity;
      doc["lat"] = hasGpsFix ? lastLat : 0.0;
      doc["lon"] = hasGpsFix ? lastLon : 0.0;

      String requestBody;
      serializeJson(doc, requestBody);

      int httpResponseCode = http.POST(requestBody);

      Serial.print("Sent: ");
      Serial.println(requestBody);
      Serial.print("Response code: ");
      Serial.println(httpResponseCode);

      http.end();
    } else {
      Serial.println("WiFi disconnected - skipping send.");
    }
  }
}