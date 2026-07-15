
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify

import config
import mosquitto_admin as broker
import parsers
import telemetry_store
from services import UserService


app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

# Initialize service layer
user_service = UserService()


# =============================================================================
# DECORATORS & HELPERS
# =============================================================================

def login_required(view):
    """Require user to be logged in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Require user to be logged in as admin."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("This account can only view telemetry.", "warning")
            return redirect(url_for("telemetry"))
        return view(*args, **kwargs)
    return wrapped


def handle_broker_action(success_message, action_func):
    """Execute a broker action and handle errors consistently."""
    try:
        action_func()
        flash(success_message, "success")
    except broker.MosquittoError as exc:
        flash(str(exc), "danger")


# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route("/", methods=["GET"])
def index():
    """Redirect to appropriate page based on login status."""
    if session.get("logged_in"):
        return redirect(url_for("clients"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
        # Check admin credentials
        if username == config.WEB_USERNAME and password == config.WEB_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            session["role"] = "admin"
            flash("Logged in successfully.", "success")
            return redirect(url_for("clients"))
        
        # Check telemetry viewer credentials
        if username == config.TELEMETRY_USERNAME and password == config.TELEMETRY_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            session["role"] = "telemetry"
            flash("Logged in successfully.", "success")
            return redirect(url_for("telemetry"))
        
        flash("Invalid username or password.", "danger")
    
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    """Handle user logout."""
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


# =============================================================================
# CLIENT/USER MANAGEMENT ROUTES
# =============================================================================

@app.route("/clients", methods=["GET"])
@admin_required
def clients():
    """Display client list with search and pagination."""
    selected = request.args.get("selected")
    search_query = (request.args.get("q") or "").strip().lower()
    
    # Get all clients
    try:
        client_names = broker.list_clients()
    except broker.MosquittoError:
        client_names = []
    
    # Apply search filter
    if search_query:
        client_names = [c for c in client_names if search_query in c.lower()]
    
    # Pagination
    try:
        per_page = int(request.args.get("per_page", 50))
    except ValueError:
        per_page = 50
    
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    
    total = len(client_names)
    start = (page - 1) * per_page
    end = start + per_page
    page_clients = client_names[start:end]
    
    # Get available roles and groups for forms
    try:
        roles = broker.list_roles()
    except broker.MosquittoError:
        roles = []
    
    try:
        groups = broker.list_groups()
    except broker.MosquittoError:
        groups = []
    
    # Build user summaries for the current page
    user_summaries = user_service.get_users_summaries(page_clients)
    
    # Get details for selected user
    details = None
    assigned_roles = []
    assigned_groups = []
    selected_disabled = False
    
    if selected:
        try:
            details = broker.get_client(selected)
            assigned_roles = parsers.parse_roles(details)
            assigned_groups = parsers.parse_groups(details)
            selected_disabled = parsers.is_client_disabled(details)
        except broker.MosquittoError:
            pass
    
    return render_template(
        "clients.html",
        clients=client_names,
        roles=roles,
        groups=groups,
        selected=selected,
        details=details,
        assigned_roles=assigned_roles,
        assigned_groups=assigned_groups,
        selected_disabled=selected_disabled,
        user_summaries=user_summaries,
        page=page,
        per_page=per_page,
        total=total,
    )


@app.route("/clients/create", methods=["POST"])
@admin_required
def clients_create():
    """Create a new client."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "")
    group = request.form.get("group", "")
    
    def _create():
        broker.create_client(username, password)
        if role:
            broker.add_client_role(username, role)
        if group:
            broker.add_group_client(group, username)
    
    handle_broker_action(f"Created user {username}.", _create)
    return redirect(url_for("clients", selected=username))


@app.route("/clients/bulk_delete", methods=["POST"])
@admin_required
def clients_bulk_delete():
    """Delete multiple clients."""
    usernames = request.form.getlist("usernames") or []
    
    def _bulk_delete():
        for username in usernames:
            broker.delete_client(username)
    
    handle_broker_action(f"Deleted {len(usernames)} users.", _bulk_delete)
    return redirect(url_for("clients"))


@app.route("/clients/<username>/json", methods=["GET"])
@admin_required
def clients_json(username):
    """Get client details as JSON (for API or AJAX requests)."""
    try:
        details = broker.get_client(username)
    except broker.MosquittoError:
        return jsonify({"error": "not found"}), 404
    
    data = {
        "username": username,
        "details": details,
        "roles": parsers.parse_roles(details),
        "groups": parsers.parse_groups(details),
        "acls": parsers.parse_acls(details),
    }
    return jsonify(data)


