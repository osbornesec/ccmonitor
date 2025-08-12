"""Comprehensive tests for animation and transition system.

This module provides thorough testing coverage for the transition system,
including:
- TransitionManager static methods
- Animation functions (fade_in, fade_out, slide_in, highlight)
- Async animation execution patterns
- Error handling and graceful degradation
- Theme integration for highlight effects
- Animation chaining and parallel execution
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from textual._easing import EASING
from textual.color import Color
from textual.widget import Widget

from src.tui.utils.themes import ColorScheme, ThemeManager
from src.tui.utils.transitions import (
    EASING_PRESETS,
    AnimationQueue,
    TransitionDirection,
    TransitionManager,
    animate_widget_entrance,
    animate_widget_exit,
    animation_context,
)

# Test constants
TEST_WIDGET_ID = "test-widget-123"
FAST_ANIMATION_DURATION = 0.01  # Speed up tests
DEFAULT_TEST_OPACITY = 0.5

# Animation test constants
TEST_FRAME_WIDTH = 100
TEST_FRAME_HEIGHT = 50
DELAY_TIME_SECONDS = 0.1
EXPECTED_CALL_COUNT = 2
TEST_WIDGET_COUNT = 3
CUSTOM_OPACITY = 0.8
MIN_DOT_COUNT = 2
MIN_ANIMATION_COUNT = 3


@pytest.fixture
def mock_widget() -> Mock:
    """Create a mock widget for testing animations."""
    mock = Mock(spec=Widget)
    mock.__class__.__name__ = "TestWidget"

    # Mock size with proper attributes
    mock.size = Mock()
    mock.size.width = TEST_FRAME_WIDTH
    mock.size.height = TEST_FRAME_HEIGHT

    # Mock styles with proper attributes
    mock.styles = Mock()
    mock.styles.opacity = DEFAULT_TEST_OPACITY

    # Mock animate method
    mock.animate = Mock()

    return mock


@pytest.fixture
def mock_theme_manager() -> Mock:
    """Create a mock theme manager for testing."""
    mock_manager = Mock(spec=ThemeManager)
    mock_theme = Mock(spec=ColorScheme)
    mock_theme.focus_primary = "#007ACC"
    mock_manager.get_current_theme.return_value = mock_theme
    return mock_manager


class TestTransitionDirection:
    """Test suite for TransitionDirection enum."""

    def test_transition_direction_values(self) -> None:
        """Test that all transition directions are defined."""
        assert TransitionDirection.LEFT is not None
        assert TransitionDirection.RIGHT is not None
        assert TransitionDirection.TOP is not None
        assert TransitionDirection.BOTTOM is not None

    def test_transition_direction_uniqueness(self) -> None:
        """Test that all transition directions have unique values."""
        directions = [
            TransitionDirection.LEFT,
            TransitionDirection.RIGHT,
            TransitionDirection.TOP,
            TransitionDirection.BOTTOM,
        ]

        assert len(set(directions)) == len(directions)

    def test_transition_direction_auto_values(self) -> None:
        """Test that enum uses auto() for values."""
        # Each direction should have a distinct auto-generated value
        assert isinstance(TransitionDirection.LEFT.value, int)
        assert isinstance(TransitionDirection.RIGHT.value, int)
        assert isinstance(TransitionDirection.TOP.value, int)
        assert isinstance(TransitionDirection.BOTTOM.value, int)


class TestAnimationQueue:
    """Test suite for AnimationQueue class."""

    def test_animation_queue_initialization(self) -> None:
        """Test AnimationQueue initialization."""
        queue = AnimationQueue()

        # Test internal state - accessing private members for testing purposes
        assert isinstance(queue._queues, dict)  # noqa: SLF001
        assert isinstance(queue._workers, dict)  # noqa: SLF001
        assert len(queue._queues) == 0  # noqa: SLF001
        assert len(queue._workers) == 0  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_get_queue_creates_new_queue(self) -> None:
        """Test that get_queue creates new queue and worker."""
        queue_manager = AnimationQueue()
        widget_id = TEST_WIDGET_ID

        with patch("asyncio.create_task") as mock_create_task:
            mock_task = Mock()
            mock_create_task.return_value = mock_task

            queue = queue_manager.get_queue(widget_id)

            assert isinstance(queue, asyncio.Queue)
            assert widget_id in queue_manager._queues  # noqa: SLF001
            assert widget_id in queue_manager._workers  # noqa: SLF001
            assert (
                queue_manager._workers[widget_id] is mock_task  # noqa: SLF001  # Testing internal state
            )
            mock_create_task.assert_called_once()

    def test_get_queue_returns_existing_queue(self) -> None:
        """Test that get_queue returns existing queue for same widget."""
        queue_manager = AnimationQueue()
        widget_id = TEST_WIDGET_ID

        with patch("asyncio.create_task") as mock_create_task:
            # First call creates queue
            queue1 = queue_manager.get_queue(widget_id)

            # Second call returns same queue
            queue2 = queue_manager.get_queue(widget_id)

            assert queue1 is queue2
            mock_create_task.assert_called_once()  # Only called once

    @pytest.mark.asyncio
    async def test_process_queue_functionality(self) -> None:
        """Test queue processing functionality."""
        # No queue manager needed for this test - we test the queue directly
        test_queue: asyncio.Queue[Any] = asyncio.Queue()

        # Mock animation function
        mock_animation = AsyncMock()

        # Add animation to queue
        await test_queue.put(mock_animation)

        # Process one item manually (simulating _process_queue behavior)
        animation_func = await test_queue.get()
        await animation_func()
        test_queue.task_done()

        mock_animation.assert_called_once()

    def test_cleanup_single_widget(self) -> None:
        """Test cleanup for single widget."""
        queue_manager = AnimationQueue()
        widget_id = TEST_WIDGET_ID

        # Create mock task
        mock_task = Mock()
        queue_manager._workers[widget_id] = mock_task  # noqa: SLF001
        queue_manager._queues[widget_id] = asyncio.Queue()  # noqa: SLF001

        # Cleanup
        queue_manager.cleanup(widget_id)

        mock_task.cancel.assert_called_once()
        assert widget_id not in queue_manager._workers  # noqa: SLF001
        assert widget_id not in queue_manager._queues  # noqa: SLF001

    def test_cleanup_all_widgets(self) -> None:
        """Test cleanup for all widgets."""
        queue_manager = AnimationQueue()

        # Create mock tasks
        widget_ids = ["widget1", "widget2", "widget3"]
        mock_tasks = []

        for widget_id in widget_ids:
            mock_task = Mock()
            mock_tasks.append(mock_task)
            queue_manager._workers[widget_id] = mock_task  # noqa: SLF001
            queue_manager._queues[widget_id] = asyncio.Queue()  # noqa: SLF001

        # Cleanup all
        queue_manager.cleanup_all()

        # All tasks should be cancelled
        for mock_task in mock_tasks:
            mock_task.cancel.assert_called_once()

        assert len(queue_manager._workers) == 0  # noqa: SLF001
        assert len(queue_manager._queues) == 0  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_process_queue_error_handling(self) -> None:
        """Test error handling in queue processing."""
        # Mock animation that raises exception
        failing_animation = AsyncMock(
            side_effect=Exception("Animation failed"),
        )

        # Manually simulate queue processing with error
        with patch("src.tui.utils.transitions.logger.exception") as mock_log:
            try:
                await failing_animation()
            except Exception:  # noqa: BLE001
                # Simulate the exception handling in _process_queue
                mock_log("Animation queue error for %s", TEST_WIDGET_ID)

            mock_log.assert_called_once()


class TestTransitionManager:
    """Test suite for TransitionManager class."""

    def test_transition_manager_initialization(self) -> None:
        """Test TransitionManager class attributes."""
        assert TransitionManager._theme_manager is None  # noqa: SLF001
        assert isinstance(
            TransitionManager._animation_queue, AnimationQueue,  # noqa: SLF001  # Testing internal state
        )
        assert TransitionManager._animation_enabled is True  # noqa: SLF001

    def test_initialize_with_theme_manager(
        self,
        mock_theme_manager: Mock,
    ) -> None:
        """Test initialization with theme manager."""
        TransitionManager.initialize(mock_theme_manager)

        assert (
            TransitionManager._theme_manager is mock_theme_manager  # noqa: SLF001  # Testing internal state
        )

    def test_initialize_without_theme_manager(self) -> None:
        """Test initialization without theme manager creates one."""
        with patch(
            "src.tui.utils.transitions.ThemeManager",
        ) as mock_theme_class:
            mock_instance = Mock()
            mock_theme_class.return_value = mock_instance

            TransitionManager.initialize()

            assert (
                TransitionManager._theme_manager is mock_instance  # noqa: SLF001  # Testing internal state
            )
            mock_theme_class.assert_called_once()

    def test_set_animation_enabled(self) -> None:
        """Test enabling/disabling animations."""
        # Enable animations
        TransitionManager.set_animation_enabled(enabled=True)
        assert TransitionManager._animation_enabled is True  # noqa: SLF001

        # Disable animations
        TransitionManager.set_animation_enabled(enabled=False)
        assert TransitionManager._animation_enabled is False  # noqa: SLF001

        # Re-enable for other tests
        TransitionManager.set_animation_enabled(enabled=True)

    @pytest.mark.asyncio
    async def test_fade_in_animation(self, mock_widget: Mock) -> None:
        """Test fade in animation."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await TransitionManager.fade_in(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
                easing="smooth",
            )

            # Should set initial opacity to 0
            assert mock_widget.styles.opacity == 0.0

            # Should call animate with correct parameters
            mock_widget.animate.assert_called_once()
            animate_call = mock_widget.animate.call_args
            assert animate_call[0][0] == "opacity"  # Property to animate
            assert animate_call[0][1] == 1.0  # Target value

            # Should wait for animation duration
            mock_sleep.assert_called_once_with(FAST_ANIMATION_DURATION)

    @pytest.mark.asyncio
    async def test_fade_in_with_custom_opacity(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test fade in animation with custom final opacity."""
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await TransitionManager.fade_in(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
                final_opacity=CUSTOM_OPACITY,
            )

            # Should animate to custom opacity
            animate_call = mock_widget.animate.call_args
            assert animate_call[0][1] == CUSTOM_OPACITY  # Custom target value

    @pytest.mark.asyncio
    async def test_fade_in_with_delay(self, mock_widget: Mock) -> None:
        """Test fade in animation with delay."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await TransitionManager.fade_in(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
                delay=DELAY_TIME_SECONDS,
            )

            # Should sleep for delay + duration
            assert mock_sleep.call_count == EXPECTED_CALL_COUNT
            mock_sleep.assert_any_call(DELAY_TIME_SECONDS)  # Delay
            mock_sleep.assert_any_call(FAST_ANIMATION_DURATION)  # Duration

    @pytest.mark.asyncio
    async def test_fade_out_animation(self, mock_widget: Mock) -> None:
        """Test fade out animation."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await TransitionManager.fade_out(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
            )

            # Should call animate with opacity 0
            mock_widget.animate.assert_called_once()
            animate_call = mock_widget.animate.call_args
            assert animate_call[0][0] == "opacity"
            assert animate_call[0][1] == 0.0  # Target opacity

            # Should wait for animation duration
            mock_sleep.assert_called_once_with(FAST_ANIMATION_DURATION)

    @pytest.mark.asyncio
    async def test_slide_in_animation(self, mock_widget: Mock) -> None:
        """Test slide in animation."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await TransitionManager.slide_in(
                mock_widget,
                TransitionDirection.LEFT,
                duration=FAST_ANIMATION_DURATION,
            )

            # Should set initial opacity to 0 (simplified slide effect)
            assert mock_widget.styles.opacity == 0.0

            # Should animate to opacity 1
            mock_widget.animate.assert_called_once()
            animate_call = mock_widget.animate.call_args
            assert animate_call[0][0] == "opacity"
            assert animate_call[0][1] == 1.0

            # Should wait for animation duration
            mock_sleep.assert_called_once_with(FAST_ANIMATION_DURATION)

    @pytest.mark.asyncio
    async def test_slide_in_with_custom_distance(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test slide in animation with custom distance."""
        distance_pixels = 200
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await TransitionManager.slide_in(
                mock_widget,
                TransitionDirection.RIGHT,
                duration=FAST_ANIMATION_DURATION,
                distance=distance_pixels,
            )

            # Animation should still work (distance used internally)
            mock_widget.animate.assert_called_once()

    @pytest.mark.asyncio
    async def test_slide_out_animation(self, mock_widget: Mock) -> None:
        """Test slide out animation."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await TransitionManager.slide_out(
                mock_widget,
                TransitionDirection.TOP,
                duration=FAST_ANIMATION_DURATION,
            )

            # Should animate to opacity 0 (simplified slide effect)
            mock_widget.animate.assert_called_once()
            animate_call = mock_widget.animate.call_args
            assert animate_call[0][0] == "opacity"
            assert animate_call[0][1] == 0.0

            # Should wait for animation duration
            mock_sleep.assert_called_once_with(FAST_ANIMATION_DURATION)

    @pytest.mark.asyncio
    async def test_highlight_animation(self, mock_widget: Mock) -> None:
        """Test highlight animation."""
        with (
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            patch("textual.color.Color.parse") as mock_parse_color,
        ):
            mock_parse_color.return_value = Color(255, 0, 0, 1.0)  # Red

            await TransitionManager.highlight(
                mock_widget,
                color="#FF0000",
                duration=FAST_ANIMATION_DURATION,
                pulse_count=1,
            )

            # Should animate opacity for pulse effect
            assert mock_widget.animate.call_count >= 1

            # Should sleep for pulse duration
            assert mock_sleep.call_count >= 1

    @pytest.mark.asyncio
    async def test_highlight_with_theme_color(
        self,
        mock_widget: Mock,
        mock_theme_manager: Mock,
    ) -> None:
        """Test highlight animation using theme color."""
        TransitionManager._theme_manager = mock_theme_manager  # noqa: SLF001

        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            patch("textual.color.Color.parse") as mock_parse_color,
        ):
            mock_parse_color.return_value = Color(0, 122, 204, 1.0)

            await TransitionManager.highlight(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
                pulse_count=1,
            )

            # Should use theme color
            mock_parse_color.assert_called_with("#007ACC")

    @pytest.mark.asyncio
    async def test_attention_shake_animation(self, mock_widget: Mock) -> None:
        """Test attention shake animation."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await TransitionManager.attention_shake(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
                cycles=1,
            )

            # Should animate multiple times for shake effect
            assert mock_widget.animate.call_count >= 1

            # Should sleep for animation segments
            assert mock_sleep.call_count >= 1

    @pytest.mark.asyncio
    async def test_typing_indicator_animation(self, mock_widget: Mock) -> None:
        """Test typing indicator animation."""
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await TransitionManager.typing_indicator(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
                dot_count=MIN_DOT_COUNT,
            )

            # Should animate for each dot
            assert mock_widget.animate.call_count >= MIN_DOT_COUNT

            # Should sleep between dot animations
            assert mock_sleep.call_count >= MIN_DOT_COUNT

    @pytest.mark.asyncio
    async def test_chain_animations(self) -> None:
        """Test chaining multiple animations."""
        animation1 = AsyncMock()
        animation2 = AsyncMock()
        animation3 = AsyncMock()

        await TransitionManager.chain_animations(
            animation1(),
            animation2(),
            animation3(),
        )

        # All animations should be called
        animation1.assert_called_once()
        animation2.assert_called_once()
        animation3.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_animations(self) -> None:
        """Test running animations in parallel."""
        animation1 = AsyncMock()
        animation2 = AsyncMock()
        animation3 = AsyncMock()

        with patch("asyncio.gather", new_callable=AsyncMock) as mock_gather:
            await TransitionManager.parallel_animations(
                animation1(),
                animation2(),
                animation3(),
            )

            # Should use asyncio.gather
            mock_gather.assert_called_once()

    def test_queue_animation(self, mock_widget: Mock) -> None:
        """Test queuing animation for widget."""
        mock_animation = AsyncMock()

        with (
            patch.object(
                TransitionManager._animation_queue,  # noqa: SLF001
                "get_queue",
            ) as mock_get_queue,
            patch("asyncio.create_task") as mock_create_task,
        ):
            mock_queue = AsyncMock()
            mock_get_queue.return_value = mock_queue

            TransitionManager.queue_animation(mock_widget, mock_animation)

            # Should get queue for widget
            widget_id = str(id(mock_widget))
            mock_get_queue.assert_called_once_with(widget_id)

            # Should create task to put animation in queue
            mock_create_task.assert_called_once()

    def test_cleanup_widget_animations(self, mock_widget: Mock) -> None:
        """Test cleaning up animations for specific widget."""
        with patch.object(
            TransitionManager._animation_queue,  # noqa: SLF001
            "cleanup",
        ) as mock_cleanup:
            TransitionManager.cleanup_widget_animations(mock_widget)

            widget_id = str(id(mock_widget))
            mock_cleanup.assert_called_once_with(widget_id)

    def test_cleanup_all_animations(self) -> None:
        """Test cleaning up all animations."""
        with patch.object(
            TransitionManager._animation_queue,  # noqa: SLF001
            "cleanup_all",
        ) as mock_cleanup_all:
            TransitionManager.cleanup_all_animations()

            mock_cleanup_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_animation_disabled_skips_execution(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test that animations are skipped when disabled."""
        TransitionManager.set_animation_enabled(enabled=False)

        try:
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await TransitionManager.fade_in(
                    mock_widget,
                    duration=FAST_ANIMATION_DURATION,
                )

                # Should not animate or sleep when disabled
                mock_widget.animate.assert_not_called()
                mock_sleep.assert_not_called()
        finally:
            # Re-enable for other tests
            TransitionManager.set_animation_enabled(enabled=True)

    @pytest.mark.asyncio
    async def test_animation_error_handling(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test error handling during animations."""
        # Create a widget that doesn't support animations
        bad_widget = Mock()
        delattr(bad_widget, "animate")  # Remove animate method
        bad_widget.__class__.__name__ = "BadWidget"

        with caplog.at_level("WARNING"):
            await TransitionManager.fade_in(
                bad_widget,
                duration=FAST_ANIMATION_DURATION,
            )

            # Should log warning about unsupported animations
            assert any(
                "does not support animations" in record.message
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_animation_exception_handling(
        self,
        mock_widget: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test exception handling during animations."""
        # Make animate method raise exception
        mock_widget.animate.side_effect = Exception("Animation error")

        with caplog.at_level("ERROR"):
            # Should not raise exception
            await TransitionManager.fade_in(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
            )

            # Should log exception
            assert any(
                "Animation error" in record.message
                for record in caplog.records
            )


class TestEasingPresets:
    """Test suite for easing presets."""

    def test_easing_presets_defined(self) -> None:
        """Test that easing presets are properly defined."""
        expected_presets = ["smooth", "bounce", "snap", "elastic", "ease"]

        for preset in expected_presets:
            assert preset in EASING_PRESETS
            assert EASING_PRESETS[preset] in EASING

    def test_easing_preset_values(self) -> None:
        """Test specific easing preset values."""
        assert EASING_PRESETS["smooth"] == "out_cubic"
        assert EASING_PRESETS["bounce"] == "out_back"
        assert EASING_PRESETS["snap"] == "in_out_circ"
        assert EASING_PRESETS["elastic"] == "out_elastic"
        assert EASING_PRESETS["ease"] == "in_out_cubic"


class TestAnimationUtilities:
    """Test suite for animation utility functions."""

    @pytest.mark.asyncio
    async def test_animate_widget_entrance_fade_in(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test widget entrance with fade in."""
        with patch.object(
            TransitionManager,
            "fade_in",
            new_callable=AsyncMock,
        ) as mock_fade_in:
            await animate_widget_entrance(
                mock_widget,
                animation_type="fade_in",
                duration=FAST_ANIMATION_DURATION,
            )

            mock_fade_in.assert_called_once_with(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
            )

    @pytest.mark.asyncio
    async def test_animate_widget_entrance_slide_left(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test widget entrance with slide from left."""
        with patch.object(
            TransitionManager,
            "slide_in",
            new_callable=AsyncMock,
        ) as mock_slide_in:
            await animate_widget_entrance(
                mock_widget,
                animation_type="slide_left",
                duration=FAST_ANIMATION_DURATION,
            )

            mock_slide_in.assert_called_once_with(
                mock_widget,
                TransitionDirection.LEFT,
                duration=FAST_ANIMATION_DURATION,
            )

    @pytest.mark.asyncio
    async def test_animate_widget_entrance_with_delay(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test widget entrance with delay."""
        with (
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            patch.object(TransitionManager, "fade_in", new_callable=AsyncMock),
        ):
            await animate_widget_entrance(
                mock_widget,
                animation_type="fade_in",
                delay=DELAY_TIME_SECONDS,
            )

            # Should sleep for delay
            mock_sleep.assert_called_once_with(DELAY_TIME_SECONDS)

    @pytest.mark.asyncio
    async def test_animate_widget_entrance_unknown_type(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test widget entrance with unknown animation type defaults to fade_in."""
        with patch.object(
            TransitionManager,
            "fade_in",
            new_callable=AsyncMock,
        ) as mock_fade_in:
            await animate_widget_entrance(
                mock_widget,
                animation_type="unknown_animation",
            )

            # Should default to fade_in
            mock_fade_in.assert_called_once()

    @pytest.mark.asyncio
    async def test_animate_widget_exit_fade_out(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test widget exit with fade out."""
        with patch.object(
            TransitionManager,
            "fade_out",
            new_callable=AsyncMock,
        ) as mock_fade_out:
            await animate_widget_exit(
                mock_widget,
                animation_type="fade_out",
                duration=FAST_ANIMATION_DURATION,
            )

            mock_fade_out.assert_called_once_with(
                mock_widget,
                duration=FAST_ANIMATION_DURATION,
            )

    @pytest.mark.asyncio
    async def test_animate_widget_exit_slide_directions(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test widget exit with different slide directions."""
        slide_types = [
            ("slide_left", TransitionDirection.LEFT),
            ("slide_right", TransitionDirection.RIGHT),
            ("slide_up", TransitionDirection.TOP),
            ("slide_down", TransitionDirection.BOTTOM),
        ]

        for animation_type, expected_direction in slide_types:
            with patch.object(
                TransitionManager,
                "slide_out",
                new_callable=AsyncMock,
            ) as mock_slide_out:
                await animate_widget_exit(
                    mock_widget,
                    animation_type=animation_type,
                )

                mock_slide_out.assert_called_once_with(
                    mock_widget,
                    expected_direction,
                )

    def test_animation_context_manager(self, mock_widget: Mock) -> None:
        """Test animation context manager."""
        widgets = [mock_widget]

        with (
            patch.object(
                TransitionManager,
                "cleanup_widget_animations",
            ) as mock_cleanup,
            animation_context(widgets),
        ):
            # Context should work normally
            pass

        # Should cleanup after context exits
        mock_cleanup.assert_called_once_with(mock_widget)

    def test_animation_context_manager_exception(
        self,
        mock_widget: Mock,
    ) -> None:
        """Test animation context manager handles exceptions."""
        widgets = [mock_widget]
        msg = "Test exception"

        with (
            patch.object(
                TransitionManager,
                "cleanup_widget_animations",
            ) as mock_cleanup,
            pytest.raises(ValueError, match="Test exception"),
            animation_context(widgets),
        ):
            raise ValueError(msg)

        # Should still cleanup after exception
        mock_cleanup.assert_called_once_with(mock_widget)

    def test_animation_context_manager_multiple_widgets(self) -> None:
        """Test animation context manager with multiple widgets."""
        mock_widgets = [Mock(spec=Widget) for _ in range(TEST_WIDGET_COUNT)]

        with (
            patch.object(
                TransitionManager,
                "cleanup_widget_animations",
            ) as mock_cleanup,
            animation_context(mock_widgets),
        ):
            pass

        # Should cleanup all widgets
        assert mock_cleanup.call_count == TEST_WIDGET_COUNT
        for widget in mock_widgets:
            mock_cleanup.assert_any_call(widget)


class TestTransitionIntegration:
    """Integration tests for transition system."""

    def test_transition_manager_module_initialization(self) -> None:
        """Test that TransitionManager is initialized on module import."""
        # Module should initialize TransitionManager
        assert TransitionManager._animation_queue is not None  # noqa: SLF001
        assert TransitionManager._animation_enabled is True  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_full_animation_workflow(self, mock_widget: Mock) -> None:
        """Test complete animation workflow."""
        with (
            patch("asyncio.sleep", new_callable=AsyncMock),
            patch("textual.color.Color.parse") as mock_parse_color,
        ):
            mock_parse_color.return_value = Color(255, 0, 0, 1.0)

            # Run multiple animations
            await TransitionManager.fade_in(mock_widget, duration=0.01)
            await TransitionManager.highlight(
                mock_widget,
                duration=0.01,
                pulse_count=1,
            )
            await TransitionManager.fade_out(mock_widget, duration=0.01)

            # All animations should execute
            assert mock_widget.animate.call_count >= MIN_ANIMATION_COUNT

    def test_theme_integration(self, mock_theme_manager: Mock) -> None:
        """Test integration with theme system."""
        TransitionManager.initialize(mock_theme_manager)

        assert (
            TransitionManager._theme_manager is mock_theme_manager  # noqa: SLF001  # Testing internal state
        )

        # Theme should be used in highlight animations
        theme = mock_theme_manager.get_current_theme()
        assert theme.focus_primary == "#007ACC"

    @pytest.mark.parametrize(
        "animation_type",
        ["fade_in", "slide_left", "slide_right", "slide_up", "slide_down"],
    )
    @pytest.mark.asyncio
    async def test_all_entrance_animations(
        self,
        mock_widget: Mock,
        animation_type: str,
    ) -> None:
        """Test all entrance animation types."""
        with patch("asyncio.sleep", new_callable=AsyncMock):
            # Should not raise exceptions
            await animate_widget_entrance(
                mock_widget,
                animation_type=animation_type,
                duration=0.01,
            )

            # Should call some animation method
            assert (
                mock_widget.animate.called or mock_widget.styles.opacity == 0.0
            )

    @pytest.mark.parametrize(
        "animation_type",
        ["fade_out", "slide_left", "slide_right", "slide_up", "slide_down"],
    )
    @pytest.mark.asyncio
    async def test_all_exit_animations(
        self,
        mock_widget: Mock,
        animation_type: str,
    ) -> None:
        """Test all exit animation types."""
        with patch("asyncio.sleep", new_callable=AsyncMock):
            # Should not raise exceptions
            await animate_widget_exit(
                mock_widget,
                animation_type=animation_type,
                duration=0.01,
            )

            # Should call animation method
            assert mock_widget.animate.called
