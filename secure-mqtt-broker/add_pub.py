import subprocess
from pathlib import Path


# badle el esm wo l lunch b  python add_pub.py aprt tmess chy 
PUBLISHER_NAME = "new_sensor"
PUBLISHER_PASSWORD = "906271"
ALLOWED_TOPIC = "sensors/new_sensor"
MAKE_ADMIN = False


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

    entries[PUBLISHER_NAME] = PUBLISHER_PASSWORD
    PASSWORDS_FILE.write_text(
        "\n".join(f"{key}={value}" for key, value in sorted(entries.items())) + "\n"
    )


role_name = f"{PUBLISHER_NAME}_publisher"

run_dynsec("createClient", PUBLISHER_NAME, "-p", PUBLISHER_PASSWORD, allow_existing=True)
run_dynsec("setClientPassword", PUBLISHER_NAME, PUBLISHER_PASSWORD)
run_dynsec("createRole", role_name, allow_existing=True)
run_dynsec("addRoleACL", role_name, "publishClientSend", ALLOWED_TOPIC, "allow", allow_existing=True)
run_dynsec("addClientRole", PUBLISHER_NAME, role_name, allow_existing=True)

if MAKE_ADMIN:
    run_dynsec("addClientRole", PUBLISHER_NAME, "admin", allow_existing=True)

save_password_reminder()

print("Publisher added.")
print(f"Username: {PUBLISHER_NAME}")
print(f"Password: {PUBLISHER_PASSWORD}")
print(f"Can publish to: {ALLOWED_TOPIC}")
print(f"Admin access: {'yes' if MAKE_ADMIN else 'no'}")

if MAKE_ADMIN:
    print("Warning: this user can manage broker users, roles, groups, and ACLs.")
