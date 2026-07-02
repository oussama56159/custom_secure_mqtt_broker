import subprocess
from pathlib import Path


# kif kif 
SUBSCRIBER_NAME = "new_dashboard"
SUBSCRIBER_PASSWORD = "906271"
ALLOWED_TOPIC = "sensors/#"


MOSQUITTO_CTRL = Path(r"C:\Program Files\mosquitto\mosquitto_ctrl.exe")
HOST = "localhost"
PORT = "1884"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "906271"
PASSWORDS_FILE = Path("client-passwords.txt")


def run_dynsec(*args, allow_existing=False):
    command = [
        str(MOSQUITTO_CTRL),
        "-h",
        HOST,
        "-p",
        PORT,
        "-u",
        ADMIN_USER,
        "-P",
        ADMIN_PASSWORD,
        "dynsec",
        *args,
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        if allow_existing and "already exists" in output.lower():
            return
        raise RuntimeError(output)


def save_password_reminder():
    entries = {}
    if PASSWORDS_FILE.exists():
        for line in PASSWORDS_FILE.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                entries[key.strip()] = value.strip()

    entries[SUBSCRIBER_NAME] = SUBSCRIBER_PASSWORD
    PASSWORDS_FILE.write_text(
        "\n".join(f"{key}={value}" for key, value in sorted(entries.items())) + "\n"
    )


role_name = f"{SUBSCRIBER_NAME}_subscriber"

run_dynsec("createClient", SUBSCRIBER_NAME, "-p", SUBSCRIBER_PASSWORD, allow_existing=True)
run_dynsec("setClientPassword", SUBSCRIBER_NAME, SUBSCRIBER_PASSWORD)
run_dynsec("createRole", role_name, allow_existing=True)
run_dynsec("addRoleACL", role_name, "subscribePattern", ALLOWED_TOPIC, "allow", allow_existing=True)
run_dynsec("addRoleACL", role_name, "publishClientReceive", ALLOWED_TOPIC, "allow", allow_existing=True)
run_dynsec("addClientRole", SUBSCRIBER_NAME, role_name, allow_existing=True)
save_password_reminder()

print("Subscriber added.")
print(f"Username: {SUBSCRIBER_NAME}")
print(f"Password: {SUBSCRIBER_PASSWORD}")
print(f"Can subscribe to: {ALLOWED_TOPIC}")
