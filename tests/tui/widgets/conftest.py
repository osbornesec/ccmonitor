"""Shared fixtures and utilities for widget testing."""

from __future__ import annotations

# Import fixtures from integration directory to make them available
from tests.tui.integration.conftest import (
    AccessibilityTestHelper,
    NavigationTestBase,
    accessibility_helper,
    navigation_base,
)

# Re-export fixtures to make them available in widget tests
__all__ = [
    "AccessibilityTestHelper",
    "NavigationTestBase",
    "accessibility_helper",
    "navigation_base",
]
