#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Arefe";
const char* password = "arefe1234";
const char* serverName = "http://172.20.10.4:8888/test";

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to ");
  Serial.print(ssid);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("Connected to Wi-Fi!");

  // Send POST request
  sendPostRequest();
}

void loop() {
  // Nothing to do here
}

void sendPostRequest() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
  
    // Your Domain name with URL path or IP address with path
    http.begin(client, serverName);

    http.addHeader("Content-Type", "text/plain"); // Specify content-type

    // Send the request
    String payload = "This is a test message from ESP32";
    int httpResponseCode = http.POST(payload);

    // Check the response
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Response from server:");
      Serial.println(response);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end(); // Free resources
  } else {
    Serial.println("Error in WiFi connection");
  }
}
