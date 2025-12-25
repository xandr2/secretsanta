"""Tests for utility functions.

This module tests helper functions like invite code generation.
"""

import pytest

from app.utils import generate_invite_code


def test_generate_invite_code_format():
    """Test invite code format is correct."""
    code = generate_invite_code()
    
    # Should be in format XXX-XX (7 characters total: 3 + dash + 2)
    assert len(code) == 7
    assert code[3] == "-"
    assert code[:3].isalnum()
    assert code[4:].isalnum()


def test_generate_invite_code_uniqueness():
    """Test invite codes are unique."""
    codes = [generate_invite_code() for _ in range(100)]
    assert len(codes) == len(set(codes))  # All unique


def test_generate_invite_code_uppercase():
    """Test invite codes use uppercase."""
    code = generate_invite_code()
    assert code.isupper() or any(c.isupper() for c in code)

