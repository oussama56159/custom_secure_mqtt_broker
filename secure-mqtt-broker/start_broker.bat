@echo off
netstat -ano | findstr ":1884" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo Secure MQTT broker is already running on port 1884.
    echo Use stop_broker.bat if you want to stop it.
    pause
    exit /b 0
)

"C:\Program Files\mosquitto\mosquitto.exe" -c "C:\custom_secure_mqtt_broker\secure-mqtt-broker\mosquitto-secure.conf" -v
