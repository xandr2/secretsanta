"""Utility functions for the Secret Santa application."""

import secrets
import string


def generate_invite_code() -> str:
    """Generate a 6-character invite code.

    Returns:
        str: Invite code in format "XXX-XX" (e.g., "X7K-9P")
    """
    chars = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(chars) for _ in range(6))
    return f"{code[:3]}-{code[3:]}"

