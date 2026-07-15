$broker = "C:\Program Files\mosquitto\mosquitto.exe"
$config = "C:\custom_mqtt_broker\secure-mqtt-broker\mosquitto-secure.conf"

& $broker -c $config -v
