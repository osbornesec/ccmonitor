"""Search highlighting utilities for CCMonitor TUI application."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.style import Style
from rich.text import Text

if TYPE_CHECKING:
    from src.tui.utils.filter_state import SearchConfig


class SearchHighlighter:
    """Highlighter for search results in text content."""

    def __init__(self) -> None:
        """Initialize search highlighter."""
        self.highlight_style = Style(
            bgcolor="yellow", color="black", bold=True,
        )
        self.console = Console()
        self.repr_highlighter = ReprHighlighter()
        self._compiled_regex: re.Pattern[str] | None = None
        self._last_query = ""
        self._last_case_sensitive = False

    def highlight_text(
        self,
        text: str,
        search_config: SearchConfig,
        max_length: int = 200,
    ) -> Text:
        """Highlight search terms in text and return Rich Text object."""
        if not search_config.query:
            return Text(
                text[:max_length] + ("..." if len(text) > max_length else ""),
            )

        # Truncate text if necessary
        display_text = text[:max_length] + (
            "..." if len(text) > max_length else ""
        )

        if search_config.use_regex:
            return self._highlight_regex_matches(display_text, search_config)
        return self._highlight_literal_matches(display_text, search_config)

    def _highlight_regex_matches(
        self,
        text: str,
        search_config: SearchConfig,
    ) -> Text:
        """Highlight regex pattern matches in text."""
        try:
            if (
                self._compiled_regex is None
                or search_config.query != self._last_query
                or search_config.case_sensitive != self._last_case_sensitive
            ):
                flags = 0 if search_config.case_sensitive else re.IGNORECASE
                self._compiled_regex = re.compile(search_config.query, flags)
                self._last_query = search_config.query
                self._last_case_sensitive = search_config.case_sensitive

            return self._apply_regex_highlighting(text, self._compiled_regex)
        except re.error:
            # Invalid regex, return plain text
            return Text(text)

    def _apply_regex_highlighting(
        self,
        text: str,
        regex_pattern: re.Pattern[str],
    ) -> Text:
        """Apply regex highlighting to text."""
        result = Text()
        last_end = 0

        for match in regex_pattern.finditer(text):
            # Add text before match
            result.append(text[last_end : match.start()])
            # Add highlighted match
            result.append(match.group(), style=self.highlight_style)
            last_end = match.end()

        # Add remaining text
        result.append(text[last_end:])
        return result

    def _highlight_literal_matches(
        self,
        text: str,
        search_config: SearchConfig,
    ) -> Text:
        """Highlight literal string matches in text."""
        if search_config.case_sensitive:
            search_text = text
            query = search_config.query
        else:
            search_text = text.lower()
            query = search_config.query.lower()

        result = Text()
        start_pos = 0

        while True:
            match_pos = search_text.find(query, start_pos)
            if match_pos == -1:
                # No more matches, add remaining text
                result.append(text[start_pos:])
                break

            # Add text before match
            result.append(text[start_pos:match_pos])
            # Add highlighted match (preserve original case)
            match_end = match_pos + len(query)
            result.append(
                text[match_pos:match_end], style=self.highlight_style,
            )
            start_pos = match_end

        return result

    def extract_search_snippet(
        self,
        text: str,
        search_config: SearchConfig,
        snippet_length: int = 150,
        context_chars: int = 30,
    ) -> Text:
        """Extract a snippet around the first search match."""
        if not search_config.query:
            return Text(text[:snippet_length])

        # Find first match position
        match_pos = self._find_first_match_position(text, search_config)
        if match_pos == -1:
            # No match found, return beginning of text
            return Text(text[:snippet_length])

        # Calculate snippet boundaries
        start_pos = max(0, match_pos - context_chars)
        end_pos = min(
            len(text), match_pos + len(search_config.query) + context_chars,
        )

        # Adjust to fit within snippet_length
        if end_pos - start_pos > snippet_length:
            end_pos = start_pos + snippet_length

        snippet_text = text[start_pos:end_pos]

        # Add ellipsis indicators
        if start_pos > 0:
            snippet_text = "..." + snippet_text
        if end_pos < len(text):
            snippet_text = snippet_text + "..."

        # Apply highlighting to the snippet
        return self.highlight_text(
            snippet_text, search_config, len(snippet_text) + 10,
        )

    def _find_first_match_position(
        self,
        text: str,
        search_config: SearchConfig,
    ) -> int:
        """Find the position of the first search match."""
        if search_config.use_regex:
            try:
                flags = 0 if search_config.case_sensitive else re.IGNORECASE
                pattern = re.compile(search_config.query, flags)
                match = pattern.search(text)
                return match.start() if match else -1
            except re.error:
                return -1
        else:
            search_text = (
                text if search_config.case_sensitive else text.lower()
            )
            query = (
                search_config.query
                if search_config.case_sensitive
                else search_config.query.lower()
            )
            return search_text.find(query)

    def get_match_count(self, text: str, search_config: SearchConfig) -> int:
        """Get the number of matches in the text."""
        if not search_config.query:
            return 0

        if search_config.use_regex:
            try:
                flags = 0 if search_config.case_sensitive else re.IGNORECASE
                pattern = re.compile(search_config.query, flags)
                return len(pattern.findall(text))
            except re.error:
                return 0
        else:
            search_text = (
                text if search_config.case_sensitive else text.lower()
            )
            query = (
                search_config.query
                if search_config.case_sensitive
                else search_config.query.lower()
            )

            count = 0
            start_pos = 0
            while True:
                pos = search_text.find(query, start_pos)
                if pos == -1:
                    break
                count += 1
                start_pos = pos + 1
            return count


# Global highlighter instance
search_highlighter = SearchHighlighter()


def highlight_search_in_content(
    content: str,
    search_query: str = "",
    use_regex: bool = False,
    case_sensitive: bool = False,
    max_length: int = 200,
) -> Text:
    """Convenience function to highlight search terms in content."""
    from src.tui.utils.filter_state import SearchConfig

    if not search_query:
        return Text(
            content[:max_length] + ("..." if len(content) > max_length else ""),
        )

    search_config = SearchConfig(
        query=search_query,
        use_regex=use_regex,
        case_sensitive=case_sensitive,
    )

    return search_highlighter.highlight_text(
        content, search_config, max_length,
    )


def extract_search_snippet_from_content(
    content: str,
    search_query: str = "",
    use_regex: bool = False,
    case_sensitive: bool = False,
    snippet_length: int = 150,
) -> Text:
    """Convenience function to extract search snippet from content."""
    from src.tui.utils.filter_state import SearchConfig

    if not search_query:
        return Text(content[:snippet_length])

    search_config = SearchConfig(
        query=search_query,
        use_regex=use_regex,
        case_sensitive=case_sensitive,
    )

    return search_highlighter.extract_search_snippet(
        content, search_config, snippet_length,
    )
