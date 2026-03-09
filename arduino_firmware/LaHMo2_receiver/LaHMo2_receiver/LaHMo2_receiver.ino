// ESP32-S3 central receiver for LaHMo2 using ArduinoBLE
// - Scans & connects (by name or service UUID)
// - Subscribes to notify characteristic
// - Writes incoming CSV lines to Serial

#include <Arduino.h>
#include <ArduinoBLE.h>

// ======= FILL THESE FROM lahmo2.h (or print them from the peripheral) =======
static const char* TARGET_NAME          = "SpectraDerma";  // DEVICE_NAME in your LaHMo2 code (optional but handy)
static const char* LHM_SERVICE_UUID     = "0000ACEF-0000-1000-8000-00805F9B34FB"; // LHM_SERVICE_UUID
static const char* LHM_CHAR_UUID        = "0000FF01-0000-1000-8000-00805F9B34FB"; // LHM_CHAR_UUID
// ============================================================================
static const unsigned long SCAN_MS        = 6000;
static const unsigned long RECONNECT_MS   = 1500;

BLEDevice        peripheral;
BLEService       lhmService;
BLECharacteristic lhmChar;

bool connectToTarget();
bool discoverLahmo2();

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  if (!BLE.begin()) {
    Serial.println("[ERR] BLE init failed.");
    while (1) delay(1000);
  }
  Serial.println("[OK ] BLE started.");

  // Try to connect (loop until we do)
  while (!connectToTarget()) {
    Serial.println("[.. ] Re-scan in a moment...");
    delay(RECONNECT_MS);
  }

  Serial.println("[OK ] Connected. Discovering attributes...");
  if (!discoverLahmo2()) {
    Serial.println("[ERR] Discovery failed. Disconnecting and retrying...");
    peripheral.disconnect();
  } else {
    Serial.println("[OK ] Subscribed. Streaming CSV to Serial...");
  }
}

void loop() {
  BLE.poll();

  // Auto-reconnect if dropped
  if (peripheral && !peripheral.connected()) {
    Serial.println("[WARN] Disconnected. Reconnecting...");
    delay(RECONNECT_MS);
    while (!connectToTarget()) {
      delay(RECONNECT_MS);
    }
    if (!discoverLahmo2()) {
      Serial.println("[ERR] Discovery failed after reconnect.");
    } else {
      Serial.println("[OK ] Re-subscribed.");
    }
  }

  // Print notifications
  if (peripheral && peripheral.connected() && lhmChar) {
    if (lhmChar.valueUpdated()) {
      int len = lhmChar.valueLength();
      if (len > 0) {
        static char buf[512];
        len = min(len, (int)sizeof(buf) - 1);
        int n = lhmChar.readValue((uint8_t*)buf, len);
        if (n > 0) {
          buf[n] = '\0';
          Serial.println(buf);  // already CSV from peripheral
        }
      }
    }
  }
}

// ===== Helpers =====

bool connectToTarget() {
  // Prefer scanning by UUID when provided; fallback to generic scan
  if (LHM_SERVICE_UUID && strlen(LHM_SERVICE_UUID) > 0) {
    BLE.scanForUuid(LHM_SERVICE_UUID);  // supported in ArduinoBLE 1.4.x
  } else {
    BLE.scan();                         // generic scan
  }

  unsigned long t0 = millis();

  while (millis() - t0 < SCAN_MS) {
    BLEDevice dev = BLE.available();
    if (!dev) {
      BLE.poll();
      continue;
    }

    bool ok = false;

    // If you provided a name, match it (helps avoid the hasAdvertisedServiceUuid(const char*) overload issue)
    if (TARGET_NAME && strlen(TARGET_NAME) > 0) {
      if (dev.hasLocalName() && dev.localName() == TARGET_NAME) ok = true;
    }

    // If we scanned by UUID, anything we get here should have advertised the UUID already.
    if (!ok && (LHM_SERVICE_UUID && strlen(LHM_SERVICE_UUID) > 0)) {
      ok = true; // scanForUuid filtered it for us
    }

    if (ok) {
      Serial.print("[OK ] Found target ");
      if (dev.hasLocalName()) Serial.print(dev.localName());
      else Serial.print(dev.address());
      Serial.println(". Connecting...");

      BLE.stopScan();
      if (dev.connect()) {
        peripheral = dev;  // store handle
        Serial.println("[OK ] Connected.");
        return true;
      } else {
        Serial.println("[ERR] Connect failed. Rescanning.");
        if (LHM_SERVICE_UUID && strlen(LHM_SERVICE_UUID) > 0) BLE.scanForUuid(LHM_SERVICE_UUID);
        else BLE.scan();
      }
    }
  }

  BLE.stopScan();
  return false;
}

bool discoverLahmo2() {
  if (!peripheral || !peripheral.connected()) return false;

  if (!peripheral.discoverAttributes()) {
    Serial.println("[ERR] discoverAttributes() failed.");
    return false;
  }

  lhmService = peripheral.service(LHM_SERVICE_UUID);
  if (!lhmService) {
    Serial.println("[ERR] Service not found. Check LHM_SERVICE_UUID.");
    return false;
  }

  lhmChar = lhmService.characteristic(LHM_CHAR_UUID);
  if (!lhmChar) {
    Serial.println("[ERR] Characteristic not found. Check LHM_CHAR_UUID.");
    return false;
  }

  if (!lhmChar.canSubscribe()) {
    Serial.println("[ERR] Characteristic is not notifiable.");
    return false;
  }

  if (!lhmChar.subscribe()) {
    Serial.println("[ERR] subscribe() failed.");
    return false;
  }

  // No zero-arg readValue() in ArduinoBLE; we’re done.
  return true;
}