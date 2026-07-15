"""
Business logic layer for user management.
Separates complex operations from route handlers.
"""

import mosquitto_admin as broker
import parsers


class UserService:
    """Service for managing MQTT users and their permissions."""
    
    def __init__(self):
        # Cache for group and role lookups to reduce broker calls
        self._group_role_cache = {}
        self._role_topic_cache = {}
    
    def get_user_summary(self, username):
        """
        Get a comprehensive summary of a user's permissions.
        
        Returns:
            dict with username, groups, direct_roles, all_roles, topics, disabled status
        """
        try:
            details = broker.get_client(username)
        except broker.MosquittoError:
            details = ""
        
        # Parse basic info
        direct_roles = parsers.parse_roles(details)
        groups = parsers.parse_groups(details)
        disabled = parsers.is_client_disabled(details)
        
        # Get roles inherited from groups
        inherited_roles = []
        for group in groups:
            group_roles = self._get_group_roles(group)
            inherited_roles.extend(group_roles)
        
        # Combine all roles (direct + inherited)
        all_roles = sorted(set(direct_roles + inherited_roles))
        
        # Get all topics from all roles
        topics = []
        for role in all_roles:
            role_topics = self._get_role_topics(role)
            topics.extend(role_topics)
        
        return {
            "username": username,
            "groups": sorted(set(groups)),
            "direct_roles": sorted(set(direct_roles)),
            "roles": all_roles,
            "topics": sorted(set(topics)),
            "disabled": disabled,
        }
    
    def get_users_summaries(self, usernames):
        """Get summaries for multiple users efficiently."""
        return [self.get_user_summary(username) for username in usernames]
    
    def disable_user(self, username):
        """
        Disable a user and add to blocked_clients group.
        
        Note: This only prevents NEW connections. Existing connections
        remain active until they disconnect.
        """
        # Disable the user (this is critical)
        broker.disable_client(username)
        
        # Add to blocked_clients group (best effort)
        try:
            broker.create_group("blocked_clients")
        except broker.MosquittoError:
            pass  # Group might already exist
        
        try:
            broker.add_group_client("blocked_clients", username)
        except broker.MosquittoError:
            pass  # Already in group or other error
    
    def enable_user(self, username):
        """Enable a user and remove from blocked_clients group."""
        broker.enable_client(username)
        
        # Remove from blocked_clients group (best effort)
        try:
            broker.remove_group_client("blocked_clients", username)
        except broker.MosquittoError:
            pass  # Not in group or other error
    
    def update_user(self, username, password=None, roles=None, groups=None):
        """
        Update user password, roles, and groups.
        
        Args:
            username: Username to update
            password: New password (optional)
            roles: List of role names (replaces current roles)
            groups: List of group names (replaces current groups)
        """
        # Update password if provided
        if password:
            broker.set_client_password(username, password)
        
        # Get current state
        try:
            details = broker.get_client(username)
        except broker.MosquittoError:
            details = ""
        
        # Update roles if provided
        if roles is not None:
            current_roles = parsers.parse_roles(details)
            
            # Remove old roles
            for role in current_roles:
                if role not in roles:
                    broker.remove_client_role(username, role)
            
            # Add new roles
            for role in roles:
                if role not in current_roles:
                    broker.add_client_role(username, role)
        
        # Update groups if provided
        if groups is not None:
            current_groups = parsers.parse_groups(details)
            
            # Remove from old groups
            for group in current_groups:
                if group not in groups:
                    broker.remove_group_client(group, username)
            
            # Add to new groups
            for group in groups:
                if group not in current_groups:
                    broker.add_group_client(group, username)
    
    def clear_cache(self):
        """Clear cached group and role data."""
        self._group_role_cache.clear()
        self._role_topic_cache.clear()
    
    # Private helper methods
    
    def _get_group_roles(self, group):
        """Get roles assigned to a group (cached)."""
        if group not in self._group_role_cache:
            try:
                details = broker.get_group(group)
                self._group_role_cache[group] = parsers.parse_roles(details)
            except broker.MosquittoError:
                self._group_role_cache[group] = []
        
        return self._group_role_cache[group]
    
    def _get_role_topics(self, role):
        """Get topics accessible by a role (cached)."""
        if role not in self._role_topic_cache:
            try:
                details = broker.get_role(role)
                acls = parsers.parse_acls(details)
                self._role_topic_cache[role] = [
                    parsers.format_acl_for_display(acl) for acl in acls
                ]
            except broker.MosquittoError:
                self._role_topic_cache[role] = []
        
        return self._role_topic_cache[role]
