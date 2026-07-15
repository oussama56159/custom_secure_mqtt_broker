@echo off
netstat -ano | findstr ":8883" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo Secure MQTT broker is already running on port 8883.
    echo Use stop_broker.bat if you want to stop it.
    pause
    exit /b 0
)

"C:\Program Files\mosquitto\mosquitto.exe" -c "C:\custom_mqtt_broker\secure-mqtt-broker\mosquitto-secure.conf" -v