@app.route("/clients/<username>/update", methods=["POST"])
@admin_required
def clients_update(username):
    """Update client password, roles, and groups."""
    password = request.form.get("password", None)
    new_roles = request.form.getlist("roles")
    new_groups = request.form.getlist("groups")
    
    def _update():
        user_service.update_user(
            username,
            password=password,
            roles=new_roles,
            groups=new_groups
        )
    
    handle_broker_action(f"Updated user {username}.", _update)
    return redirect(url_for("clients", selected=username))


@app.route("/clients/<username>/delete", methods=["POST"])
@admin_required
def clients_delete(username):
    """Delete a client."""
    handle_broker_action(
        f"Deleted user {username}.",
        lambda: broker.delete_client(username)
    )
    return redirect(url_for("clients"))


@app.route("/clients/<username>/enable", methods=["POST"])
@admin_required
def clients_enable(username):
    """Enable a disabled client."""
    handle_broker_action(
        f"Enabled user {username}.",
        lambda: user_service.enable_user(username)
    )
    return redirect(url_for("clients", selected=username))


@app.route("/clients/<username>/disable", methods=["POST"])
@admin_required
def clients_disable(username):
    """Disable a client (prevents new connections)."""
    handle_broker_action(
        f"Disabled user {username}.",
        lambda: user_service.disable_user(username)
    )
    flash(
        "Note: Existing connections remain active until they disconnect. "
        "To force immediate disconnection, restart the broker or the client.",
        "warning"
    )
    return redirect(url_for("clients", selected=username))


@app.route("/clients/<username>/password", methods=["POST"])
@admin_required
def clients_password(username):
    """Change client password."""
    password = request.form.get("password", "")
    handle_broker_action(
        f"Changed password for {username}.",
        lambda: broker.set_client_password(username, password)
    )
    return redirect(url_for("clients", selected=username))


@app.route("/clients/<username>/roles/add", methods=["POST"])
@admin_required
def clients_role_add(username):
    """Add a role to a client."""
    role = request.form.get("role", "")
    priority = request.form.get("priority", "")
    handle_broker_action(
        f"Assigned {role} to {username}.",
        lambda: broker.add_client_role(username, role, priority)
    )
    return redirect(url_for("clients", selected=username))


@app.route("/clients/<username>/roles/remove", methods=["POST"])
@admin_required
def clients_role_remove(username):
    """Remove a role from a client."""
    role = request.form.get("role", "")
    handle_broker_action(
        f"Removed {role} from {username}.",
        lambda: broker.remove_client_role(username, role)
    )
    return redirect(url_for("clients", selected=username))


# =============================================================================
# ROLE MANAGEMENT ROUTES
# =============================================================================

@app.route("/roles", methods=["GET"])
@admin_required
def roles():
    """Display roles list and ACLs."""
    selected = request.args.get("selected")
    
    role_names = broker.list_roles()
    details = broker.get_role(selected) if selected else None
    existing_acls = parsers.parse_acls(details)
    
    acl_types = [
        "publishClientSend",
        "publishClientReceive",
        "subscribeLiteral",
        "subscribePattern",
        "unsubscribeLiteral",
        "unsubscribePattern",
    ]
    
    return render_template(
        "roles.html",
        roles=role_names,
        selected=selected,
        details=details,
        acl_types=acl_types,
        existing_acls=existing_acls
    )


@app.route("/roles/create", methods=["POST"])
@admin_required
def roles_create():
    """Create a new role."""
    role = request.form.get("role", "").strip()
    handle_broker_action(
        f"Created role {role}.",
        lambda: broker.create_role(role)
    )
    return redirect(url_for("roles", selected=role))


@app.route("/roles/<role>/delete", methods=["POST"])
@admin_required
def roles_delete(role):
    """Delete a role."""
    handle_broker_action(
        f"Deleted role {role}.",
        lambda: broker.delete_role(role)
    )
    return redirect(url_for("roles"))


@app.route("/roles/<role>/acls/add", methods=["POST"])
@admin_required
def roles_acl_add(role):
    """Add an ACL to a role."""
    acl_type = request.form.get("acl_type", "")
    topic = request.form.get("topic", "")
    allow = request.form.get("allow", "allow")
    priority = request.form.get("priority", "")
    
    handle_broker_action(
        f"Added ACL to {role}.",
        lambda: broker.add_role_acl(role, acl_type, topic, allow, priority)
    )
    return redirect(url_for("roles", selected=role))


