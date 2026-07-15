# MQTT Broker Dashboard

A web-based management interface for Mosquitto MQTT Broker with TLS/mTLS and dynamic security.

## Features

- 🔐 Secure authentication (admin and telemetry viewer roles)
- 👥 User management (create, disable, delete MQTT users)
- 🛡️ Role-based access control (ACLs)
- 👪 Group management
- 📊 Real-time telemetry monitoring
- 📝 Broker logs viewing
- 🔍 User search and pagination

---

## Prerequisites

Before your friend can run the dashboard, they need:

### 1. **Python 3.7+**
Check if installed:
```bash
python --version
```

### 2. **Mosquitto Broker**
- Must be installed and in PATH
- Running on `localhost:8883` with TLS enabled
- Dynamic security plugin configured

### 3. **Certificates**
The following certificate files must exist in `../certificates/`:
- `ca.crt` - Certificate Authority
- `admin_client.crt` + `admin_client.key` - For dashboard to manage broker

### 4. **Python Dependencies**
Install via pip:
```bash
pip install -r requirements.txt
```

---

## Quick Start

### Step 1: Install Dependencies
```bash
cd broker-dashboard
pip install -r requirements.txt
```

### Step 2: Configure Settings
Edit `config.py` and update:
```python
# Paths (adjust if needed)
CERT_DIR = BASE_DIR / "certificates"
CA_FILE = CERT_DIR / "ca.crt"
ADMIN_CERT = CERT_DIR / "admin_client.crt"
ADMIN_KEY = CERT_DIR / "admin_client.key"

# Broker connection
BROKER_HOST = "localhost"
BROKER_PORT = "8883"
BROKER_USERNAME = "admin"
BROKER_PASSWORD = "906271"  # Change this!

# Dashboard login credentials
WEB_USERNAME = "admin"
WEB_PASSWORD = "906271"  # Change this!

TELEMETRY_USERNAME = "dashboard"
TELEMETRY_PASSWORD = "906271"  # Change this!
```

### Step 3: Start the Broker
Make sure the Mosquitto broker is running:
```bash
# From the project root
cd secure-mqtt-broker
.\start_broker.ps1
```

### Step 4: Run the Dashboard
```bash
cd broker-dashboard
python app.py
```

### Step 5: Open in Browser
Navigate to: http://127.0.0.1:5000

**Login credentials:**
- **Admin:** username=`admin`, password=`906271`
- **Telemetry Viewer:** username=`dashboard`, password=`906271`

---

## What Your Friend Needs (Checklist)

### ✅ Files to Send:
```
custom_mqtt_broker/
├── broker-dashboard/          # The web dashboard
│   ├── app.py
│   ├── config.py
│   ├── mosquitto_admin.py
│   ├── parsers.py
│   ├── services.py
│   ├── telemetry_store.py
│   ├── requirements.txt
│   ├── static/
│   └── templates/
├── certificates/              # TLS certificates
│   ├── ca.crt
│   ├── admin_client.crt
│   └── admin_client.key
├── secure-mqtt-broker/        # Broker config & scripts
│   ├── mosquitto-secure.conf
│   ├── dynamic-security.json
│   ├── start_broker.ps1
│   └── stop_broker.ps1
└── README.md
```

### ✅ Software to Install:
1. **Python 3.7+** - https://www.python.org/downloads/
2. **Mosquitto** - https://mosquitto.org/download/
3. **pip** (usually comes with Python)

### ✅ Python Packages:
```bash
pip install flask paho-mqtt
```

---

## Installation Instructions (Send to Friend)

### For Windows:

1. **Install Python:**
   - Download from https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation

2. **Install Mosquitto:**
   - Download from https://mosquitto.org/download/
   - Run installer
   - ✅ Make sure to add to PATH

3. **Extract Project Files:**
   - Unzip `custom_mqtt_broker.zip` to `C:\custom_mqtt_broker\`

4. **Install Python Dependencies:**
   ```powershell
   cd C:\custom_mqtt_broker\broker-dashboard
   pip install -r requirements.txt
   ```

5. **Start the Broker:**
   ```powershell
   cd C:\custom_mqtt_broker\secure-mqtt-broker
   .\start_broker.ps1
   ```

6. **Start the Dashboard:**
   ```powershell
   cd C:\custom_mqtt_broker\broker-dashboard
   python app.py
   ```

7. **Open Browser:**
   Go to http://127.0.0.1:5000

---

## Configuration

### Dashboard Settings (`config.py`)

```python
# Web interface credentials
WEB_USERNAME = "admin"
WEB_PASSWORD = "your_secure_password"

# Telemetry viewer credentials
TELEMETRY_USERNAME = "dashboard"
TELEMETRY_PASSWORD = "your_secure_password"

