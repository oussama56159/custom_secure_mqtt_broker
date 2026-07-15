import json
import ssl
import threading
import time
from collections import defaultdict, deque

import config

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


MAX_MESSAGES = 300
MAX_SERIES_POINTS = 120
OFFLINE_AFTER_SECONDS = 20

lock = threading.Lock()
started = False
collector_error = None
messages = deque(maxlen=MAX_MESSAGES)
devices = {}
series = defaultdict(lambda: deque(maxlen=MAX_SERIES_POINTS))
widget_config = {}


def _device_from_message(topic, payload):
    if isinstance(payload, dict):
        for key in ("device", "sensor", "client", "client_id", "id"):
            value = payload.get(key)
            if value:
                return str(value)
        if payload.get("type"):
            return f"{payload['type']}_sensor"
    parts = topic.split("/")
    if len(parts) > 1:
        return f"{parts[1]}_sensor"
    return topic


def _numeric_fields(payload):
    if not isinstance(payload, dict):
        return {}
    ignored = {"timestamp", "time", "ts"}
    return {
        key: float(value)
        for key, value in payload.items()
        if key.lower() not in ignored and isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _parse_payload(raw_payload):
    text = raw_payload.decode("utf-8", errors="replace")
    try:
        return json.loads(text), text
    except json.JSONDecodeError:
        return text, text


def record_message(topic, raw_payload):
    now = time.time()
    payload, text = _parse_payload(raw_payload)
    device = _device_from_message(topic, payload)
    numeric = _numeric_fields(payload)

    with lock:
        entry = {
            "device": device,
            "topic": topic,
            "payload": payload,
            "payload_text": text,
            "timestamp": now,
        }
        messages.appendleft(entry)
        current = devices.setdefault(
            device,
            {
                "device": device,
                "topics": set(),
                "fields": set(),
                "last_seen": 0,
                "last_payload": None,
            },
        )
        current["topics"].add(topic)
        current["fields"].update(numeric.keys())
        current["last_seen"] = now
        current["last_payload"] = payload
        for field, value in numeric.items():
            series[(device, field)].append({"x": now, "y": value})


def snapshot():
    now = time.time()
    with lock:
        device_rows = []
        for device in devices.values():
            age = now - device["last_seen"]
            device_rows.append(
                {
                    "device": device["device"],
                    "online": age <= OFFLINE_AFTER_SECONDS,
                    "last_seen": device["last_seen"],
                    "seconds_since_seen": round(age, 1),
                    "topics": sorted(device["topics"]),
                    "fields": sorted(device["fields"]),
                    "last_payload": device["last_payload"],
                }
            )
        return {
            "collector": {
                "available": mqtt is not None,
                "started": started,
                "error": collector_error,
                "topic": config.TELEMETRY_TOPIC,
                "username": config.TELEMETRY_USERNAME,
            },
            "devices": sorted(device_rows, key=lambda row: row["device"]),
            "messages": list(messages)[:80],
            "widgets": widget_config,
        }


def series_snapshot(device, field):
    with lock:
        return list(series.get((device, field), []))


def save_widget_config(device, field, widget_type):
    with lock:
        widget_config[f"{device}:{field}"] = widget_type
        return widget_config


def start_collector():
    global started, collector_error
    if started:
        return
    started = True
    if mqtt is None:
        collector_error = "paho-mqtt is not installed. Run pip install -r requirements.txt."
        return

    def run():
        global collector_error, started
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=config.TELEMETRY_CLIENT_ID)
            client.username_pw_set(config.TELEMETRY_USERNAME, config.TELEMETRY_PASSWORD)
            client.tls_set(
                ca_certs=str(config.CA_FILE),
                certfile=str(config.TELEMETRY_CERT),
                keyfile=str(config.TELEMETRY_KEY),
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS_CLIENT,
            )

            def on_connect(client, userdata, flags, reason_code, properties):
                global collector_error
                if not reason_code.is_failure:
                    collector_error = None
                    client.subscribe(config.TELEMETRY_TOPIC)
                else:
                    collector_error = f"MQTT connection failed: {reason_code}"

            def on_message(client, userdata, msg):
                record_message(msg.topic, msg.payload)

            client.on_connect = on_connect
            client.on_message = on_message
            while True:
                try:
                    client.connect(config.BROKER_HOST, int(config.BROKER_PORT), keepalive=30)
                    client.loop_forever(retry_first_connection=True)
                except Exception as exc:
                    collector_error = str(exc)
                    time.sleep(5)
        except Exception as exc:
            collector_error = str(exc)
            started = False

    threading.Thread(target=run, daemon=True, name="telemetry-mqtt-collector").start()