@app.route("/roles/<role>/acls/remove", methods=["POST"])
@admin_required
def roles_acl_remove(role):
    """Remove an ACL from a role."""
    acl_type = request.form.get("acl_type", "")
    topic = request.form.get("topic", "")
    allow = request.form.get("allow", "allow")
    
    handle_broker_action(
        f"Removed ACL from {role}.",
        lambda: broker.remove_role_acl(role, acl_type, topic, allow)
    )
    return redirect(url_for("roles", selected=role))


# =============================================================================
# GROUP MANAGEMENT ROUTES
# =============================================================================

@app.route("/groups", methods=["GET"])
@admin_required
def groups():
    """Display groups list."""
    selected = request.args.get("selected")
    
    group_names = broker.list_groups()
    clients_list = broker.list_clients()
    roles_list = broker.list_roles()
    details = broker.get_group(selected) if selected else None
    
    group_clients = parsers.parse_clients(details)
    group_roles = parsers.parse_roles(details)
    
    return render_template(
        "groups.html",
        groups=group_names,
        clients=clients_list,
        roles=roles_list,
        selected=selected,
        details=details,
        group_clients=group_clients,
        group_roles=group_roles,
    )


@app.route("/groups/create", methods=["POST"])
@admin_required
def groups_create():
    """Create a new group."""
    group = request.form.get("group", "").strip()
    handle_broker_action(
        f"Created group {group}.",
        lambda: broker.create_group(group)
    )
    return redirect(url_for("groups", selected=group))


@app.route("/groups/<group>/delete", methods=["POST"])
@admin_required
def groups_delete(group):
    """Delete a group."""
    handle_broker_action(
        f"Deleted group {group}.",
        lambda: broker.delete_group(group)
    )
    return redirect(url_for("groups"))


@app.route("/groups/<group>/clients/add", methods=["POST"])
@admin_required
def groups_client_add(group):
    """Add a client to a group."""
    username = request.form.get("username", "")
    priority = request.form.get("priority", "")
    
    handle_broker_action(
        f"Added {username} to {group}.",
        lambda: broker.add_group_client(group, username, priority)
    )
    return redirect(url_for("groups", selected=group))


@app.route("/groups/<group>/clients/remove", methods=["POST"])
@admin_required
def groups_client_remove(group):
    """Remove a client from a group."""
    username = request.form.get("username", "")
    handle_broker_action(
        f"Removed {username} from {group}.",
        lambda: broker.remove_group_client(group, username)
    )
    return redirect(url_for("groups", selected=group))


@app.route("/groups/<group>/roles/add", methods=["POST"])
@admin_required
def groups_role_add(group):
    """Add a role to a group."""
    role = request.form.get("role", "")
    priority = request.form.get("priority", "")
    
    handle_broker_action(
        f"Assigned {role} to {group}.",
        lambda: broker.add_group_role(group, role, priority)
    )
    return redirect(url_for("groups", selected=group))


@app.route("/groups/<group>/roles/remove", methods=["POST"])
@admin_required
def groups_role_remove(group):
    """Remove a role from a group."""
    role = request.form.get("role", "")
    handle_broker_action(
        f"Removed {role} from {group}.",
        lambda: broker.remove_group_role(group, role)
    )
    return redirect(url_for("groups", selected=group))


# =============================================================================
# STATUS & MONITORING ROUTES
# =============================================================================

@app.route("/status", methods=["GET"])
@admin_required
def status():
    """Display broker status and logs."""
    status_info = broker.broker_status()
    
    log_tail = ""
    if config.LOG_FILE.exists():
        lines = config.LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        log_tail = "\n".join(lines[-40:])
    
    return render_template("status.html", status=status_info, log_tail=log_tail)


# =============================================================================
# TELEMETRY ROUTES
# =============================================================================

@app.route("/telemetry", methods=["GET"])
@login_required
def telemetry():
    """Display telemetry dashboard."""
    telemetry_store.start_collector()
    return render_template("telemetry.html")


@app.route("/api/telemetry", methods=["GET"])
@login_required
def telemetry_api():
    """Get current telemetry data as JSON."""
    telemetry_store.start_collector()
    return jsonify(telemetry_store.snapshot())


@app.route("/api/telemetry/series", methods=["GET"])
@login_required
def telemetry_series_api():
    """Get time series data for a specific device and field."""
    device = request.args.get("device", "")
    field = request.args.get("field", "")
    return jsonify({"points": telemetry_store.series_snapshot(device, field)})


@app.route("/api/telemetry/widgets", methods=["POST"])
@login_required
def telemetry_widgets_api():
    """Save widget configuration."""
    data = request.get_json(silent=True) or {}
    widgets = telemetry_store.save_widget_config(
        data.get("device", ""),
        data.get("field", ""),
        data.get("type", "chart"),
    )
    return jsonify({"widgets": widgets})


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
