from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

SECRET_KEY = "change-this-dev-secret"
WEB_USERNAME = "admin"
WEB_PASSWORD = "906271"

MOSQUITTO_CTRL = r"C:\Program Files\mosquitto\mosquitto_ctrl.exe"
BROKER_HOST = "localhost"
BROKER_PORT = "8883"
MOSQUITTO_CTRL_USERNAME = "admin"
MOSQUITTO_CTRL_PASSWORD = "906271"

# Backward-compatible aliases used by older code paths.
BROKER_USERNAME = MOSQUITTO_CTRL_USERNAME
BROKER_PASSWORD = MOSQUITTO_CTRL_PASSWORD

CERT_DIR = BASE_DIR / "certificates"
CA_FILE = CERT_DIR / "ca.crt"
ADMIN_CERT = CERT_DIR / "admin_client.crt"
ADMIN_KEY = CERT_DIR / "admin_client.key"

LOG_FILE = BASE_DIR / "secure-mqtt-broker" / "logs" / "mosquitto.log"

TELEMETRY_USERNAME = "dashboard"
TELEMETRY_PASSWORD = "906271"
TELEMETRY_CLIENT_ID = "flask-telemetry-dashboard"
TELEMETRY_TOPIC = "sensors/#"
TELEMETRY_CERT = CERT_DIR / "client.crt"
TELEMETRY_KEY = CERT_DIR / "client.key"
