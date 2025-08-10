"""Tests for key binding management system."""

from __future__ import annotations

from src.tui.utils.keybindings import KeyBindingManager

# Test constants
EXPECTED_THREE_BINDINGS = 3
EXPECTED_TWO_BINDINGS = 2
LARGE_BINDING_COUNT = 1000
HUNDRED_CHAR_REPEAT = 100


class TestKeyBindingManager:
    """Test KeyBindingManager functionality."""

    def test_initialization(self) -> None:
        """Test key binding manager initialization."""
        manager = KeyBindingManager()
        assert isinstance(manager.bindings, dict)
        assert len(manager.bindings) == 0

    def test_register_binding(self) -> None:
        """Test registering key bindings."""
        manager = KeyBindingManager()

        # Register single binding
        manager.register_binding("q", "quit")
        assert manager.bindings["q"] == "quit"

        # Register multiple bindings
        manager.register_binding("h", "help")
        manager.register_binding("r", "refresh")

        assert len(manager.bindings) == EXPECTED_THREE_BINDINGS
        assert manager.bindings["h"] == "help"
        assert manager.bindings["r"] == "refresh"

    def test_register_binding_overwrites(self) -> None:
        """Test that registering same key overwrites previous binding."""
        manager = KeyBindingManager()

        # Register initial binding
        manager.register_binding("q", "quit")
        assert manager.bindings["q"] == "quit"

        # Overwrite with new action
        manager.register_binding("q", "exit")
        assert manager.bindings["q"] == "exit"
        assert len(manager.bindings) == 1

    def test_get_action_existing_key(self) -> None:
        """Test getting action for existing key."""
        manager = KeyBindingManager()
        manager.register_binding("q", "quit")
        manager.register_binding("ctrl+c", "force_quit")

        assert manager.get_action("q") == "quit"
        assert manager.get_action("ctrl+c") == "force_quit"

    def test_get_action_nonexistent_key(self) -> None:
        """Test getting action for non-existent key."""
        manager = KeyBindingManager()
        manager.register_binding("q", "quit")

        # Should return None for unregistered keys
        assert manager.get_action("x") is None
        assert manager.get_action("unknown") is None
        assert manager.get_action("") is None

    def test_complex_key_combinations(self) -> None:
        """Test registering complex key combinations."""
        manager = KeyBindingManager()

        # Register various key combinations
        manager.register_binding("ctrl+q", "quit")
        manager.register_binding("shift+tab", "focus_previous")
        manager.register_binding("alt+f4", "close_window")
        manager.register_binding("escape", "cancel")

        assert manager.get_action("ctrl+q") == "quit"
        assert manager.get_action("shift+tab") == "focus_previous"
        assert manager.get_action("alt+f4") == "close_window"
        assert manager.get_action("escape") == "cancel"

    def test_case_sensitivity(self) -> None:
        """Test that key bindings are case sensitive."""
        manager = KeyBindingManager()

        manager.register_binding("Q", "quit")
        manager.register_binding("q", "query")

        assert manager.get_action("Q") == "quit"
        assert manager.get_action("q") == "query"
        assert len(manager.bindings) == EXPECTED_TWO_BINDINGS

    def test_empty_key_and_action(self) -> None:
        """Test registering empty key and action."""
        manager = KeyBindingManager()

        # Should handle empty strings without error
        manager.register_binding("", "empty_key")
        manager.register_binding("x", "")

        assert manager.get_action("") == "empty_key"
        assert manager.get_action("x") == ""

    def test_special_characters(self) -> None:
        """Test registering keys with special characters."""
        manager = KeyBindingManager()

        # Register keys with special characters
        manager.register_binding("ctrl+/", "search")
        manager.register_binding("shift+?", "help")
        manager.register_binding("ctrl+shift+!", "urgent")

        assert manager.get_action("ctrl+/") == "search"
        assert manager.get_action("shift+?") == "help"
        assert manager.get_action("ctrl+shift+!") == "urgent"


