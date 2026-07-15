"""
Parsing utilities for mosquitto_ctrl command output.
Separates parsing logic from route handlers.
"""


def parse_roles(details):
    """Extract roles from client/group details."""
    return _parse_section(details, "Roles")


def parse_groups(details):
    """Extract groups from client details."""
    return _parse_section(details, "Groups")


def parse_clients(details):
    """Extract clients from group details."""
    return _parse_section(details, "Clients")


def _parse_section(details, section_name):
    """
    Generic parser for sections in mosquitto_ctrl output.
    
    Example output format:
        Roles:
            role_name (priority: -1)
            another_role (priority: 0)
    """
    values = []
    if not details:
        return values
    
    prefix = f"{section_name}:"
    in_section = False
    
    for line in details.splitlines():
        stripped = line.strip()
        
        # Section header found
        if stripped.startswith(prefix):
            in_section = True
            # Check if value on same line (e.g., "Roles: role1")
            value = line.split(":", 1)[1].strip()
            if value:
                values.append(value.split(" (priority:", 1)[0].strip())
        
        # Value in next line (indented)
        elif in_section and line.startswith(" " * 12) and "(priority:" in line:
            values.append(stripped.split(" (priority:", 1)[0].strip())
        
        # Section ended (non-indented line)
        elif stripped and not line.startswith(" " * 12):
            in_section = False
    
    return values


def parse_acls(details):
    """
    Extract ACLs from role details.
    
    Example output format:
        ACLs:
            publishClientSend: sensors/temperature allow (priority: 0)
    
    Returns:
        List of dicts: [{"acl_type": "publishClientSend", "access": "allow", "topic": "sensors/temperature"}]
    """
    acls = []
    if not details:
        return acls
    
    for line in details.splitlines():
        stripped = line.strip()
        
        # Skip empty lines or invalid format
        if not stripped or ":" not in stripped or "(priority:" not in stripped:
            continue
        
        # Remove "ACLs:" prefix if present
        if stripped.startswith("ACLs:"):
            stripped = stripped.split("ACLs:", 1)[1].strip()
        
        # Parse format: "publishClientSend: sensors/temperature allow (priority: 0)"
        parts = [part.strip() for part in stripped.split(":", 2)]
        if len(parts) != 3:
            continue
        
        acl_type, access, rest = parts
        topic = rest.split(" (priority:", 1)[0].strip()
        
        if acl_type and access and topic:
            acls.append({
                "acl_type": acl_type,
                "access": access,
                "topic": topic
            })
    
    return acls


def is_client_disabled(details):
    """
    Check if a client is disabled.
    
    A client is disabled if:
    1. The details contain "Disabled: true", OR
    2. The client is in the "blocked_clients" group
    """
    if not details:
        return False
    
    # Check for explicit disabled flag
    if "disabled: true" in details.lower():
        return True
    
    # Check if in blocked_clients group
    groups = parse_groups(details)
    return "blocked_clients" in groups


def format_acl_for_display(acl):
    """Format ACL dict as readable string."""
    return f"{acl['acl_type']} {acl['access']} {acl['topic']}"
