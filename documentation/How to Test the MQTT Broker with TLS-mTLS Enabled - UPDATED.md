# How to Test the MQTT Broker with TLS/mTLS Enabled

**Updated Version - Dual Authentication (Certificate + Username/Password)**

This guide shows how to test your secure MQTT broker that requires:
1. Valid TLS client certificate (mTLS)
2. Username and password (Dynamic Security)

---

## Prerequisites

- Mosquitto installed and available in PATH
- Broker running on `localhost:8883`
- Certificates located in `C:\custom_mqtt_broker\certificates\`
- Default password for all clients: `906271`
- Admin username: `admin`
- Admin password: `906271`

---

## Important: PowerShell vs Bash Syntax

**This guide uses Windows PowerShell syntax:**
- Line continuation: backtick `` ` `` (NOT backslash `\`)
- Example:
  ```powershell
  mosquitto_sub -h localhost -p 8883 `
    --cafile C:\path\to\ca.crt `
    -u username `
    -P password
  ```

**If using Git Bash or WSL, replace backticks with backslash `\`**

**Easiest approach: Write commands on one line (works in both):**
  ```
  mosquitto_sub -h localhost -p 8883 --cafile C:\path\to\ca.crt -u username -P password
  ```

---

## Certificate Files Overview

| Certificate | Purpose | Username (from CN) |
|------------|---------|-------------------|
| `ca.crt` | Certificate Authority (trust anchor) | - |
| `admin_client.crt` + `admin_client.key` | Admin management | admin |
| `temp_sensor.crt` + `temp_sensor.key` | Temperature sensor | temperature_sensor |
| `hum_sensor.crt` + `hum_sensor.key` | Humidity sensor | humidity_sensor (if exists) |
| `client.crt` + `client.key` | Dashboard/subscriber | dashboard |

---

## Test 1: Subscribe as Dashboard

**Purpose:** Test if the dashboard can subscribe to all sensor topics.

**Command:**
```powershell
mosquitto_sub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\dashboard.crt `
  --key C:\custom_mqtt_broker\certificates\dashboard.key `
  -u dashboard `
  -P 906271 `
  -t sensors/# `
  -v
```

**Or as one line:**
```powershell
mosquitto_sub -h localhost -p 8883 --cafile C:\custom_mqtt_broker\certificates\ca.crt --cert C:\custom_mqtt_broker\certificates\client.crt --key C:\custom_mqtt_broker\certificates\client.key -u dashboard -P 906271 -t sensors/# -v
```

**Expected Result:**
- Connection succeeds
- You see messages from `sensors/temperature` and `sensors/humidity`
- Format: `sensors/temperature {"value": 25.6, ...}`

**Troubleshooting:**
- If "Connection refused: not authorised" → Check username/password
- If "Error: A TLS error occurred" → Check certificate paths
- If "No route to host" → Broker not running

---

## Test 2: Publish Temperature Data

**Purpose:** Test if temperature sensor can publish to its topic.

**Command:**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m '{"value": 25.5, "unit": "celsius", "timestamp": 1234567890}'
```

**Or as one line:**
```powershell
mosquitto_pub -h localhost -p 8883 --cafile C:\custom_mqtt_broker\certificates\ca.crt --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt --key C:\custom_mqtt_broker\certificates\temp_sensor.key -u temperature_sensor -P 906271 -t sensors/temperature -m '{"value": 25.5, "unit": "celsius", "timestamp": 1234567890}'
```

**Expected Result:**
- Message published successfully
- No error messages
- If you have a subscriber running (Test 1), it receives this message

**Troubleshooting:**
- If "Not authorized to publish" → Check ACL permissions for temperature_sensor role
- If "Connection refused" → User might be disabled or password wrong

---

## Test 3: Verify Role-Based Access Control

**Purpose:** Test if temperature sensor is blocked from publishing to humidity topic.

**Command (Should FAIL):**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/humidity `
  -m '{"value": 60}'
```

**Or as one line:**
```powershell
mosquitto_pub -h localhost -p 8883 --cafile C:\custom_mqtt_broker\certificates\ca.crt --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt --key C:\custom_mqtt_broker\certificates\temp_sensor.key -u temperature_sensor -P 906271 -t sensors/humidity -m '{"value": 60}'
```

**Expected Result:**
- Connection succeeds BUT publish is rejected
- No error message (silent failure is normal in MQTT QoS 0)
- Subscriber does NOT receive the message

**Why This Fails:**
The `temperature_sensor` user only has `publishClientSend` permission for `sensors/temperature`, not `sensors/humidity`.

---

## Test 4: Test Disabled User

**Purpose:** Verify that disabling a user prevents connections.

**Step 1 - Disable the user:**
```powershell
mosquitto_ctrl -h localhost -p 8883 `
  --cafile "C:\custom_mqtt_broker\certificates\ca.crt" `
  --cert "C:\custom_mqtt_broker\certificates\admin_client.crt" `
  --key "C:\custom_mqtt_broker\certificates\admin_client.key" `
  -u admin `
  -P 906271 `
  dynsec disableClient temperature_sensor
```

**Step 2 - Try to publish (Should FAIL):**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "test"
```

**Expected Result:**
- Error: `Connection refused: not authorised`
- User cannot connect at all

**Step 3 - Re-enable the user:**
```powershell
mosquitto_ctrl -h localhost -p 8883 `
  --cafile "C:\custom_mqtt_broker\certificates\ca.crt" `
  --cert "C:\custom_mqtt_broker\certificates\admin_client.crt" `
  --key "C:\custom_mqtt_broker\certificates\admin_client.key" `
  -u admin `
  -P 906271 `
  dynsec enableClient temperature_sensor
```

**Step 4 - Try to publish again (Should SUCCEED):**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "test_after_enable"
```

**Expected Result:**
- Connection succeeds
- Message published successfully

---

## Test 5: Certificate Validation (No Client Certificate)

**Purpose:** Verify that broker rejects connections without client certificate.

**Command (Should FAIL):**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "no_cert_test"
```

**Expected Result:**
- Error: `A TLS error occurred` or `Connection refused`
- Connection fails at TLS handshake

**Why This Fails:**
The broker has `require_certificate true`, which means all clients MUST present a valid certificate.

---

## Test 6: Invalid Certificate

**Purpose:** Test that self-signed or invalid certificates are rejected.

**Command (Should FAIL):**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\invalid.crt `
  --key C:\custom_mqtt_broker\certificates\invalid.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "invalid_cert_test"
```

**Expected Result:**
- Error: `A TLS error occurred` or certificate verification failed
- Connection fails during TLS handshake

**Why This Fails:**
The `invalid.crt` certificate is not signed by the trusted CA (`ca.crt`).

---

## Test 7: Wrong Password

**Purpose:** Verify that wrong password is rejected even with valid certificate.

**Command (Should FAIL):**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P wrongpassword `
  -t sensors/temperature `
  -m "test"
```

**Expected Result:**
- Error: `Connection refused: not authorised`
- Authentication fails at dynamic security layer

**Why This Fails:**
Even though the certificate is valid, the username/password combination must also be correct.

---

## Test 8: Quality of Service (QoS) Levels

**Purpose:** Test different QoS levels for message delivery.

### QoS 0 (Fire and Forget)
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "qos0_test" `
  -q 0
```

### QoS 1 (At Least Once)
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "qos1_test" `
  -q 1
```

### QoS 2 (Exactly Once)
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "qos2_test" `
  -q 2
```

**Expected Result:**
- All should succeed (if ACLs allow)
- Higher QoS levels provide stronger delivery guarantees

---

## Test 9: Retained Messages

**Purpose:** Test if messages can be retained on the broker.

**Step 1 - Publish a retained message:**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m '{"value": 22.5, "retained": true}' `
  -r
```

**Step 2 - Subscribe to see the retained message:**
```powershell
mosquitto_sub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\client.crt `
  --key C:\custom_mqtt_broker\certificates\client.key `
  -u dashboard `
  -P 906271 `
  -t sensors/temperature `
  -v
```

**Expected Result:**
- Subscriber immediately receives the retained message
- No need to wait for a new publish

**Step 3 - Clear the retained message:**
```powershell
mosquitto_pub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\temp_sensor.crt `
  --key C:\custom_mqtt_broker\certificates\temp_sensor.key `
  -u temperature_sensor `
  -P 906271 `
  -t sensors/temperature `
  -m "" `
  -r
```

---

## Test 10: Wildcard Subscriptions

**Purpose:** Test wildcard topic patterns.

### Single-level wildcard (+)
```powershell
mosquitto_sub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\client.crt `
  --key C:\custom_mqtt_broker\certificates\client.key `
  -u dashboard `
  -P 906271 `
  -t sensors/+ `
  -v
```
**Matches:** `sensors/temperature`, `sensors/humidity`  
**Does NOT match:** `sensors/room/temperature` (nested topics)

### Multi-level wildcard (#)
```powershell
mosquitto_sub -h localhost -p 8883 `
  --cafile C:\custom_mqtt_broker\certificates\ca.crt `
  --cert C:\custom_mqtt_broker\certificates\client.crt `
  --key C:\custom_mqtt_broker\certificates\client.key `
  -u dashboard `
  -P 906271 `
  -t sensors/# `
  -v
```
**Matches:** All topics under `sensors/` including nested ones

---

## Test 11: Check User Status

**Purpose:** Verify user configuration and permissions.

**Get user details:**
```powershell
mosquitto_ctrl -h localhost -p 8883 `
  --cafile "C:\custom_mqtt_broker\certificates\ca.crt" `
  --cert "C:\custom_mqtt_broker\certificates\admin_client.crt" `
  --key "C:\custom_mqtt_broker\certificates\admin_client.key" `
  -u admin `
  -P 906271 `
  dynsec getClient temperature_sensor
```

**Expected Output:**
```
Username:    temperature_sensor
Clientid:    
Disabled:    false
Roles:       (list of assigned roles)
Groups:      sensor_devices (priority: -1)
```

**List all users:**
```powershell
mosquitto_ctrl -h localhost -p 8883 `
  --cafile "C:\custom_mqtt_broker\certificates\ca.crt" `
  --cert "C:\custom_mqtt_broker\certificates\admin_client.crt" `
  --key "C:\custom_mqtt_broker\certificates\admin_client.key" `
  -u admin `
  -P 906271 `
  dynsec listClients
```

---

## Test 12: Monitor Broker Logs

**Purpose:** View broker activity in real-time.

**Windows PowerShell:**
```powershell
Get-Content "C:\custom_mqtt_broker\secure-mqtt-broker\logs\mosquitto.log" -Wait -Tail 20
```

**What to Look For:**
- `New client connected from` - Successful connections
- `Connection refused` - Authentication failures
- `Received PUBLISH from` - Published messages
- `Sending PUBLISH to` - Messages delivered to subscribers
- `Client disconnected` - Clean disconnections
- `Socket error` or `TLS error` - Certificate/network issues

---

## Common Issues and Solutions

### Issue 1: "Connection refused: not authorised"
**Causes:**
- Wrong username or password
- User is disabled
- User doesn't exist in dynamic security

**Solution:**
- Check password in `secure-mqtt-broker/client-passwords.txt`
- Verify user is enabled: `dynsec getClient <username>`
- Create user if missing

### Issue 2: "A TLS error occurred"
**Causes:**
- Certificate not signed by CA
- Certificate file path wrong
- Certificate expired or invalid

**Solution:**
- Verify certificate: `openssl x509 -in <cert.crt> -noout -text`
- Check certificate paths in command
- Regenerate certificates if needed

### Issue 3: "No route to host"
**Causes:**
- Broker not running
- Wrong host/port

**Solution:**
- Start broker: `.\secure-mqtt-broker\start_broker.ps1`
- Check if port 8883 is listening: `netstat -an | findstr 8883`

### Issue 4: Publish succeeds but subscriber doesn't receive
**Causes:**
- Publisher doesn't have ACL permission
- Subscriber not subscribed to correct topic
- Network issue

**Solution:**
- Check role ACLs for publisher
- Verify topic spelling matches exactly
- Check broker logs for errors

### Issue 5: Disabled user still connects
**Causes:**
- Existing connection from before disabling
- Using wrong certificate/username combination

**Solution:**
- Disabling only prevents NEW connections
- Restart broker to force all reconnections
- Or wait for client to disconnect naturally

### Issue 6: PowerShell line continuation errors
**Causes:**
- Using backslash `\` instead of backtick `` ` ``
- Extra spaces after backtick

**Solution:**
- Use backtick `` ` `` for line continuation in PowerShell
- Ensure no spaces after the backtick
- Or write command on one line

---

## Security Best Practices

1. **Never commit certificates or passwords to version control**
   - Keep certificates in a secure location
   - Use environment variables or secure vaults for passwords

2. **Use strong passwords**
   - Default `906271` is for testing only
   - Change to strong unique passwords in production

3. **Regularly rotate certificates**
   - Set expiration dates on certificates
   - Have a rotation plan before expiry

4. **Minimize permissions**
   - Only grant necessary ACLs to each user
   - Use groups for managing multiple users

5. **Monitor broker logs**
   - Watch for failed authentication attempts
   - Alert on suspicious patterns

6. **Keep Mosquitto updated**
   - Apply security patches promptly
   - Review release notes for security fixes

---

## Quick Reference Card

| Test Type | Username | Certificate | Expected Result |
|-----------|----------|-------------|-----------------|
| Dashboard Subscribe | dashboard | client.crt | SUCCESS |
| Temp Sensor Publish | temperature_sensor | temp_sensor.crt | SUCCESS |
| Wrong Topic | temperature_sensor | temp_sensor.crt | SILENT FAIL (ACL) |
| Disabled User | temperature_sensor | temp_sensor.crt | CONNECTION REFUSED |
| No Certificate | temperature_sensor | (none) | TLS ERROR |
| Invalid Certificate | temperature_sensor | invalid.crt | TLS ERROR |
| Wrong Password | temperature_sensor | temp_sensor.crt | NOT AUTHORISED |

---

## Appendix: Certificate CN to Username Mapping

When `use_identity_as_username` was `true`, the CN became the username automatically.  
Now with `use_identity_as_username false`, you must explicitly provide BOTH:

| Certificate File | CN (Common Name) | Username in Dynamic Security | Password |
|-----------------|------------------|------------------------------|----------|
| admin_client.crt | admin | admin | 906271 |
| temp_sensor.crt | temperature_sensor | temperature_sensor | 906271 |
| hum_sensor.crt | humidity_sensor | humidity_sensor (if exists) | 906271 |
| client.crt | dashboard | dashboard | 906271 |

**Important:** The certificate CN and username don't need to match anymore, but it's good practice to keep them aligned to avoid confusion.

---

**Document Version:** 2.0 (Dual Authentication)  
**Last Updated:** 2026  
**Configuration:** `use_identity_as_username false` + Dynamic Security Plugin