class TestKeyBindingEdgeCases:
    """Test edge cases and error conditions."""

    def test_multiple_managers_independence(self) -> None:
        """Test that multiple managers are independent."""
        manager1 = KeyBindingManager()
        manager2 = KeyBindingManager()

        # Register different bindings
        manager1.register_binding("q", "quit1")
        manager2.register_binding("q", "quit2")

        # Should be independent
        assert manager1.get_action("q") == "quit1"
        assert manager2.get_action("q") == "quit2"
        assert len(manager1.bindings) == 1
        assert len(manager2.bindings) == 1

    def test_large_number_of_bindings(self) -> None:
        """Test registering large number of bindings."""
        manager = KeyBindingManager()

        # Register many bindings
        for i in range(LARGE_BINDING_COUNT):
            manager.register_binding(f"key{i}", f"action{i}")

        assert len(manager.bindings) == LARGE_BINDING_COUNT

        # Test some random bindings
        assert manager.get_action("key0") == "action0"
        assert manager.get_action("key500") == "action500"
        assert manager.get_action("key999") == "action999"

    def test_unicode_keys_and_actions(self) -> None:
        """Test registering Unicode keys and actions."""
        manager = KeyBindingManager()

        # Register Unicode keys and actions
        manager.register_binding("ü", "umlaut")
        manager.register_binding("ctrl+a", "alpha")
        manager.register_binding("shift+🎯", "target")
        manager.register_binding("esc", "выход")  # Russian "exit"

        assert manager.get_action("ü") == "umlaut"
        assert manager.get_action("ctrl+a") == "alpha"
        assert manager.get_action("shift+🎯") == "target"
        assert manager.get_action("esc") == "выход"

    def test_very_long_keys_and_actions(self) -> None:
        """Test registering very long keys and actions."""
        manager = KeyBindingManager()

        long_key = "ctrl+shift+alt+super+meta+" + "x" * HUNDRED_CHAR_REPEAT
        long_action = "very_long_action_name_" + "y" * HUNDRED_CHAR_REPEAT

        manager.register_binding(long_key, long_action)
        assert manager.get_action(long_key) == long_action

    def test_whitespace_handling(self) -> None:
        """Test handling of whitespace in keys and actions."""
        manager = KeyBindingManager()

        # Register keys/actions with whitespace
        manager.register_binding(" ", "space")
        manager.register_binding("tab", "tab action")
        manager.register_binding("key with spaces", "action")
        manager.register_binding("trailing_space ", "action")
        manager.register_binding(" leading_space", "action")

        assert manager.get_action(" ") == "space"
        assert manager.get_action("tab") == "tab action"
        assert manager.get_action("key with spaces") == "action"
        assert manager.get_action("trailing_space ") == "action"
        assert manager.get_action(" leading_space") == "action"

    def test_bindings_persistence(self) -> None:
        """Test that bindings persist across operations."""
        manager = KeyBindingManager()

        # Register initial bindings
        manager.register_binding("q", "quit")
        manager.register_binding("h", "help")

        # Get some actions
        assert manager.get_action("q") == "quit"
        assert manager.get_action("nonexistent") is None

        # Bindings should still exist
        assert len(manager.bindings) == EXPECTED_TWO_BINDINGS
        assert manager.get_action("h") == "help"

        # Add more bindings
        manager.register_binding("r", "refresh")

        # All should still work
        assert manager.get_action("q") == "quit"
        assert manager.get_action("h") == "help"
        assert manager.get_action("r") == "refresh"

    def test_modification_after_creation(self) -> None:
        """Test that bindings dictionary can be modified after creation."""
        manager = KeyBindingManager()

        # Initial state
        assert len(manager.bindings) == 0

        # Direct modification (though not recommended in practice)
        manager.bindings["direct"] = "modified"
        assert manager.get_action("direct") == "modified"

        # Normal registration should still work
        manager.register_binding("normal", "action")
        assert manager.get_action("normal") == "action"

        # Both should exist
        assert len(manager.bindings) == EXPECTED_TWO_BINDINGS
