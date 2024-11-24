#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>

#define CAMERA_MODEL_AI_THINKER // Define the camera model you're using

#include "camera_pins.h"  // This includes the pin configuration for the AI Thinker model

#define RELAY_PIN 12   // Relay connected to GPIO 12
#define GSM_TX 27
#define GSM_RX 26
#define GPS_TX 34
#define GPS_RX 35

LiquidCrystal_I2C lcd(0x27, 16, 2);  // Set the LCD address to 0x27 for a 16 chars and 2 line display
SoftwareSerial gsmSerial(GSM_RX, GSM_TX);  // For GSM module
SoftwareSerial gpsSerial(GPS_RX, GPS_TX);  // For GPS module
TinyGPSPlus gps;

const char* ssid = "Rugaba";
const char* password = "Rugaba321";
String plateNumber = "RAG 548 H";

void startCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_UXGA;  // High resolution
    config.jpeg_quality = 10;  // Lower is higher quality
    config.fb_count = 2;       // Frame buffers
  } else {
    config.frame_size = FRAMESIZE_SVGA;  // Lower resolution for devices without PSRAM
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Initialize the camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
  Serial.println("Camera initialized successfully");
}
void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // Keep the relay off by default
  
  Serial.begin(115200);
  gsmSerial.begin(9600); // GSM module baud rate
  gpsSerial.begin(9600); // GPS module baud rate
  
  lcd.init();              // Initialize the LCD
  lcd.backlight();         // Turn on the backlight
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("System Ready");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Connecting WiFi");
  }
  Serial.println("Connected to WiFi");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi Connected");
  delay(2000);
}

void loop() {
  // Retrieve the result from Python face recognition system (using HTTP or MQTT)
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("http://192.168.1.210/D:\face_recognition/recognizer.py"); // Replace with your Python server
    int httpCode = http.GET();

    if (httpCode > 0) {
      String response = http.getString();
      
      if (response == "known") {
        // Face recognized, driver valid
        Serial.println("Driver recognized. Starting the car...");
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Driver recognized");
        lcd.setCursor(0, 1);
        lcd.print("Car Starting...");
        digitalWrite(RELAY_PIN, HIGH);  // Activate relay (car starts)
        delay(900000);  // Wait for 15 minutes (900000 ms)
        // After 15 minutes, recheck the face recognition
        recheckFace();
      } else if (response == "unknown") {
        // Face not recognized
        Serial.println("Driver unknown. Car won't start.");
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Unknown Driver");
        lcd.setCursor(0, 1);
        lcd.print("Access Denied");
        digitalWrite(RELAY_PIN, LOW);   // Keep relay off
      }
    }
    http.end();
  }
  
  // Continuously check GPS location
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
    if (gps.location.isUpdated()) {
      Serial.print("Lat: "); Serial.println(gps.location.lat(), 6);
      Serial.print("Lng: "); Serial.println(gps.location.lng(), 6);
    }
  }

  delay(2000);
}

void recheckFace() {
  // After 15 minutes, request new face recognition
  HTTPClient http;
  http.begin("http://192.168.1.210/D:\face_recognition/recognizer.py"); // Replace with your Python server for recheck
  int httpCode = http.GET();
  
  if (httpCode > 0) {
    String response = http.getString();
    
    if (response == "valid") {
      Serial.println("Driver revalidated. Car continues.");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Driver Valid");
      lcd.setCursor(0, 1);
      lcd.print("Car Continues");
    } else {
      Serial.println("Driver invalid after recheck. Sending alert to police...");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Invalid Driver");
      lcd.setCursor(0, 1);
      lcd.print("Sending SMS...");
      sendSMSToPolice();
    }
  }
  http.end();
}

void sendSMSToPolice() {
  String smsMessage = "Alert: Invalid driver detected.\n";
  smsMessage += "Plate: " + plateNumber + "\n";
  smsMessage += "Location: Lat " + String(gps.location.lat(), 6) + ", Lng " + String(gps.location.lng(), 6);

  gsmSerial.println("AT+CMGF=1");    // Configuring TEXT mode
  delay(1000);
  gsmSerial.println("AT+CMGS=\"+250780765548\"");  // Replace with police phone number
  delay(1000);
  gsmSerial.println(smsMessage);    // Message content
  delay(1000);
  gsmSerial.println((char)26);      // End AT command with a ^Z
  delay(1000);
  Serial.println("SMS Sent.");
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SMS Sent");
}
