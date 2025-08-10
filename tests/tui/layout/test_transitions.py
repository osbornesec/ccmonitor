"""Tests for UI transition animation system."""

from __future__ import annotations

from src.tui.utils.transitions import TransitionManager


class TestTransitionManager:
    """Test TransitionManager functionality."""

    def test_initialization(self) -> None:
        """Test transition manager initialization."""
        manager = TransitionManager()
        assert manager.animation_enabled is True

    def test_set_animation_enabled(self) -> None:
        """Test enabling/disabling animations."""
        manager = TransitionManager()

        # Test disabling animations
        manager.set_animation_enabled(enabled=False)
        assert manager.animation_enabled is False

        # Test enabling animations
        manager.set_animation_enabled(enabled=True)
        assert manager.animation_enabled is True

    def test_fade_in_with_animations_enabled(self) -> None:
        """Test fade-in animation when animations are enabled."""
        manager = TransitionManager()
        manager.set_animation_enabled(enabled=True)

        # Should not raise exception (placeholder implementation)
        manager.fade_in("test-widget")
        manager.fade_in("test-widget", duration=0.5)

    def test_fade_in_with_animations_disabled(self) -> None:
        """Test fade-in animation when animations are disabled."""
        manager = TransitionManager()
        manager.set_animation_enabled(enabled=False)

        # Should not raise exception and should return early
        manager.fade_in("test-widget")
        manager.fade_in("test-widget", duration=0.5)

    def test_fade_out_with_animations_enabled(self) -> None:
        """Test fade-out animation when animations are enabled."""
        manager = TransitionManager()
        manager.set_animation_enabled(enabled=True)

        # Should not raise exception (placeholder implementation)
        manager.fade_out("test-widget")
        manager.fade_out("test-widget", duration=0.5)

    def test_fade_out_with_animations_disabled(self) -> None:
        """Test fade-out animation when animations are disabled."""
        manager = TransitionManager()
        manager.set_animation_enabled(enabled=False)

        # Should not raise exception and should return early
        manager.fade_out("test-widget")
        manager.fade_out("test-widget", duration=0.5)

    def test_default_duration_values(self) -> None:
        """Test that default duration values are used correctly."""
        manager = TransitionManager()

        # Test with default duration (should be 0.3)
        manager.fade_in("test-widget")
        manager.fade_out("test-widget")

        # Test with custom duration
        manager.fade_in("test-widget", duration=1.0)
        manager.fade_out("test-widget", duration=1.0)

    def test_animation_state_persistence(self) -> None:
        """Test that animation state persists across method calls."""
        manager = TransitionManager()

        # Disable animations
        manager.set_animation_enabled(enabled=False)
        assert manager.animation_enabled is False

        # Call animation methods - should still be disabled
        manager.fade_in("widget1")
        manager.fade_out("widget2")
        assert manager.animation_enabled is False

        # Re-enable animations
        manager.set_animation_enabled(enabled=True)
        assert manager.animation_enabled is True


class TestTransitionEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_widget_id(self) -> None:
        """Test animation methods with empty widget ID."""
        manager = TransitionManager()

        # Should not raise exception with empty string
        manager.fade_in("")
        manager.fade_out("")

    def test_zero_duration(self) -> None:
        """Test animation methods with zero duration."""
        manager = TransitionManager()

        # Should not raise exception with zero duration
        manager.fade_in("test-widget", duration=0.0)
        manager.fade_out("test-widget", duration=0.0)

    def test_negative_duration(self) -> None:
        """Test animation methods with negative duration."""
        manager = TransitionManager()

        # Should not raise exception with negative duration
        manager.fade_in("test-widget", duration=-1.0)
        manager.fade_out("test-widget", duration=-1.0)

    def test_very_long_duration(self) -> None:
        """Test animation methods with very long duration."""
        manager = TransitionManager()

        # Should not raise exception with long duration
        long_duration = 999999.0
        manager.fade_in("test-widget", duration=long_duration)
        manager.fade_out("test-widget", duration=long_duration)

    def test_multiple_manager_instances(self) -> None:
        """Test that multiple manager instances are independent."""
        manager1 = TransitionManager()
        manager2 = TransitionManager()

        # Change state of first manager
        manager1.set_animation_enabled(enabled=False)

        # Second manager should still have default state
        assert manager1.animation_enabled is False
        assert manager2.animation_enabled is True

        # Change state of second manager
        manager2.set_animation_enabled(enabled=False)

        # Both should now be disabled
        assert manager1.animation_enabled is False
        assert manager2.animation_enabled is False