# Broker connection
BROKER_HOST = "localhost"
BROKER_PORT = "8883"
BROKER_USERNAME = "admin"
BROKER_PASSWORD = "broker_admin_password"

# Paths (relative to project root)
CERT_DIR = BASE_DIR / "certificates"
CA_FILE = CERT_DIR / "ca.crt"
ADMIN_CERT = CERT_DIR / "admin_client.crt"
ADMIN_KEY = CERT_DIR / "admin_client.key"
LOG_FILE = BASE_DIR / "secure-mqtt-broker" / "logs" / "mosquitto.log"
```

### Telemetry Settings (`config.py`)

For real-time sensor monitoring:
```python
TELEMETRY_CLIENT_ID = "flask-telemetry-dashboard"
TELEMETRY_TOPIC = "sensors/#"
TELEMETRY_CERT = CERT_DIR / "client.crt"
TELEMETRY_KEY = CERT_DIR / "client.key"
```

---

## Troubleshooting

### Issue: "Connection refused" when starting dashboard

**Cause:** Broker not running or wrong port

**Solution:**
```bash
# Check if broker is running
netstat -an | findstr 8883

# Start broker if not running
cd secure-mqtt-broker
.\start_broker.ps1
```

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "A TLS error occurred"

**Cause:** Certificate files missing or wrong paths

**Solution:**
- Check that `certificates/` folder exists
- Verify `ca.crt`, `admin_client.crt`, `admin_client.key` are present
- Update paths in `config.py` if files are in different location

### Issue: "mosquitto_ctrl not found"

**Cause:** Mosquitto not installed or not in PATH

**Solution:**
- Install Mosquitto: https://mosquitto.org/download/
- Add to PATH: `C:\Program Files\mosquitto`
- Restart terminal/PowerShell

### Issue: "Invalid username or password"

**Cause:** Wrong login credentials

**Solution:**
- Check `config.py` for correct `WEB_USERNAME` and `WEB_PASSWORD`
- Default is `admin` / `906271`

---

## Project Structure

```
broker-dashboard/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── mosquitto_admin.py     # Mosquitto broker commands
├── parsers.py             # Output parsing utilities
├── services.py            # Business logic layer
├── telemetry_store.py     # Real-time telemetry storage
├── requirements.txt       # Python dependencies
├── static/                # CSS, JavaScript
│   ├── app.js
│   ├── style.css
│   └── telemetry.js
└── templates/             # HTML templates
    ├── base.html
    ├── clients.html
    ├── groups.html
    ├── login.html
    ├── roles.html
    ├── status.html
    └── telemetry.html
```

---

## Security Notes

⚠️ **IMPORTANT:**

1. **Change default passwords** in `config.py` before deploying
2. **Never commit certificates** to version control
3. **Use HTTPS** in production (not just HTTP)
4. **Restrict access** - Don't expose dashboard to public internet
5. **Keep Mosquitto updated** for security patches

---

## Features Overview

### 👥 User Management
- Create/delete MQTT users
- Enable/disable users
- Change passwords
- Assign roles and groups

### 🛡️ Access Control
- Create roles with specific permissions
- Define ACLs (publish/subscribe topics)
- Group users for easier management

### 📊 Telemetry Monitoring
- Real-time sensor data visualization
- Supports temperature, humidity sensors
- Time-series charts
- Alert thresholds

### 📝 Broker Status
- View connected clients
- Monitor broker logs
- Check system status

---

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `POST /logout` - Logout

### Clients
- `GET /clients` - List all clients
- `POST /clients/create` - Create new client
- `POST /clients/<username>/disable` - Disable client
- `POST /clients/<username>/enable` - Enable client
- `DELETE /clients/<username>/delete` - Delete client

### Roles
- `GET /roles` - List all roles
- `POST /roles/create` - Create new role
- `POST /roles/<role>/acls/add` - Add ACL to role

### Groups
- `GET /groups` - List all groups
- `POST /groups/create` - Create new group
- `POST /groups/<group>/clients/add` - Add client to group

### Telemetry
- `GET /telemetry` - Telemetry dashboard
- `GET /api/telemetry` - Get current sensor data (JSON)

---

## Development

### Running in Debug Mode
```bash
python app.py
```
Flask debug mode is enabled by default (see `app.py` last line).

### Code Organization
- **app.py** - Route handlers only
- **services.py** - Business logic
- **parsers.py** - Data parsing
- **mosquitto_admin.py** - Broker communication

This separation makes the code easier to understand and maintain!

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the documentation in `/documentation`
3. Check broker logs in `/secure-mqtt-broker/logs/mosquitto.log`

---

## License

This project is for educational/internal use.

---

**Version:** 2.0 (Dual Authentication)  
**Last Updated:** 2026
