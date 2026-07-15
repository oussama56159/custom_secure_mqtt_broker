# NORA-W366 AT Command Cheat Sheet
**Firmware:** u-connectXpress v1.0.0-011

---

# 1. Test Communication

Check if the module is responding.

```text
AT
```

Response:

```text
OK
```

---

# 2. Module Information

Manufacturer

```text
AT+GMI
```

Model

```text
AT+GMM
```

Firmware Version

```text
AT+CGMR
```

Serial Number

```text
AT+CGSN
```

---

# 3. Echo

Disable echo

```text
ATE0
```

Enable echo

```text
ATE1
```

---

# 4. Error Handling

Enable detailed errors

```text
AT+USYEE=1
```

Read last error

```text
AT+USYEC?
```

Common Errors

| Code | Meaning |
|------|---------|
|0|No Error|
|5|Invalid Parameter|
|32|Unknown Command|
|34|Invalid Syntax|
|35|Operation Not Supported|

---

# 5. Restart Module

```text
AT+CPWROFF
```

The module will reboot and print:

```text
+STARTUP
```

---

# 6. Wi-Fi Scan

Active Scan

```text
AT+UWSSC=0
```

Passive Scan

```text
AT+UWSSC=1
```

Example

```text
+UWSSC:2887BA7C3C7F,"OfficeWiFi",7,-42,18,8,8
+UWSSC:6014665B68FB,"Guest",1,-60,18,8,8
OK
```

Fields

```
BSSID
SSID
Channel
RSSI
...
```

---

# 7. Wi-Fi Events

Connected

```text
+UEWLU
```

Disconnected

```text
+UEWLD
```

Network Down

```text
+UEWSND
```

---

# 8. Save Settings

```text
AT&W
```

---

# 9. Factory Reset

```text
AT+USYFR
```

---

# 10. TCP Socket

Create TCP Socket

```text
AT+USOCR=6
```

Connect

```text
AT+USOCO=<socket>,"192.168.1.100",80
```

Send Data

```text
AT+USOWS=<socket>,"Hello"
```

Receive Data

```text
AT+USORF=<socket>,100
```

Close Socket

```text
AT+USOCL=<socket>
```

---

# 11. UDP

Create Socket

```text
AT+USOCR=17
```

Send Packet

```text
AT+USOST=<socket>,"192.168.1.50",5000,"Hello"
```

Receive

```text
AT+USORF=<socket>,100
```

---

# 12. MQTT (Basic)

Connect

```text
AT+UMQTTC
```

Publish

```text
AT+UMQPS
```

Subscribe

```text
AT+UMQTS
```

Disconnect

```text
AT+UMQTD
```

---

# 13. Bluetooth LE

Start Advertising

```text
AT+UBTA
```

Stop Advertising

```text
AT+UBTAD
```

Bluetooth Mode

```text
AT+UBTM?
```

---

# 14. Useful Events

Wi-Fi Connected

```text
+UEWLU
```

Wi-Fi Lost

```text
+UEWLD
```

TCP Data Received

```text
+UESODA
```

MQTT Data Received

```text
+UEMQDA
```

Bluetooth Connected

```text
+UUBTACLC
```

---

# Typical Workflow

```text
AT
↓
AT+GMM
↓
AT+CGMR
↓
AT+USYEE=1
↓
AT+UWSSC=0
↓
Choose Wi-Fi
↓
Connect
↓
Open TCP Socket
↓
Send Data
↓
Receive Data
↓
Close Socket
```

---

# Commands Verified on Your Module

✅ AT

✅ ATE0

✅ ATE1

✅ AT+GMI

✅ AT+GMM

✅ AT+CGMR

✅ AT+CGSN

✅ AT+USYEE=1

✅ AT+USYEC?

✅ AT+UWSSC=0

✅ AT+CPWROFF

---

# Tips

- Use **115200 baud**, 8 data bits, no parity, 1 stop bit.
- Always terminate commands with **CR** (`\r`) or **CR+LF** (`\r\n`).
- Enable extended errors (`AT+USYEE=1`) during development.
- Save configuration with `AT&W` after changing persistent settings.
- Watch for unsolicited events (`+UEWLU`, `+UEWLD`, `+UEWSND`) while connected.
