"""Database management commands for CCMonitor."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click
from sqlalchemy.exc import SQLAlchemyError

from src.services.database import DatabaseManager
from src.services.jsonl_parser import (
    JSONLParseError,
    JSONLParser,
    find_claude_activity_files,
)


@click.group()
def db() -> None:
    """Database management commands."""


@db.command()
@click.option(
    "--database-url",
    default="sqlite:///ccmonitor.db",
    help="Database URL (default: sqlite:///ccmonitor.db)",
)
def init(database_url: str) -> None:
    """Initialize the database."""
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    click.echo("Database initialized successfully.")


@db.command()
@click.option(
    "--database-url",
    default="sqlite:///ccmonitor.db",
    help="Database URL",
)
@click.option(
    "--claude-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Claude projects directory (default: ~/.claude/projects)",
)
def import_data(database_url: str, claude_dir: Path | None) -> None:
    """Import JSONL files into the database."""
    asyncio.run(_import_data_async(database_url, claude_dir))


async def _import_data_async(
    database_url: str,
    claude_dir: Path | None,
) -> None:
    """Async import implementation."""
    if claude_dir is None:
        claude_dir = Path.home() / ".claude" / "projects"

    if not claude_dir.exists():
        click.echo(f"Error: Claude projects directory not found: {claude_dir}")
        return

    db_manager = DatabaseManager(database_url)
    parser = JSONLParser(file_age_limit_hours=168)  # 7 days

    # Find JSONL files
    jsonl_files = find_claude_activity_files(
        claude_projects_dir=claude_dir,
        file_pattern="*.jsonl",
    )

    click.echo(f"Found {len(jsonl_files)} JSONL files")

    total_entries = 0
    processed_files = 0

    with click.progressbar(jsonl_files, label="Importing files") as bar:
        for file_path in bar:
            if db_manager.needs_parsing(file_path):
                try:
                    result = parser.parse_file(file_path)
                    count = db_manager.store_entries(
                        result.entries,
                        file_path,
                        result,
                    )
                    total_entries += count
                    processed_files += 1
                except (
                    JSONLParseError,
                    json.JSONDecodeError,
                    FileNotFoundError,
                    PermissionError,
                ) as e:
                    # Handle parsing and file access errors - continue processing other files
                    click.echo(f"Parse error processing {file_path}: {e}")
                except (
                    SQLAlchemyError,
                    OSError,
                ) as e:
                    # Handle database and critical system errors - continue processing other files
                    click.echo(f"Database error processing {file_path}: {e}")

    click.echo("Import complete:")
    click.echo(f"  Files processed: {processed_files}")
    click.echo(f"  Total entries: {total_entries}")


@db.command()
@click.option(
    "--database-url",
    default="sqlite:///ccmonitor.db",
    help="Database URL",
)
def stats(database_url: str) -> None:
    """Show database statistics."""
    db_manager = DatabaseManager(database_url)

    with db_manager.get_session() as session:
        projects = db_manager.get_projects(session)

        if not projects:
            click.echo("No projects found in database.")
            return

        total_entries = 0
        total_conversations = 0
        active_projects = 0

        click.echo("Project Statistics:")
        click.echo("-" * 50)

        for project in projects:
            # Use intermediate variable to help mypy understand this is a value
            project_id = project.id
            stats_data = db_manager.get_project_stats(session, project_id)  # type: ignore[arg-type]
            total_entries += stats_data["total_entries"]
            total_conversations += stats_data["conversations"]
            if project.is_active:
                active_projects += 1

            click.echo(f"{project.name}:")
            click.echo(f"  Entries: {stats_data['total_entries']}")
            click.echo(f"  Conversations: {stats_data['conversations']}")
            click.echo(f"  User messages: {stats_data['user_messages']}")
            click.echo(
                f"  Assistant messages: {stats_data['assistant_messages']}",
            )
            click.echo(f"  Tool calls: {stats_data['tool_calls']}")
            click.echo(f"  Last activity: {stats_data['last_activity']}")
            click.echo()

        click.echo("Summary:")
        click.echo(f"  Total projects: {len(projects)}")
        click.echo(f"  Active projects: {active_projects}")
        click.echo(f"  Total entries: {total_entries}")
        click.echo(f"  Total conversations: {total_conversations}")


@db.command()
@click.option(
    "--database-url",
    default="sqlite:///ccmonitor.db",
    help="Database URL",
)
@click.option(
    "--query",
    prompt="Search query",
    help="Text to search for",
)
@click.option(
    "--limit",
    default=10,
    help="Number of results to show",
)
def search(database_url: str, query: str, limit: int) -> None:
    """Search message content in the database."""
    db_manager = DatabaseManager(database_url)

    with db_manager.get_session() as session:
        entries = db_manager.search_entries(
            session,
            query=query,
            limit=limit,
        )

        if not entries:
            click.echo("No results found.")
            return

        click.echo(f"Found {len(entries)} results:")
        click.echo("-" * 50)

        for entry in entries:
            click.echo(f"Project: {entry.project.name}")
            click.echo(f"Type: {entry.entry_type.value}")
            click.echo(f"Timestamp: {entry.timestamp}")
            if entry.message_content:
                # Show first 200 chars of content
                # Use intermediate variable to help mypy understand this is a value
                message_content = entry.message_content
                content = message_content[:200]  # type: ignore[index]
                if len(message_content) > 200:
                    content += "..."
                click.echo(f"Content: {content}")
            click.echo()


if __name__ == "__main__":
    db()
