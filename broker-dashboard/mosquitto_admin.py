import subprocess
import sys

import config


class MosquittoError(RuntimeError):
    pass


def run_dynsec(*args):
    command = [
        config.MOSQUITTO_CTRL,
        "-h",
        config.BROKER_HOST,
        "-p",
        config.BROKER_PORT,
        "--cafile",
        str(config.CA_FILE),
        "--cert",
        str(config.ADMIN_CERT),
        "--key",
        str(config.ADMIN_KEY),
        "-u",
        config.MOSQUITTO_CTRL_USERNAME,
        "-P",
        config.MOSQUITTO_CTRL_PASSWORD,
        "dynsec",
        *[str(arg) for arg in args if arg is not None and str(arg) != ""],
    ]

    redacted_command = list(command)
    if "-u" in redacted_command:
        username_index = redacted_command.index("-u") + 1
        if username_index < len(redacted_command):
            redacted_command[username_index] = "<redacted>"
    if "-P" in redacted_command:
        password_index = redacted_command.index("-P") + 1
        if password_index < len(redacted_command):
            redacted_command[password_index] = "<redacted>"
    print(f"[DEBUG] Running command: {' '.join(redacted_command)}", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)

        print(f"[DEBUG] Exit code: {result.returncode}", file=sys.stderr, flush=True)
        print(f"[DEBUG] Stdout: {result.stdout}", file=sys.stderr, flush=True)
        print(f"[DEBUG] Stderr: {result.stderr}", file=sys.stderr, flush=True)
        
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "Mosquitto command failed").strip()
            raise MosquittoError(f"Command failed (exit code {result.returncode}): {message}")
        return result.stdout.strip()
    except MosquittoError:
        raise
    except subprocess.TimeoutExpired:
        raise MosquittoError("Command timed out after 10 seconds")
    except FileNotFoundError:
        raise MosquittoError(f"mosquitto_ctrl not found at: {config.MOSQUITTO_CTRL}")
    except Exception as e:
        raise MosquittoError(f"Unexpected error: {str(e)}")


def list_items(command):
    output = run_dynsec(command)
    return [line.strip() for line in output.splitlines() if line.strip()]


def list_clients():
    return list_items("listClients")


def list_roles():
    return list_items("listRoles")


def list_groups():
    return list_items("listGroups")


def get_client(username):
    return run_dynsec("getClient", username)


def get_role(role):
    return run_dynsec("getRole", role)


def get_group(group):
    return run_dynsec("getGroup", group)


def create_client(username, password):
    return run_dynsec("createClient", username, "-p", password)


def delete_client(username):
    return run_dynsec("deleteClient", username)


def enable_client(username):
    return run_dynsec("enableClient", username)


def disable_client(username):
    return run_dynsec("disableClient", username)


def set_client_password(username, password):
    return run_dynsec("setClientPassword", username, password)


def add_client_role(username, role, priority=None):
    return run_dynsec("addClientRole", username, role, priority)


def remove_client_role(username, role):
    return run_dynsec("removeClientRole", username, role)


def create_group(group):
    return run_dynsec("createGroup", group)


def delete_group(group):
    return run_dynsec("deleteGroup", group)


def add_group_client(group, username, priority=None):
    return run_dynsec("addGroupClient", group, username, priority)


def remove_group_client(group, username):
    return run_dynsec("removeGroupClient", group, username)


def add_group_role(group, role, priority=None):
    return run_dynsec("addGroupRole", group, role, priority)


def remove_group_role(group, role):
    return run_dynsec("removeGroupRole", group, role)


def create_role(role):
    return run_dynsec("createRole", role)


def delete_role(role):
    return run_dynsec("deleteRole", role)


def add_role_acl(role, acl_type, topic, allow, priority=None):
    return run_dynsec("addRoleACL", role, acl_type, topic, allow, priority)


def remove_role_acl(role, acl_type, topic, allow):
    return run_dynsec("removeRoleACL", role, acl_type, topic, allow)


def broker_status():
    try:
        clients = len(list_clients())
        roles = len(list_roles())
        return {"ok": True, "clients": clients, "roles": roles}
    except MosquittoError as exc:
        return {"ok": False, "error": str(exc)}
